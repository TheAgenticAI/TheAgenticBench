import asyncio
from dataclasses import dataclass,asdict
from dotenv import load_dotenv
import logfire
import os
import re
import json
import time
from pydantic import Field, BaseModel
from pydantic_ai import Agent, RunContext
from pydantic_ai.messages import ModelMessage
from pydantic_ai.models.openai import OpenAIModel
from fastapi import WebSocket
from pydantic_ai.tools import AgentDeps
from typing import List, Type, Union, Callable, Awaitable, Literal, Tuple, Any, Optional
import tokenize
from io import StringIO
from utils.stream_response_format import StreamResponse
from utils import CancellationToken
from utils.executors.executor_utils import CodeBlock
from utils.executors import LocalCommandLineCodeExecutor as LocalCodeExecutor
from utils.executors import DockerCommandLineCodeExecutor as DockerCodeExecutor
from utils.executors.executor_utils._base import CodeExecutor
from utils.oai_client import get_client

load_dotenv()
coder_system_message = """You are a helpful AI assistant. Solve tasks using your coding and language skills.

    <critical>
        - Remember do not provide any test run snippets in the code block that print unnecessary answers in the terminal. The user will provide the test run inputs.
    <critical>

    In the following cases, suggest python code (in a python coding block) or shell script (in a sh coding block) for the user to execute.
        1. When you need to collect info, use the code to output the info you need, for example, browse or search the web, download/read a file, print the content of a webpage or a file, get the current date/time, check the operating system. After sufficient info is printed and the task is ready to be solved based on your language skill, you can solve the task by yourself.
        2. When you need to perform some task with code, use the code to perform the task and output the result. Finish the task smartly.
    Solve the task step by step if you need to. If a plan is not provided, explain your plan first. Be clear which step uses code, and which step uses your language skill.
    When using code, you must indicate the script type in the code block. The user cannot provide any other feedback or perform any other action beyond executing the code you suggest. The user can't modify your code. So do not suggest incomplete code which requires users to modify. Don't use a code block if it's not intended to be executed by the user.
    If you want the user to save the code in a file before executing it, put # filename: <filename> inside the code block as the first line. Don't include multiple code blocks in one response. Do not ask users to copy and paste the result. Instead, use 'print' function for the output when relevant. Check the execution result returned by the user.
    If the result indicates there is an error, fix the error and output the code again. Suggest the full code instead of partial code or code changes. If the error can't be fixed or if the task is not solved even after the code is executed successfully, analyze the problem, revisit your assumption, collect additional info you need, and think of a different approach to try.
    When you find an answer, verify the answer carefully. Include verifiable evidence in your response if possible.
    Reply "TERMINATE" in the end when everything is done."""
            

@dataclass
class CoderDependencies:
    description: str
    system_messages: str
    request_terminate: bool

class CoderResult(BaseModel):
    terminated: bool = Field(description="Whether the task is terminated")
    dependencies: List = Field(
        description="All the packages name that has to be installed before the code execution"
    )
    content: str = Field(description="Response content in the form of code")
    sample_input:str=Field(description="Simulation of human input for execution of the code")

class ExecutorDependencies(BaseModel):
    executor: CodeExecutor
    confirm_execution: Union[
        Callable[[CodeBlock], Awaitable[bool]], Literal["ACCEPT_ALL"]
    ]
    description: str
    system_message: str
    check_last_n_message: int
    content: Any

    class Config:
        arbitrary_types_allowed = True

class ExecutorResult(BaseModel):
    executed: bool = Field(description="Whether the code block was executed")
    content: str = Field(description="Execution result or message")

