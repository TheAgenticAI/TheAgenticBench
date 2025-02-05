import os
import json
import traceback
from typing import List, Optional, Dict, Any, Union, Tuple
from datetime import datetime
from pydantic import BaseModel
from dataclasses import asdict
import logfire
from fastapi import WebSocket
from dotenv import load_dotenv
from pydantic_ai.messages import ModelMessage
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai import Agent
from utils.oai_client import get_client
from utils.stream_response_format import StreamResponse
from utils.prompts import (
    ORCHESTRATOR_PLAN_PROMPT,
    ORCHESTRATOR_GET_FINAL_ANSWER,
)
from agents.file_surfer import FileSurfer, FileToolDependencies, RequestsMarkdownBrowser
from agents.web_surfer import WebSurfer
from agents.coder_agent import (
    CoderAgent, CoderDependencies, Executor, ExecutorDependencies,
    DockerCodeExecutor, LocalCodeExecutor, CoderResult, coder_system_message
)
from agents.rag_agent import RAGAgent, RAGDependencies
from openai import AsyncOpenAI
from utils.initializers.rag_constants import rag_system_prompt

load_dotenv()

# Base Models
class PlanModel(BaseModel):
    """Model for the planning stage output"""
    plan: str
    metadata: Optional[Dict[str, Any]] = None

class AgentSelectorOutput(BaseModel):
    """Model for the agent selection output"""
    next_speaker: str
    instruction: str
    explanation: str

class CritiqueOutput(BaseModel):
    """Model for critique stage output"""
    feedback: str
    terminate: bool
    final_response: Optional[str] = None
    retry_count: Optional[int] = 0

class AgentExecutionResult(BaseModel):
    """Model for storing agent execution results"""
    success: bool
    output: str
    error_message: Optional[str] = None
    execution_time: float
    agent_name: str

# Custom Exceptions
class OrchestrationError(Exception):
    """Base exception for orchestration errors"""
    pass

class AgentInitializationError(OrchestrationError):
    """Raised when agent initialization fails"""
    pass

class AgentExecutionError(OrchestrationError):
    """Raised when agent execution fails"""
    pass

class WebSocketError(OrchestrationError):
    """Raised when WebSocket communication fails"""
    pass

# Context Management
class OrchestrationContext:
    """Maintains the context throughout the orchestration process"""
    def __init__(self):
        self.current_plan: Optional[str] = None
        self.execution_history: List[AgentExecutionResult] = []
        self.retry_counts: Dict[str, int] = {}
        self.max_retries: int = 3
        self.chat_history: List[ModelMessage] = []
        self.agent_selector_chat_history: List[ModelMessage] = []
        self.last_code_block: Optional[Dict[str, Any]] = None

