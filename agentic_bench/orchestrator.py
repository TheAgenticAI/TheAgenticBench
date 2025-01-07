import logfire
import os
import re
import json
import datetime
from typing import List, Optional, Dict, Any, Union
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.messages import ModelResponse, ToolCallPart, ArgsJson
from agentic_bench.utils.oai_client import get_client
from pydantic_ai import Agent
from agentic_bench.utils.prompts import (
    ORCHESTRATOR_CLOSED_BOOK_PROMPT,
    ORCHESTRATOR_PLAN_PROMPT,
    ORCHESTRATOR_LEDGER_PROMPT,
    ORCHESTRATOR_GET_FINAL_ANSWER,
)
from agentic_bench.utils.models import FactModel, PlanModel
from agentic_bench.utils.get_openai_format_json_messages_from_pydantic_message_response import (
    get_openai_format_json_messages_from_pydantic_message_response,
    convert_json_to_string_messages,
)
from agentic_bench.agents.file_surfer import (
    FileToolDependencies,
    FileSurfer,
    RequestsMarkdownBrowser,
)
from agentic_bench.agents.web_surfer import WebSurfer
from agentic_bench.agents.coder_agent import (
    CoderAgent,
    CoderDependencies,
    CoderResult,
    Executor,
    ExecutorDependencies,
    ExecutorResult,
    DockerCodeExecutor,
    LocalCodeExecutor,
)
from agentic_bench.utils.stream_response_format import StreamResponse
from agentic_bench.ledger import LedgerManager, LedgerModel
from dotenv import load_dotenv
from fastapi import WebSocket
from dataclasses import asdict

load_dotenv()

logfire.configure(
    send_to_logfire="if-token-present",
    token=os.getenv("LOGFIRE_TOKEN"),
    scrubbing=False,
)

def _convert_messages_to_openai_format(messages: List[dict]) -> List[dict]:
    """Convert custom message format to OpenAI format"""
    openai_messages = []

    for message in messages:
        for part in message.get("parts", []):
            if part.get("part_kind") == "user-prompt":
                openai_messages.append({"role": "user", "content": part["content"]})
            elif part.get("part_kind") == "tool-call":
                args_json = json.loads(part["args"]["args_json"])
                openai_messages.append(
                    {"role": "assistant", "content": args_json.get("content", "")}
                )
            elif part.get("part_kind") == "system-prompt":
                openai_messages.append({"role": "system", "content": part["content"]})

    return openai_messages

# Custom exceptions
class OrchestratorError(Exception):
    """Base exception for orchestrator errors"""

    pass

class AgentInitializationError(OrchestratorError):
    """Raised when agent initialization fails"""

    pass

class TaskInitializationError(OrchestratorError):
    """Raised when task initialization fails"""

    pass

class MessageHistory:
    def __init__(self, messages):
        self.messages = messages if isinstance(messages, list) else [messages]

    def all_messages(self):
        return self.messages

# Type definition for supported agent types
AgentType = Union[FileSurfer, CoderAgent, Executor, WebSurfer]