class CoderAgent:
    def __init__(
        self, agent: Agent[CoderDependencies, CoderResult], system_prompt: str
    ):
        try:
            self._agent = agent
            self.name = "Coder Agent"
            self.description = "An agent that can write code and has strong Python and Linux command line skills."
            self._system_prompt = system_prompt
            self.websocket:Optional[WebSocket]=None
            self.stream_output: Optional[StreamResponse] = None
            self.add_system_message()
        except Exception as e:
            logfire.error(f"Failed to initialize CoderAgent: {e}")
            raise

    def add_system_message(self):
        @self._agent.system_prompt
        async def add_system_messages(ctx: RunContext[CoderDependencies]) -> str:
            # Use raw string to prevent escape character issues
            return self._system_prompt

    async def is_python_code(self,content):
        try:
            if self.stream_output and self.websocket:
                self.stream_output.steps.append("Verifying if the code is a python based code")
                await self.websocket.send_text(json.dumps(asdict(self.stream_output)))
            tokens = tokenize.generate_tokens(StringIO(content).readline)
            for _ in tokens:
                pass  # Simply iterate through the tokens
            return True
        except tokenize.TokenError:
            return False
    
    async def ensure_code_block_format(self, code_content: str) -> str:
        """Ensure code is properly wrapped in markdown code block markers"""
        # Remove existing markers if present
        if("```python" in code_content):
            return code_content

        # Check if it's a proper Python code (has imports or typical Python syntax)
        if await self.is_python_code(code_content):
            return f"```python\n{code_content}\n```"
        return code_content

    async def generate_reply(
        self, user_message: str, deps: CoderDependencies,websocket:WebSocket,
                    stream_output:StreamResponse
    ) -> Tuple[bool, str, List[ModelMessage]]:
        """Generate reply from the coder agent"""
        try:
            self.websocket = websocket
            self.stream_output = stream_output
            print(f"\nInside generate reply message (Coder Agent)")
            print(f"User message: {user_message}")
            print(f"Dependencies: {deps}\n")
            if self.stream_output and self.websocket:
                self.stream_output.steps.append("Generating the code...")
                await self.websocket.send_text(json.dumps(asdict(self.stream_output)))
            result = await self._agent.run(user_message, deps=deps)
            if hasattr(result, "data"):
                # Ensure code is properly formatted
                content = (
                    str(result.data.content)
                    if hasattr(result.data, "content")
                    else str(result.data)
                )
                time.sleep(2)
                if self.stream_output and self.websocket:
                    self.stream_output.steps.append("Ensuring code is properly formatted")
                    await self.websocket.send_text(json.dumps(asdict(self.stream_output)))
                
                formatted_content = await self.ensure_code_block_format(content)

                # Build properly formatted response
                response = f"terminated={getattr(result.data, 'terminated', True)} "
                response += f"dependencies={getattr(result.data, 'dependencies', [])} "
                response += f"sample_input={getattr(result.data, 'sample_input', '')} "
                response += f"content='{formatted_content}'"

                return True, response, result.all_messages()
            else:
                return False, "No data in result", []

        except Exception as e:
            logfire.error(f"Failed to generate coder reply: {e}")
            return False, str(e), []

class Executor:
    def __init__(
        self, agent: Agent[ExecutorDependencies, ExecutorResult], system_prompt: str
    ):
        try:
            self._agent = agent
            self._system_prompt = system_prompt
            self.name = "Executor Agent"
            self.description = "A computer terminal that performs no other action than running Python scripts or sh shell scripts"
            self.websocket:Optional[WebSocket]=None
            self.stream_output: Optional[StreamResponse] = None
            self.add_system_message()
            self.register_tool()
        except Exception as e:
            print(e)

    def add_system_message(self):
        @self._agent.system_prompt
        async def add_executor_prompt(ctx: RunContext[ExecutorDependencies]) -> str:
            return "\n".join(ctx.deps.system_message)

    def register_tool(self):
        @self._agent.tool
        async def execute_code(
            ctx: RunContext[ExecutorDependencies],
        ) -> Tuple[bool, str]:
            try:
                # Now content is directly the dict we need
                response_block = ctx.deps.content
                print()
                print(f"Response block inside execute code: {response_block}")
                print()
                code = self.extract_execution_request(response_block["content"])
                print()
                print(f"Code block inside execute code: {code}")
                print()
                if code is not None:
                    code_lang = code[0]
                    code_block = code[1]
                    if code_lang == "py":
                        code_lang = "python"

                    execution_requests = [
                        CodeBlock(
                            code=code_block,
                            packages=response_block["dependencies"],
                            language=code_lang,
                            sample_input=response_block['sample_input'] if response_block['sample_input'] else ""
                        )
                    ]

                    if (
                        ctx.deps.confirm_execution == "ACCEPT_ALL"
                        or await ctx.deps.confirm_execution(execution_requests[0])
                    ):
                        result = await ctx.deps.executor.execute_code_blocks(
                            execution_requests,self.websocket,self.stream_output, cancellation_token=CancellationToken()
                        )

                        if result.output.strip() == "":
                            return (
                                False,
                                f"The script ran but produced no output to console. The Unix exit code was: {result.exit_code}. If you were expecting output, consider revising the script to ensure content is printed to stdout.",
                            )
                        else:
                            return (
                                True,
                                f"The script ran, then exited with Unix exit code: {result.exit_code}\nIts output was:\n{result.output}",
                            )
                    else:
                        return (
                            False,
                            "The code block was not confirmed by the user and so was not run.",
                        )
                return (
                    False,
                    "No code block detected in the content. Please provide a markdown-encoded code block to execute for the original task.",
                )

            except Exception as e:
                print(f"Error details: {str(e)}")
                raise e

    def extract_execution_request(
        self, markdown_text: str
    ) -> Union[Tuple[str, str], None]:
        pattern = r"```(\w+)\n(.*?)\n```"
        match = re.search(pattern, markdown_text, re.DOTALL)
        if match:
            return (match.group(1), match.group(2))
        return None

    async def generate_reply(
        self, user_message: str, deps: ExecutorDependencies,websocket: WebSocket, stream_output: StreamResponse) -> Tuple[bool, str, List[ModelMessage]]:
        try:
            self.websocket = websocket
            self.stream_output = stream_output
            result = await self._agent.run(user_message, deps=deps)
            print(
                f"Executor result (Inside executor agent generate reply): {result.data}"
            )
            return True, str(result.data), result.all_messages()
        except Exception as e:
            print(e)
            return False, str(e), []

