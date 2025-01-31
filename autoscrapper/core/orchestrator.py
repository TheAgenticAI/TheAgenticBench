import os
import asyncio
import tiktoken
import logfire

from core.agents.browser_agent import BA_agent, BA_SYS_PROMPT
from core.agents.planner_agent import PA_agent, PA_SYS_PROMPT
from core.agents.critique_agent import CA_agent, CA_SYS_PROMPT
from core.browser_manager import PlaywrightManager 

from core.utils.dom_analysis import ImageAnalyzer
from core.utils.openai_client import get_client
from core.utils.logger import logger
from core.utils.message_type import MessageType
from core.utils.openai_msg_parser import AgentConversationHandler, ConversationStorage
from core.utils.custom_exceptions import CustomException, PlannerError, BrowserNavigationError, SSAnalysisError, CritiqueError


tokenizer = tiktoken.get_encoding("o200k_base")


def ensure_tool_response_sequence(messages):
    """Ensures that every tool call has a corresponding tool response"""
    tool_calls = {}
    result = []
    
    for msg in messages:
        if isinstance(msg, dict) and 'tool_calls' in msg.get('parts', [{}])[0]:
            # Store tool calls
            for tool_call in msg['parts'][0]['tool_calls']:
                tool_calls[tool_call['tool_call_id']] = False
            result.append(msg)
        elif isinstance(msg, dict) and 'tool_return' in msg.get('parts', [{}])[0]:
            # Mark tool call as responded
            tool_call_id = msg['parts'][0].get('tool_call_id')
            if tool_call_id in tool_calls:
                tool_calls[tool_call_id] = True
            result.append(msg)
        else:
            result.append(msg)
    
    # Check if all tool calls have responses
    missing_responses = [id for id, has_response in tool_calls.items() if not has_response]
    if missing_responses:
        raise ValueError(f"Missing tool responses for: {missing_responses}")
        
    return result

def prompt_constructor(sys_prompt, inputs):
    """Constructs a prompt string with system prompt and inputs"""
    return f"{sys_prompt}\n\nInputs :\n{inputs}"

def log_token_usage(total_tokens, request_tokens, response_tokens):
    """Prints token usage information"""
    logfire.debug(
        f"""
        \nToken Usage:
        \nTotal tokens: {total_tokens}
        \nRequest tokens: {request_tokens}
        \nResponse tokens: {response_tokens}\n
        """
    )
    return