class SystemOrchestrator:
    def __init__(self):
        self.agents: List[AgentType] = []
        self.team_description: str = ""
        self.client = get_client()
        self.facts = None
        self.chat_history = []
        self.ledger_manager = LedgerManager()
        self.model: Optional[OpenAIModel] = None
        self.coder_deps = None
        self.executor_deps = None
        logfire.info("Orchestrator initialized")
        self.websocket: Optional[WebSocket] = None
        self.stream_output: Optional[StreamResponse] = None
        self.orchestrator_response: List[StreamResponse] = []

    async def initialize_agents(self) -> List[AgentType]:
        """Initialize all required agents"""
        try:
            logfire.info("Initializing agents")

            self.model = OpenAIModel(
                os.environ.get("AGENTIC_BENCH_MODEL_NAME", "gpt-4o"), openai_client=self.client
            )

            # Initialize File Surfer agent
            file_surfer = Agent(
                model=self.model,
                name="File Surfer Agent",
                deps_type=FileToolDependencies,
            )
            file_surfer_agent = FileSurfer(
                agent=file_surfer,
                browser=RequestsMarkdownBrowser(
                    viewport_size=1024 * 5, downloads_folder="coding"
                ),
            )

            # Initialize Coder agent
            coder_description = "A helpful and general-purpose AI assistant that has strong language skills, Python skills, and Linux command line skills."
            coder_system_message = """You are a helpful AI assistant. Solve tasks using your coding and language skills.

In the following cases, suggest python code (in a python coding block) or shell script (in a sh coding block) for the user to execute:

1. When you need to collect info, use the code to output the info you need
2. When you need to perform some task with code, use the code to perform the task and output the result

Follow these rules:
- Always wrap code in ```python or ```sh markers
- Put # filename: <filename> as first line in code blocks if file needs to be saved
- Only one code block per response
- Use print function for output when relevant
- Provide complete, executable code only
- Do not use code blocks for non-executable explanations
- Reply "TERMINATE" when done

Example format:
```python
# filename: example.py
code here...
```
"""

            coder_deps = CoderDependencies(
                description=coder_description,
                system_messages=coder_system_message,
                request_terminate=False,
            )
            self.coder_deps = coder_deps

            cod_agent = Agent(
                model=self.model,
                name="Coder Agent",
                deps_type=CoderDependencies,
                result_type=CoderResult,
            )
            coder_agent = CoderAgent(
                agent=cod_agent, system_prompt=coder_system_message
            )

            # Initialize Executor agent
            executor_system_message = "A computer terminal that performs no other action than running Python scripts or sh shell scripts"

            # We create initial executor dependencies without the coder_result
            # This will be updated during runtime when we have actual results
            executor_type = os.environ.get("AGENTIC_BENCH_EXECUTOR")
            if executor_type and executor_type in os.environ.get(
                "AGENTIC_BENCH_SUPPORTED_EXECUTORS", []
            ):
                if executor_type == "Docker":
                    executor = DockerCodeExecutor()
                else:
                    executor = LocalCodeExecutor()

                executor_deps = ExecutorDependencies(
                    executor=executor,
                    confirm_execution="ACCEPT_ALL",
                    description="Executor to execute the generated code",
                    system_message=executor_system_message,
                    content=None,  # This will be populated during runtime
                    check_last_n_message=5,
                )
                self.executor_deps = executor_deps

            exec_agent = Agent(
                model=self.model,
                name="Executor Agent",
                deps_type=ExecutorDependencies,
                result_type=ExecutorResult,
                system_prompt="You are a computer terminal that performs no other action than running Python scripts or sh shell scripts.",
            )

            executor_agent = Executor(
                agent=exec_agent, system_prompt=executor_system_message
            )

            web_surfer_agent = WebSurfer(api_url="http://localhost:8000/execute_task")

            self.agents = [
                file_surfer_agent,
                coder_agent,
                executor_agent,
                web_surfer_agent,
            ]
            logfire.info(f"Successfully initialized {len(self.agents)} agents")
            logfire.info(f"Agents: {[agent.name for agent in self.agents]}")

            return self.agents

        except Exception as e:
            error_msg = f"Failed to initialize agents: {str(e)}"
            logfire.error(error_msg, exc_info=True)
            raise AgentInitializationError(error_msg)

    async def initialize_task(self, task: str) -> str:
        """Initialize task and create initial plan"""
        try:
            logfire.info(f"Initializing task: {task}")

            # Initialize team description
            self.team_description = (
                "Coder Agent for writing code, Executor agent for executing the written code, "
                "File surfer agent for reading local files, Web surfer agent for searching and "
                "extracting information from web pages."
            )

            # Initialize ledger
            self.ledger_manager.initialize_ledger()

            # Gather facts
            fact_subagent_prompt = ORCHESTRATOR_CLOSED_BOOK_PROMPT.format(task=task)
            fact_subagent = Agent(
                model=self.model,
                name="Fact Sub-Agent",
                system_prompt=fact_subagent_prompt,
                result_type=FactModel,
            )

            fact_result = await fact_subagent.run(task)
            # Extract just the string content from facts
            facts_text = (
                fact_result.data.facts
                if isinstance(fact_result.data, FactModel)
                else str(fact_result.data)
            )
            self.facts = facts_text
            logfire.info(f"Facts gathered successfully: {self.facts}")

            # Create plan
            planner_subagent_prompt = ORCHESTRATOR_PLAN_PROMPT.format(
                team=self.team_description
            )
            planner_subagent = Agent(
                model=self.model,
                name="Planner Sub-Agent",
                system_prompt=planner_subagent_prompt,
                result_type=PlanModel,
            )

            plan_result = await planner_subagent.run(self.facts)
            # Extract just the string content from plan
            plan_text = (
                plan_result.data.plan
                if isinstance(plan_result.data, PlanModel)
                else str(plan_result.data)
            )
            self.plan = plan_text
            logfire.info(f"Plan generated successfully: {self.plan}")
            print(f"Generated Plan: {self.plan}")

            # Clean start for chat history
            self.chat_history = []

            return self.plan

        except Exception as e:
            error_msg = f"Failed to initialize task: {str(e)}"
            logfire.error(error_msg, exc_info=True)
            raise TaskInitializationError(error_msg)

    async def update_ledger_state(self) -> None:
        """Update ledger state using LLM"""
        try:
            print("Updating ledger state......")
            if not self.model:
                raise OrchestratorError("Model not initialized")

            # Include chat history in the prompt
            # oai_json_formatted_messages = get_openai_format_json_messages_from_pydantic_message_response(self.chat_history)
            # string_chat_context = convert_json_to_string_messages(oai_json_formatted_messages)
            # openai_formatted_messages = _convert_messages_to_openai_format(self.chat_history)

            prompt = ORCHESTRATOR_LEDGER_PROMPT.format(
                task=self.facts if self.facts else "",
                team=self.team_description,
                names=[agent.name for agent in self.agents],
            )

            # print("Ledger Update Prompt: ", prompt)
            print(f"Message History : {self.chat_history}")

            ledger_agent = Agent(
                model=self.model,
                name="Ledger Agent",
                system_prompt="",
                result_type=LedgerModel,
            )

            # Pass the chat history to maintain context
            result = await ledger_agent.run(
                prompt, message_history=self.chat_history or None
            )

            logfire.debug(
                f"Ledger updated successfully {json.dumps(result.data.model_dump(), indent=4)}"
            )
            print(
                f"Ledger updated successfully {json.dumps(result.data.model_dump(), indent=4)}"
            )
            self.ledger_manager.update_ledger(result.data.model_dump())

        except Exception as e:
            logfire.error(f"Failed to update ledger: {str(e)}", exc_info=True)
            raise

    async def select_next_agent(self) -> Optional[AgentType]:
        """Select next agent based on ledger state"""
        try:
            print("Selecting next speaker......")
            next_speaker = self.ledger_manager.get_next_speaker()
            if not next_speaker:
                logfire.info("No next speaker specified in ledger")
                return None

            # Log available agents for debugging
            available_agents = [agent.name for agent in self.agents]
            logfire.debug(f"Available agents: {available_agents}")

            # Find matching agent
            for agent in self.agents:
                if agent.name == next_speaker:
                    logfire.info(f"Selected agent: {agent.name}")
                    print()
                    print(f"Next Speaker: {agent.name}")
                    print()
                    return agent

            logfire.warn(
                f"No agent found for speaker: {next_speaker}. Available agents: {available_agents}"
            )
            return None

        except Exception as e:
            logfire.error(f"Error selecting next agent: {str(e)}", exc_info=True)
            return None

    async def execute_agent_instruction(self, agent):
        try:
            instruction = self.ledger_manager.get_instruction()
            if not instruction:
                raise OrchestratorError("No instruction available")

            log = f"Executing instruction {instruction} with {agent.__class__.__name__}"
            logfire.info(log)
            if self.stream_output and self.stream_output.agent_name == agent.name:
                self.stream_output.steps.append(
                    f"Executing the instruction with {agent.__class__.__name__}"
                )
                if self.websocket:
                    await self.websocket.send_text(
                        json.dumps(asdict(self.stream_output))
                    )

            if isinstance(agent, WebSurfer):
                assert self.websocket is not None
                assert self.stream_output is not None
                success, response, messages = await agent.generate_reply(
                    instruction, self.websocket, self.stream_output
                )
                if success:
                    self.chat_history = [*self.chat_history, *messages]
                    log = "WebSurfer response received and messages stored"
                    logfire.info(log)
                    if (
                        self.stream_output
                        and self.stream_output.agent_name == agent.name
                    ):
                        self.stream_output.steps.append(log)
                        if self.websocket:
                            await self.websocket.send_text(
                                json.dumps(asdict(self.stream_output))
                            )

                    print(f"WebSurfer response: {response}")
                    if (
                        self.stream_output
                        and self.stream_output.agent_name == agent.name
                    ):
                        self.stream_output.output = response
                        self.stream_output.status_code = 200
                        self.orchestrator_response.append(self.stream_output)
                        if self.websocket:
                            await self.websocket.send_text(
                                json.dumps(asdict(self.stream_output))
                            )
                    return
                else:
                    logfire.error(
                        f"Failed to execute WebSurfer instruction: {response}"
                    )
                    raise OrchestratorError(f"WebSurfer execution failed: {response}")

            elif isinstance(agent, CoderAgent) and self.coder_deps:
                success, response, messages = await agent.generate_reply(
                    instruction, deps=self.coder_deps
                )

                if success:
                    # Append coder messages to chat history
                    self.chat_history = [*self.chat_history, *messages]
                    logfire.info(f"Coder agent messages : {messages}")
                    try:
                        # Parse the coder's response to get content and dependencies
                        # Response format is like: "terminated=True dependencies=['fastapi'] content='# code here...'"
                        parts = response.split("content=")
                        code_content = parts[1].strip("'")

                        # More robust dependency parsing
                        deps_part = parts[0].split("dependencies=")[1]
                        # Extract everything between [ and ]
                        deps_list = re.search(r"\[(.*?)\]", deps_part)
                        if deps_list:
                            # Split by comma, clean each dependency
                            dependencies = [
                                dep.strip().strip("'").strip('"').strip()
                                for dep in deps_list.group(1).split(",")
                                if dep.strip()
                            ]
                        else:
                            dependencies = []

                        print(f"Extracted dependencies: {dependencies}")

                        # Store what executor needs directly
                        if self.executor_deps:
                            self.executor_deps.content = {
                                "content": code_content,
                                "dependencies": dependencies,
                            }
                        log = "Coder agent response received and messages stored"
                        logfire.info(log)
                        if (
                            self.stream_output
                            and self.stream_output.agent_name == agent.name
                        ):
                            self.stream_output.steps.append(log)
                            if self.websocket:
                                await self.websocket.send_text(
                                    json.dumps(asdict(self.stream_output))
                                )

                        print(f"Coder agent response : {response}")
                        print(f"Parsed content and dependencies:")
                        print(f"Dependencies: {dependencies}")
                        print(f"Content : {code_content}")
                        if (
                            self.stream_output
                            and self.stream_output.agent_name == agent.name
                        ):
                            self.stream_output.output = code_content
                            self.stream_output.status_code = 200
                            self.orchestrator_response.append(self.stream_output)
                            if self.websocket:
                                await self.websocket.send_text(
                                    json.dumps(asdict(self.stream_output))
                                )
                    except Exception as e:
                        logfire.error(f"Failed to parse coder response: {e}")
                        print(f"Raw response for debugging: {response}")
                        raise OrchestratorError(f"Failed to parse coder response: {e}")

                else:
                    logfire.error(f"Failed to execute coder instruction: {response}")

            elif isinstance(agent, Executor):
                if not self.executor_deps or not self.executor_deps.content:
                    logfire.error("No coder result available for executor")
                    raise OrchestratorError(
                        "Executor deps not properly initialized with coder result"
                    )

                print(
                    f"Executor dependencies: {self.executor_deps.content.get('dependencies', [])}"
                )
                if self.stream_output and self.stream_output.agent_name == agent.name:
                    self.stream_output.steps.append(
                        "Executing the code in a safe environment"
                    )
                    if self.websocket:
                        await self.websocket.send_text(
                            json.dumps(asdict(self.stream_output))
                        )
                success, response, messages = await agent.generate_reply(
                    instruction, deps=self.executor_deps
                )

                if success:
                    self.chat_history = [*self.chat_history, *messages]
                    log = "Executor agent response received and messages stored"
                    logfire.info(log)
                    print(f"Executor agent response: {response}")
                    logfire.info(f"Executor agent messages: {messages}")

                    if (
                        self.stream_output
                        and self.stream_output.agent_name == agent.name
                    ):
                        self.stream_output.steps.append(log)
                        if self.websocket:
                            await self.websocket.send_text(
                                json.dumps(asdict(self.stream_output))
                            )
                    if (
                        self.stream_output
                        and self.stream_output.agent_name == agent.name
                    ):
                        self.stream_output.output = response
                        self.stream_output.status_code = 200
                        self.orchestrator_response.append(self.stream_output)
                        if self.websocket:
                            await self.websocket.send_text(
                                json.dumps(asdict(self.stream_output))
                            )
                else:
                    logfire.error(f"Failed to execute executor instruction: {response}")

            elif isinstance(agent, FileSurfer):
                success, response, messages = await agent.generate_reply(instruction)

                if success:
                    self.chat_history = [*self.chat_history, *messages]
                    log = "FileSurfer response received and messages stored"
                    logfire.info(log)
                    if (
                        self.stream_output
                        and self.stream_output.agent_name == agent.name
                    ):
                        self.stream_output.steps.append(log)
                        if self.websocket:
                            await self.websocket.send_text(
                                json.dumps(asdict(self.stream_output))
                            )
                    print(f"FileSurfer response: {response}")
                    logfire.info(f"FileSurfer messages: {messages}")
                    if (
                        self.stream_output
                        and self.stream_output.agent_name == agent.name
                    ):
                        self.stream_output.output = response
                        self.stream_output.status_code = 200
                        self.orchestrator_response.append(self.stream_output)
                        if self.websocket:
                            await self.websocket.send_text(
                                json.dumps(asdict(self.stream_output))
                            )
                else:
                    logfire.error(
                        f"Failed to execute FileSurfer instruction: {response}"
                    )

            else:
                raise OrchestratorError(f"Unknown agent type: {type(agent)}")

        except Exception as e:
            logfire.error(
                f"Failed to execute agent instruction: {str(e)}", exc_info=True
            )
            if self.stream_output and self.stream_output.agent_name == agent.name:
                self.stream_output.status_code = 500
                self.stream_output.output = str(e)

            raise

    async def prepare_final_answer(self, task) -> str:
        """Called when the task is complete"""

        final_message = ORCHESTRATOR_GET_FINAL_ANSWER.format(task=task)

        final_answer_subagent = Agent(
            model=self.model, name="Final Answer Sub-Agent", system_prompt=""
        )

        self.final_answer = await final_answer_subagent.run(
            final_message, message_history=self.chat_history
        )

        return self.final_answer.data

    async def run(self, task, websocket):
        """Main orchestration loop"""
        stream_output = StreamResponse(
            agent_name="Orchestrator",
            instructions=task,
            steps=[],
            output="",
            status_code=0,
        )
        try:
            # Initializing web socket and the orchestrator stream object
            self.websocket = websocket

            if self.websocket:
                await self.websocket.send_text(json.dumps(asdict(stream_output)))

            # Initialize agents
            self.agents = await self.initialize_agents()

            if stream_output.agent_name == "Orchestrator":
                stream_output.steps.append("Agents are initialized")
                if self.websocket:
                    await self.websocket.send_text(json.dumps(asdict(stream_output)))

            task = task.strip()
            if task.lower() == "exit":
                logfire.info("Shutting down orchestrator")

            if not task:
                logfire.warn("No valid task entered")

            # Initialize task and create plan
            plan = await self.initialize_task(task)
            if stream_output.agent_name == "Orchestrator":
                stream_output.steps.append(
                    "Curating a plan and selecting the best agent for you"
                )
                if self.websocket:
                    await self.websocket.send_text(json.dumps(asdict(stream_output)))
                self.orchestrator_response.append(stream_output)

            # Main execution loop
            while not self.ledger_manager.is_task_complete():
                # Update ledger state
                await self.update_ledger_state()

                # Check for stall and replan if needed
                if self.ledger_manager.handle_stall():
                    log = "Replanning due to stall"
                    logfire.info(log)
                    stream_output.steps.append(log)
                    if self.websocket:
                        await self.websocket.send_text(
                            json.dumps(asdict(stream_output))
                        )
                    plan = await self.initialize_task(task)
                    continue

                # Select and execute next agent
                next_agent = await self.select_next_agent()
                if next_agent:
                    instruction = self.ledger_manager.get_instruction() or ""
                    self.stream_output = StreamResponse(
                        agent_name=next_agent.name,
                        instructions=instruction,
                        steps=[],
                        output="",
                        status_code=0,
                    )
                    if self.websocket:
                        await self.websocket.send_text(
                            json.dumps(asdict(self.stream_output))
                        )
                    await self.execute_agent_instruction(next_agent)
                else:
                    logfire.warn("No agent selected, checking task completion")

            final_answer = await self.prepare_final_answer(task)
            if stream_output.agent_name == "Orchestrator":
                stream_output.output = final_answer
                stream_output.status_code = 200
                self.orchestrator_response.append(stream_output)

                if self.websocket:
                    await self.websocket.send_text(json.dumps(asdict(stream_output)))
            logfire.info(f"Final answer: {final_answer}")
            logfire.info(f"Message history: {self.chat_history}")

            print("\nFinal Answer : \n ", final_answer)
            print("\n")
            print("#" * 50)
            print("\n")

            logfire.info("Task completed successfully")

        except Exception as e:
            logfire.error(f"Critical error in orchestrator: {str(e)}", exc_info=True)
            if (
                stream_output
                and stream_output.agent_name == "Orchestrator"
                and not stream_output.output
            ):
                stream_output.output = str(e)
                stream_output.status_code = 500
                self.orchestrator_response.append(stream_output)
                if self.websocket:
                    await self.websocket.send_text(json.dumps(asdict(stream_output)))
            raise
        finally:
            logfire.info("Orchestrator shutdown complete")
            agent_response = [asdict(i) for i in self.orchestrator_response]
            self.orchestrator_response = []
            return agent_response