if __name__ == "__main__":

    logfire.configure()
    model = OpenAIModel(
        model_name=os.getenv("AGENTIC_BENCH_MODEL_NAME", "gpt-4o"),
        api_key=os.getenv("AGENTIC_BENCH_MODEL_API_KEY"),
        base_url=os.getenv("AGENTIC_BENCH_MODEL_BASE_URL"),

    )

    coder_description = "A helpful and general-purpose AI assistant that has strong language skills, Python skills, and Linux command line skills."
    system_message = """You are a helpful AI assistant. Solve tasks using your coding and language skills.
    In the following cases, suggest python code (in a python coding block) or shell script (in a sh coding block) for the user to execute.
        1. When you need to collect info, use the code to output the info you need, for example, browse or search the web, download/read a file, print the content of a webpage or a file, get the current date/time, check the operating system. After sufficient info is printed and the task is ready to be solved based on your language skill, you can solve the task by yourself.
        2. When you need to perform some task with code, use the code to perform the task and output the result. Finish the task smartly.
    Solve the task step by step if you need to. If a plan is not provided, explain your plan first. Be clear which step uses code, and which step uses your language skill.
    When using code, you must indicate the script type in the code block. The user cannot provide any other feedback or perform any other action beyond executing the code you suggest. The user can't modify your code. So do not suggest incomplete code which requires users to modify. Don't use a code block if it's not intended to be executed by the user.
    If you want the user to save the code in a file before executing it, put # filename: <filename> inside the code block as the first line. Don't include multiple code blocks in one response. Do not ask users to copy and paste the result. Instead, use 'print' function for the output when relevant. Check the execution result returned by the user.
    If the result indicates there is an error, fix the error and output the code again. Suggest the full code instead of partial code or code changes. If the error can't be fixed or if the task is not solved even after the code is executed successfully, analyze the problem, revisit your assumption, collect additional info you need, and think of a different approach to try.
    When you find an answer, verify the answer carefully. Include verifiable evidence in your response if possible.
    Reply "TERMINATE" in the end when everything is done."""

    coder_deps = CoderDependencies(
        description=coder_description,
        system_messages=system_message,
        request_terminate=False,
    )
    agent = Agent(
        model,
        deps_type=coder_deps,
        result_type=CoderResult,  # type: ignore
        system_prompt=(
            "You are a helpful AI assistant that solves tasks using your coding and language skills."
        ),
    )
    coder_agent = CoderAgent(agent=agent, system_prompt=system_message)
    coder_result = asyncio.run(
        coder_agent.generate_reply(
            "Write a python program to create an api with fastapi which takes a number as input in arguments and returns its square.",
            deps=coder_deps,
        )
    )
    # print(coder_result)

    executor_system_message = "A computer terminal that performs no other action than running Python scripts (provided to it quoted in ```python code blocks), or sh shell scripts (provided to it quoted in ```sh code blocks)"
    executor_deps = ExecutorDependencies(
        executor=DockerCodeExecutor(),
        confirm_execution="ACCEPT_ALL",
        description="Executor to execute the generated code",
        system_message=executor_system_message,
        content=coder_result,
        check_last_n_message=5,
    )

    agent = Agent(
        model=model,
        deps_type=executor_deps,  # type: ignore
        result_type=ExecutorResult,
        system_prompt=(
            "You are a computer terminal that performs no other action than running Python scripts or sh shell scripts."
        ),
    )
    executor_agent = Executor(agent=agent, system_prompt=executor_system_message)  # type: ignore
    executor_result = asyncio.run(
        executor_agent.generate_reply("Execute the code", deps=executor_deps)
    )
    print(executor_result)