# Main Orchestrator Class
class SystemOrchestrator:
    def __init__(self):
        self.agents: List[Union[FileSurfer, CoderAgent, Executor, WebSurfer, RAGAgent]] = []
        self.model: Optional[OpenAIModel] = None
        self.websocket: Optional[WebSocket] = None
        self.stream_output: Optional[StreamResponse] = None
        self.orchestrator_response: List[StreamResponse] = []
        self.context = OrchestrationContext()
        self.coder_deps = None
        self.executor_deps = None
        self._setup_logging()

    def _setup_logging(self) -> None:
        """Configure logging with proper formatting"""
        logfire.configure(
            send_to_logfire='if-token-present',
            token=os.getenv("LOGFIRE_TOKEN"),
            scrubbing=False,
        )

    async def _safe_websocket_send(self, message: Any) -> bool:
        """Safely send message through websocket with error handling"""
        try:
            if self.websocket and self.websocket.client_state.CONNECTED:
                await self.websocket.send_text(json.dumps(asdict(message)))
                return True
            return False
        except Exception as e:
            logfire.error(f"WebSocket send failed: {str(e)}")
            return False

    async def initialize_agents(self) -> List[Union[FileSurfer, CoderAgent, Executor, WebSurfer, RAGAgent]]:
        """Initialize all required agents with error handling"""
        try:
            logfire.info("Initializing agents")

            # Initialize OpenAI model
            self.model = OpenAIModel(
                model_name=os.environ.get("AGENTIC_BENCH_MODEL_NAME", "gpt-4o"),
                openai_client=get_client()
            )

            # Initialize File Surfer
            file_surfer = Agent(
                model=self.model,
                name="File Surfer Agent",
                deps_type=FileToolDependencies,
            )
            file_surfer_agent = FileSurfer(
                agent=file_surfer,
                browser=RequestsMarkdownBrowser(
                    viewport_size=1024 * 5,
                    downloads_folder="coding"
                )
            )

            # Initialize Coder Agent
            coder_description = "A helpful and general-purpose AI assistant that has strong language skills, Python skills, and Linux command line skills."
            
            self.coder_deps = CoderDependencies(
                description=coder_description,
                system_messages=coder_system_message,
                request_terminate=False
            )

            cod_agent = Agent(
                model=self.model,
                name="Coder Agent",
                deps_type=CoderDependencies,
                result_type=CoderResult
            )
            coder_agent = CoderAgent(
                agent=cod_agent,
                system_prompt=coder_system_message
            )

            # Initialize Executor
            executor_system_message = "A computer terminal that performs no other action than running Python scripts or sh shell scripts. Always call the execute_code tool to execute the code and output the result."
            
            executor_type = os.environ.get("AGENTIC_BENCH_EXECUTOR")
            print()
            print(f"Executor type from env : {executor_type}")
            if executor_type in os.environ.get("AGENTIC_BENCH_SUPPORTED_EXECUTORS", []):
                print(f"Executor type in supported executors from env:  {executor_type}")
                executor = DockerCodeExecutor() if executor_type == "Docker" else LocalCodeExecutor()
                
                self.executor_deps = ExecutorDependencies(
                    executor=executor,
                    confirm_execution="ACCEPT_ALL",
                    description="Executor to execute the generated code",
                    system_message=executor_system_message,
                    content=None,
                    check_last_n_message=5
                )

            exec_agent = Agent(
                model=self.model,
                name="Executor Agent",
                deps_type=ExecutorDependencies,
            )
            executor_agent = Executor(
                agent=exec_agent,
                system_prompt=executor_system_message
            )

            # Initialize Web Surfer
            web_surfer_agent = WebSurfer(api_url="http://localhost:8000/execute_task")

            rag_agent = Agent(
                model=self.model,
                name="RAG Agent",
                deps_type=RAGDependencies
            )

            # Initialize RAG agent instance without description parameter
            rag_agent_instance = RAGAgent(
                agent=rag_agent
            )

            # Combine all agents
            self.agents = [file_surfer_agent, coder_agent, executor_agent, web_surfer_agent, rag_agent_instance]

            logfire.info(f"Successfully initialized {len(self.agents)} agents")
            logfire.info(f"Agents: {[agent.name for agent in self.agents]}")

            return self.agents

        except Exception as e:
            error_msg = f"Failed to initialize agents: {str(e)}\n{traceback.format_exc()}"
            logfire.error(error_msg)
            raise AgentInitializationError(error_msg)

    async def generate_plan(self, task: str) -> Tuple[bool, str, Optional[str]]:
        """Generate initial plan with error handling"""
        try:
            agent_descriptions = "\n".join(f"Name: {agent.name}\nDescription: {agent.description}\n" for agent in self.agents)
            planner_prompt = f"""You only need to answer in a string format. Never perform any tool calls for any agents, Just make a plan (string format) based on the information you have.

            Based on the team composition, and known and unknown facts, please devise a short bullet-point plan for addressing the original request. Remember, there is no requirement to involve all team members -- a team member's particular expertise may not be needed for this task.

            <rules>
                <input_processing> 
                    - You are provided with a team description that contains information about the team members and their expertise.
                    - These team members receive the plan generated by you but cannot follow direct orders like tool calls from you, so you are strictly restricted to only making a plan.
                    - You do not have access to any tools, just a string input and a string reply.
                </input_processing> 

                <output_processing>
                    - You need to provide a plan in a string format.
                    - The agents in the team are not directly under you so you cannot give any tool calls since you have no access to any tools whatsoever. 
                    - You need to plan in such a way that a combination of team members can be used if needed to handle and solve the task at hand.
                </output_processing>

                <critical>
                    - You always need to generate a plan that satisfies the request strictly using the agents that we have.
                     - Never ever try to answer the question yourself no matter how simple it is actually.
                    - If there are any weblinks/ file paths then never omit them from the plan. Include them as provided by the user, without any modification.
                    - If there are any instructions in the original question, include them in the plan as is, dont try to deviate from the user provided instructions and try to craft something new in the plan.
                    - Dont try to add agents unnecessarily to the plan. Use only the agents that are absolutely necessary to solve the task.
                </critical>
            </rules>
            
            Available agents and their descriptions: 

            {agent_descriptions}
            """

            planner_agent = Agent(
                model=self.model,
                name="Planner Agent",
                system_prompt=planner_prompt
            )
            
            start_time = datetime.now()
            plan_result = await planner_agent.run(task)
            execution_time = (datetime.now() - start_time).total_seconds()

            logfire.info(f"Plan generation completed in {execution_time}s")
            logfire.info(f"Planner agent new messages : {plan_result.new_messages()}")
            
            return True, plan_result.data, None

        except Exception as e:
            error_msg = f"Plan generation failed: {str(e)}\n{traceback.format_exc()}"
            logfire.error(error_msg)
            return False, "", error_msg

    async def select_next_agent(self, plan: str) -> Tuple[bool, Optional[AgentSelectorOutput], Optional[str]]:
        """Select next agent with comprehensive error handling"""
        try:
            agent_descriptions = "\n".join(f"Name: {agent.name}\nDescription: {agent.description}\n" for agent in self.agents)
            selector_prompt = f"""
            
            You are a selector agent. Your job is to look at the conversation flow and the agents at hand and then correctly decided which agent should speak next. Also when you decide which agent should speak next, you need to provide the instruction that the agent should follow.

            Available agents and their descriptions :  

            {agent_descriptions}
            
            <rules>
                <input_processing>
                    - You have been provided with the current plan that we are supposed to execute and complete in order to satisfy the request.
                    - You need to look at the conversation and then decide which agent should speak next.
                </input_processing>

                <output_processing>
                    - You need to output a JSON with keys "next_speaker", "instruction", and "explanation".
                    - The "next_speaker" key should contain the name of the agent that you think should speak next.
                    - The "instruction" key should contain the instruction that the agent should follow.
                    - The "explanation" key should contain the reasoning behind your decision.

                </output_processing>

                <critical>
                    - You always need to generate a plan that satisfies the request strictly using the agents that we have.
                    - If there are any weblinks/ file paths then never omit them from the instructions. Include them as provided by the user, without any modification.
                    - If there are any instructions in the original question, include them in the instruction as is, dont try to deviate from the user provided instruction and try to craft something new.
                </critical>
            </rules>
            
            """

            selector_agent = Agent(
                model=self.model,
                name="Agent Selector",
                system_prompt=selector_prompt,
                result_type=AgentSelectorOutput
            )

            result = await selector_agent.run(user_prompt=plan, message_history=self.context.agent_selector_chat_history)
            logfire.info(f"Agent selection completed: {result.data}")
            logfire.info(f"Selector agent new messages : {result.new_messages()}")
            self.context.agent_selector_chat_history.extend(result.new_messages())
            return True, result.data, None

        except Exception as e:
            error_msg = f"Agent selection failed: {str(e)}\n{traceback.format_exc()}"
            logfire.error(error_msg)
            return False, None, error_msg

    async def execute_agent_instruction(self, agent: Union[FileSurfer, CoderAgent, Executor, WebSurfer, RAGAgent], instruction: str) -> AgentExecutionResult:
        """Execute agent instruction with robust error handling using generate_reply"""
        start_time = datetime.now()
        result = AgentExecutionResult(
            success=False,
            output="",
            error_message=None,
            execution_time=0.0,
            agent_name=agent.name
        )

        try:
            # Update stream output for WebSocket
            self.stream_output = StreamResponse(
                agent_name=agent.name,
                instructions=instruction,
                steps=[],
                output="",
                status_code=0
            )
            await self._safe_websocket_send(self.stream_output)

            # Prepare agent-specific kwargs based on agent type
            if isinstance(agent, CoderAgent):
                success, response, messages = await agent.generate_reply(
                    user_message=instruction,
                    deps=self.coder_deps,websocket=self.websocket,
                    stream_output=self.stream_output
                )

                # Parse the response to extract code block info
                if success:
                    # Extract dependencies and content from response string
                    response_parts = response.split(" dependencies=")
                    if len(response_parts) > 1:
                        dependencies_content = response_parts[1].split(" content=", 1)
                        if dependencies_content:
                            try:
                                # Parse dependencies list from string
                                dependencies = eval(dependencies_content[0])  # Convert string to actual list

                                content_split = dependencies_content[1]
                                if len(content_split) > 1:
                                    content = content_split.strip("'")
                                    
                                    # Store in context for Executor to use
                                    self.context.last_code_block = {
                                        "dependencies": dependencies,
                                        "content": content
                                    }
                                    print("response block to send to executor", self.context.last_code_block)
                            except Exception as e:
                                logfire.error(f"Failed to parse coder response: {e}")

                print()
                print(f"Response from Coder Agent : {response}")
                print()

            elif isinstance(agent, Executor):
                # Use the stored code block from context
                if self.context.last_code_block:
                    self.executor_deps.content = self.context.last_code_block
                success, response, messages = await agent.generate_reply(
                    user_message=instruction,
                    deps=self.executor_deps,websocket=self.websocket,
                    stream_output=self.stream_output
                )
            elif isinstance(agent, FileSurfer):
                success, response, messages = await agent.generate_reply(
                    user_message=instruction,
                    websocket=self.websocket,
                    stream_output=self.stream_output
                )
            elif isinstance(agent, WebSurfer):
                success, response, messages = await agent.generate_reply(
                    instruction=instruction,
                    websocket=self.websocket,
                    stream_output=self.stream_output
                )
            elif isinstance(agent, RAGAgent): # RAG Agent
                success, response, messages = await agent.generate_reply(
                    user_message=instruction,
                    websocket=self.websocket,
                    stream_output=self.stream_output
                )

            else:  # FileSurfer
                success, response, messages = await agent.generate_reply(
                    user_message=instruction
                )

            # Update result
            execution_time = (datetime.now() - start_time).total_seconds()
            result.success = success
            result.output = response
            result.execution_time = execution_time
            
            # Update chat history
            if success:
                self.context.chat_history.extend(messages)
            
            # Update stream output
            if self.stream_output:
                self.stream_output.output = response
                self.stream_output.status_code = 200 if success else 500
                self.orchestrator_response.append(self.stream_output)
                await self._safe_websocket_send(self.stream_output)

        except Exception as e:
            error_msg = f"Agent execution failed: {str(e)}\n{traceback.format_exc()}"
            logfire.error(error_msg)
            result.error_message = error_msg
            
            if self.stream_output:
                self.stream_output.status_code = 500
                self.stream_output.output = error_msg
                await self._safe_websocket_send(self.stream_output)

        return result

    async def critique_execution(self, task: str, output: str, plan: str, execution_history: List[AgentExecutionResult]) -> Tuple[bool, Optional[CritiqueOutput], Optional[str]]:
        """Critique agent execution and determine next steps"""
        try:
            critique_prompt = """You are a critique agent. Your job is to critique the output of the agent that just executed, take into consideration the previous outputs of other agents also and then decide if the task is complete or if we need to continue with the next agent.

            <rules>

                <input_processing>
                    - You have been provided with the task description, the current plan to be followed, the output of the latest agent that executed and the output execution history of the previous agents that have finished execution.
                    - You have to look at the plan and decide firstly what is our progress currently relative to the plan.
                    - You have to decide if the task is complete or if we need to continue with the next agent.
                    - You have to provide feedback on the output of the agent that just executed.
                </input_processing>

                <output_processing>
                    - You need to output a JSON with keys "feedback", "terminate", and optionally "final_response".

                    <feedback> 
                        - You need to provide feedback on the output of the agent that just executed.
                        - The feedback should be verbose and should contain all the necessary details.
                        - The main goal with this feedback is that we should be able to understand what went wrong and what went right with the output.
                        - Highlight things that were done correctly and things that were done incorrectly.
                        - You also need to provide feedback on the progress of the task relative to the plan inside the feedback key itself in the output JSON. When giving progress feedback, you need to compare the current state with the plan and then provide feedback. Maybe compare the number of steps completed with the total number of steps in the plan. Take into consideration the execution history of previous agents while comparing with the plan.
                    </feedback>

                    <terminate>
                        - The "terminate" key should be a boolean value.
                        - If the task is complete and we do not need to continue with any other agents, then the value should be True.
                        - If the task is not complete and we need to continue with the next agent, then the value should be False.
                        - If terminate is True then you have to provide the final_response key in the output. This is a super critical key and should contain the final response to the original request.
                        - If terminate is False then you do not need to provide the final_response key.
                        - The final response key is the actual answer and so you need to output the content in the same manner inside the final_response key as you would output the final answer.
                    </terminate>

                </output_processing>

            </rules>
            
            Output JSON with 'feedback', 'terminate', and optional 'final_response' keys."""

            previous_execution_results = "\n".join(
                f"Agent: {result.agent_name}\nOutput: {result.output if result.success else result.error_message}\n"
                for result in execution_history[:-1]  # Exclude the last element
            )

            critique_agent = Agent(
                model=self.model,
                name="Critique Agent",
                system_prompt=critique_prompt,
                result_type=CritiqueOutput
            )
            
            context = f"Task: {task}\nPlan: {plan}\nLatest Output:{output}\nPrevious Execution Results: {previous_execution_results}"
            result = await critique_agent.run(user_prompt=context)
            logfire.info(f"Critique completed: {result.data}")
            logfire.info(f"Critique agent new messages : {result.new_messages()}")
            
            return True, result.data, None

        except Exception as e:
            error_msg = f"Critique failed: {str(e)}\n{traceback.format_exc()}"
            logfire.error(error_msg)
            return False, None, error_msg

    async def prepare_final_answer(self, task: str) -> str:
        """Prepare final answer when task is complete"""
        try:
            final_message = ORCHESTRATOR_GET_FINAL_ANSWER.format(task=task)
            
            final_agent = Agent(
                model=self.model,
                name="Final Answer Agent",
                system_prompt=""
            )
            
            result = await final_agent.run(final_message, message_history=self.context.chat_history)
            return result.data

        except Exception as e:
            error_msg = f"Failed to prepare final answer: {str(e)}"
            logfire.error(error_msg)
            return f"Task completed but failed to generate final answer: {error_msg}"

    async def run(self, task: str, websocket: WebSocket) -> List[Dict[str, Any]]:
        """Main orchestration loop with comprehensive error handling"""
        self.websocket = websocket
        stream_output = StreamResponse(
            agent_name="Orchestrator",
            instructions=task,
            steps=[],
            output="",
            status_code=0
        )
        
        try:
            # Initialize system
            await self._safe_websocket_send(stream_output)
            self.agents = await self.initialize_agents()
            stream_output.steps.append("Agents initialized successfully")
            await self._safe_websocket_send(stream_output)

            # Generate initial plan
            logfire.info("Generating the Plan")
            success, plan, error = await self.generate_plan(task)
            logfire.info(f"Generated Plan: {plan}")
            if not success:
                stream_output.steps.append(f"Plan generation failed: {error}")
                stream_output.status_code = 500
                return [asdict(stream_output)]

            self.context.current_plan = plan

            while True:
                # Select next agent
                success, selector_output, error = await self.select_next_agent(plan)
                if not success:
                    stream_output.steps.append(f"Agent selection failed: {error}")
                    continue

                # Find appropriate agent instance
                selected_agent = next(
                    (agent for agent in self.agents if agent.name == selector_output.next_speaker),
                    None
                )
                
                if not selected_agent:
                    stream_output.steps.append(f"Agent {selector_output.next_speaker} not found")
                    continue

                # Execute instruction
                result = await self.execute_agent_instruction(
                    selected_agent, 
                    selector_output.instruction
                )
                self.context.execution_history.append(result)

                if not result.success:
                    # Handle retry logic
                    retry_count = self.context.retry_counts.get(selected_agent.name, 0)
                    if retry_count < self.context.max_retries:
                        self.context.retry_counts[selected_agent.name] = retry_count + 1
                        stream_output.steps.append(
                            f"Retrying {selected_agent.name} execution ({retry_count + 1}/{self.context.max_retries})"
                        )
                        continue
                    else:
                        stream_output.steps.append(f"Max retries reached for {selected_agent.name}")
                        # Continue with next agent instead of failing completely
                        continue

                # Critique execution
                critique_success, critique_result, critique_error = await self.critique_execution(
                    task, result.output, plan, self.context.execution_history
                )

                if not critique_success:
                    stream_output.steps.append(f"Critique failed: {critique_error}")
                    continue

                if critique_result.terminate:
                    final_answer = critique_result.final_response or await self.prepare_final_answer(task)
                    stream_output.output = final_answer
                    stream_output.status_code = 200
                    self.orchestrator_response.append(stream_output)
                    await self._safe_websocket_send(stream_output)
                    break

                plan = result.output
                
                # Update stream output with progress
                stream_output.steps.append(f"Completed step with {selected_agent.name}")
                await self._safe_websocket_send(stream_output)

            logfire.info("Task completed successfully")
            return [asdict(i) for i in self.orchestrator_response]

        except Exception as e:
            error_msg = f"Critical orchestration error: {str(e)}\n{traceback.format_exc()}"
            logfire.error(error_msg)
            
            if stream_output:
                stream_output.output = error_msg
                stream_output.status_code = 500
                self.orchestrator_response.append(stream_output)
                await self._safe_websocket_send(stream_output)
            
            # Even in case of critical error, return what we have
            return [asdict(i) for i in self.orchestrator_response]

        finally:
            logfire.info("Orchestration process complete")
            # Clear any sensitive data
            self.context = OrchestrationContext()  
            
    def _get_agent_by_name(self, name: str) -> Optional[Union[FileSurfer, CoderAgent, Executor, WebSurfer, RAGAgent]]:
        """Helper method to find agent by name"""
        return next((agent for agent in self.agents if agent.name == name), None)

    async def shutdown(self):
        """Clean shutdown of orchestrator"""
        try:
            # Close websocket if open
            if self.websocket:
                await self.websocket.close()
            
            # Clear all responses
            self.orchestrator_response = []
            
            # Reset context
            self.context = OrchestrationContext()
            
            logfire.info("Orchestrator shutdown complete")
            
        except Exception as e:
            logfire.error(f"Error during shutdown: {str(e)}")
            raise