class Orchestrator:
    logfire.configure(send_to_logfire='if-token-present', scrubbing=False)

    def __init__(self, input_mode: str = "GUI_ONLY") -> None:
        self.client = get_client()
        self.browser_manager = None
        self.shutdown_event = asyncio.Event()
        self.input_mode = input_mode
        self.conversation_handler = AgentConversationHandler()
        self.conversation_storage = ConversationStorage()
        self.terminate = False
        self.response_handler = None

    async def async_init(self):
        self.browser_manager = await self.initialize_browser_manager()

    def set_response_handler(self, handler):
        self.response_handler = handler

    async def reset_state(self):
        """Reset internal state for new command while preserving browser"""
        self.terminate = False
        self.conversation_handler = AgentConversationHandler()
        self.conversation_storage = ConversationStorage()
    
    async def initialize_browser_manager(self):
        logfire.info("Initializing browser manager")
        browser_manager = PlaywrightManager(gui_input_mode="GUI_ONLY")
        if self.input_mode == "API":
            browser_manager = PlaywrightManager(gui_input_mode=False, take_screenshots=True, headless=True)
        self.browser_manager = browser_manager
        await self.browser_manager.async_initialize()
        logger.info(f"Browser manager initialized : {browser_manager}")
        return browser_manager
    
    async def notify_client(self, message: str, message_type: MessageType):
        """Send a message to the client-specific notification queue."""
        if self.input_mode == "GUI_ONLY":
            # Skip in GUI mode
            return
        if hasattr(self, "notification_queue") and self.notification_queue:
            self.notification_queue.put({"message": message, "type": message_type.value})
        else:
            logger.warning("No notification queue attached. Skipping client notification.")

    async def run(self, command):
        try:
            logfire.info(f" Running Loop with User Query: {command}")
            await self.notify_client(f"Executing command: {command}", MessageType.INFO)

            message_history = []
            PA_prompt = (
                f"User Query : {command}"
                "Feedback : None"
            )
            
            i = 0
            iteration_counter = 0
            while not self.terminate:
                try:
                    iteration_counter += 1
                    logfire.debug(f"________Iteration {iteration_counter}________") 
                    logfire.info("Running planner agent")
                    logfire.debug(f"\nMessage history : {message_history}\n")

                    # Planner Execution
                    try:
                        validated_history = ensure_tool_response_sequence(message_history)
                        planner_response = await PA_agent.run(
                            user_prompt=prompt_constructor(PA_SYS_PROMPT, PA_prompt),
                            message_history=validated_history
                        )
                        self.conversation_handler.add_planner_message(planner_response)
                        
                        plan = planner_response.data.plan
                        c_step = planner_response.data.next_step
                        logfire.info(f"Initial plan : {plan}")
                        logfire.info(f"Current step : {c_step}")
                        await self.notify_client(f"Plan Generated: {plan}", MessageType.INFO)
                        await self.notify_client(f"Current Step: {c_step}", MessageType.INFO)

                        try:
                            if iteration_counter == 1:  # Only show plan on first iteration
                                await self.browser_manager.notify_user(
                                    f" {planner_response.data.plan}",
                                    message_type=MessageType.PLAN
                                )
                            await self.browser_manager.notify_user(
                                f"{planner_response.data.next_step}",
                                message_type=MessageType.STEP
                            )
                        except Exception as e:
                            logfire.error(f"Error in notifying plan to the user : {e}")
                            self.notify_client(f"Error in planner: {str(e)}", MessageType.ERROR)
                        
                    except Exception as e:
                        raise PlannerError(
                            f"Planner execution failed: {str(e)}",
                            original_error=e
                        )

                    log_token_usage(
                        planner_response._usage.total_tokens, 
                        planner_response._usage.request_tokens, 
                        planner_response._usage.response_tokens
                    )

                    message_history = [*message_history, *planner_response.new_messages()]


                    # Pre-Action Screenshot
                    try:
                        logfire.info("Taking Pre_Action_SS")
                        pre_action_ss = await self.browser_manager.take_screenshots(
                            "Pre_Action_SS", page=None, full_page=False
                        )
                        logfire.info(f"SS Saved to Path: {pre_action_ss}")
                    except Exception as e:
                        error_msg = f"Failed to take Pre_Action_SS: {str(e)}"
                        logfire.error(error_msg, exc_info=True)
                        await self.browser_manager.notify_user(
                            error_msg,
                            message_type=MessageType.ERROR
                        )
                        raise CustomException(error_msg, original_error=e)


                    # Browser Execution
                    BA_prompt = (
                        f'plan="{plan}" '
                        f'current_step="{c_step}" '
                    )

                    try:
                        logfire.info("Running browser agent")
                        browser_response = await BA_agent.run(
                            user_prompt=prompt_constructor(BA_SYS_PROMPT, BA_prompt),
                            message_history=message_history, 
                        )
                        self.conversation_handler.add_browser_nav_message(browser_response)
                        logfire.debug("Extending message history with browser response")
                        message_history = [*message_history, *browser_response.new_messages()]

                        logfire.info(f"Browser Agent Response: {browser_response.data}")
                        await self.notify_client(f"Current Step Execution: {browser_response.data}", MessageType.INFO)

                        log_token_usage(
                            browser_response._usage.total_tokens,   
                            browser_response._usage.request_tokens,
                            browser_response._usage.response_tokens
                        )


                    except Exception as e:
                        error_msg = f"Browser navigation failed: {str(e)}"
                        await self.notify_client(f"Error in browser navigation: {str(e)}", MessageType.ERROR)
                        logfire.error(error_msg, exc_info=True)
                        await self.browser_manager.notify_user(
                            error_msg,
                            message_type=MessageType.ERROR
                        )
                        raise BrowserNavigationError(error_msg, original_error=e)


                    # Post_Action_SS Screenshot
                    try:
                        logfire.info("Taking Post_Action_SS")
                        post_action_ss = await self.browser_manager.take_screenshots(
                            "Post_Action_SS", page=None, full_page=False
                        )
                        logfire.info(f"Post_Action_SS Saved to Path: {post_action_ss}")
                    except Exception as e:
                        error_msg = f"Failed to take Post_Action_SS: {str(e)}"
                        logfire.error(error_msg, exc_info=True)
                        await self.browser_manager.notify_user(
                            error_msg,
                            message_type=MessageType.ERROR
                        )
                        raise CustomException(error_msg, original_error=e)

                    # SS Analysis
                    try:
                        logfire.info("Running SS analysis")
                        
                        
                        ss_analysis_response = ImageAnalyzer(
                            pre_action_ss, 
                            post_action_ss, 
                            c_step
                        ).analyze_images()
                        self.conversation_handler.add_dom_analysis_message(ss_analysis_response)
                        
                        logfire.info(f"SS Analysis Response: {ss_analysis_response}")
                    except Exception as e:
                        error_msg = f"SS Analysis failed: {str(e)}"
                        logfire.error(error_msg, exc_info=True)
                        await self.browser_manager.notify_user(
                            error_msg,
                            message_type=MessageType.ERROR
                        )
                        await self.notify_client(f"Error in SS Analysis: {str(e)}", MessageType.ERROR)
                        raise SSAnalysisError(error_msg, original_error=e)


                    # Critique Agent
                    try:
                        logfire.info("Running critique agent")
                        CA_prompt = (
                            f'plan="{plan}" '
                            f'next_step="{c_step}" '
                            f'tool_response="{browser_response.data}" '
                            f'dom_analysis="{ss_analysis_response}"'
                        )

                        critique_response = await CA_agent.run(
                            user_prompt=prompt_constructor(CA_SYS_PROMPT, CA_prompt),
                            message_history=message_history
                        )
                        self.conversation_handler.add_critique_message(critique_response)
                        logfire.debug("Extending message history with critique response")

                        message_history = [*message_history, *critique_response.new_messages()]
                        
                        logfire.info(f"Critique Feedback: {critique_response.data.feedback}")
                        logfire.info(f"Critique Response: {critique_response.data.final_response}")
                        await self.notify_client(f"Task did not complete, Retrying with Feedback : {critique_response.data.feedback}", MessageType.INFO)

                        log_token_usage(
                            critique_response._usage.total_tokens,   
                            critique_response._usage.request_tokens,
                            critique_response._usage.response_tokens
                        )

                    except Exception as e:
                        error_msg = f"Critique agent failed: {str(e)}"
                        await self.notify_client(f"Error in low-level critique: {str(e)}", MessageType.ERROR)
                        logfire.error(error_msg, exc_info=True)
                        await self.browser_manager.notify_user(
                            error_msg,
                            message_type=MessageType.ERROR
                        )
                        raise CritiqueError(error_msg, original_error=e)


                    openai_messages = self.conversation_handler.get_conversation_history()
                    saved_path = self.conversation_storage.save_conversation(openai_messages, prefix="task")
                    logfire.info(f"Conversation appended to: {saved_path}")

                    # Termination Check
                    if critique_response.data.terminate:
                        await self.browser_manager.notify_user(
                            f"{critique_response.data.final_response}",
                            message_type=MessageType.ANSWER,
                        )
                        final_response = critique_response.data.final_response
                        await self.notify_client(f"Final Response : {final_response}", MessageType.FINAL)

                        if self.response_handler:
                            await self.response_handler(final_response)
                        self.terminate = True
                        return final_response
                    else:
                        PA_prompt = (
                            f"User Query : {command}"
                            f"Previous Plan : {plan}"
                            f"Feedback : {critique_response.data.feedback}"
                        )
                    
                    # Loop Exit

                except Exception as step_error:
                    error_msg = f"Error in execution step {i}: {str(step_error)}"
                    await self.notify_client(f"Error in execution step {i} : {str(step_error)}", MessageType.ERROR)
                    logfire.error(error_msg, exc_info=True)
                    await self.browser_manager.notify_user(
                        error_msg,
                        message_type=MessageType.ERROR
                    )
                    # Optionally retry or continue to next iteration
                    continue

        except Exception as e:
            error_msg = f"Critical Error in orchestrator: {str(e)}"
            await self.notify_client(f"Error in Orchestrator : {str(e)}", MessageType.ERROR)

            logfire.error(error_msg, exc_info=True)
            await self.browser_manager.notify_user(
                error_msg,
                message_type=MessageType.ERROR
            )
            raise

        finally:
            logfire.info("Orchestrator Execution Completed")
            await self.cleanup()

    async def start(self):
    
        logfire.info("Starting the orchestrator")

        await self.initialize_browser_manager() 

        if self.input_mode == "GUI_ONLY":
            browser_context = await self.browser_manager.get_browser_context()
            await browser_context.expose_function('process_task', self.receive_command) # type: ignore


        await self.wait_for_exit()

    async def receive_command(self, command: str):
        """Process commands with state reset"""
        logger.info(f"Received command from the UI: {command}")
        await self.reset_state()  # Reset state before new command
        await self.run(command)


    async def wait_for_exit(self):
        await self.shutdown_event.wait()

    async def shutdown(self):
        if self.browser_manager:
            await self.browser_manager.stop_playwright()

    async def cleanup(self):
        """Modified cleanup to handle both modes properly"""
        if self.input_mode != "GUI_ONLY":
            # Full cleanup for API mode
            if self.browser_manager:
                await self.browser_manager.stop_playwright()
            self.shutdown_event.set()
        else:
            # Partial cleanup for GUI mode - reset state but keep browser
            await self.reset_state()
            logger.info("Partial cleanup completed - browser preserved for GUI mode")

