from __future__ import annotations

import asyncio
import logging
import shlex
import sys
import uuid
from collections.abc import Sequence
from hashlib import sha256
from pathlib import Path
from types import TracebackType
from typing import Any, Callable, ClassVar, List, Optional, ParamSpec, Type, Union
from dataclasses import asdict
import json
from utils.stream_response_format import StreamResponse
from fastapi import WebSocket
from utils import CancellationToken
from .executor_utils import (
    CodeBlock,
    CodeExecutor,
    FunctionWithRequirements,
    FunctionWithRequirementsStr,
)
from utils.executors.executor_utils.extract_command_line_args import extract_command_line_args
from .executor_utils._common import (
    CommandLineCodeResult,
    build_python_functions_file,
    get_file_name_from_content,
    lang_to_cmd,
    silence_pip,
)

if sys.version_info >= (3, 11):
    from typing import Self
else:
    from typing_extensions import Self

async def _wait_for_ready(
    container: Any, timeout: int = 60, stop_time: float = 0.1
) -> None:
    elapsed_time = 0.0
    while container.status != "running" and elapsed_time < timeout:
        await asyncio.sleep(stop_time)
        elapsed_time += stop_time
        await asyncio.to_thread(container.reload)
        continue
    if container.status != "running":
        raise ValueError("Container failed to start")

A = ParamSpec("A")

class DockerCommandLineCodeExecutor(CodeExecutor):
    """Executes code through a command line environment in a Docker container.

    The executor first saves each code block in a file in the working
    directory, and then executes the code file in the container.
    The executor executes the code blocks in the order they are received.
    Currently, the executor only supports Python and shell scripts.
    For Python code, use the language "python" for the code block.
    For shell scripts, use the language "bash", "shell", or "sh" for the code
    block.

    Args:
        image (_type_, optional): Docker image to use for code execution.
            Defaults to "python:3-slim".
        container_name (Optional[str], optional): Name of the Docker container
            which is created. If None, will autogenerate a name. Defaults to None.
        timeout (int, optional): The timeout for code execution. Defaults to 60.
        work_dir (Union[Path, str], optional): The working directory for the code
            execution. Defaults to Path(".").
        bind_dir (Union[Path, str], optional): The directory that will be bound
        to the code executor container. Useful for cases where you want to spawn
        the container from within a container. Defaults to work_dir.
        auto_remove (bool, optional): If true, will automatically remove the Docker
            container when it is stopped. Defaults to True.
        stop_container (bool, optional): If true, will automatically stop the
            container when stop is called, when the context manager exits or when
            the Python process exits with atext. Defaults to True.
        functions (List[Union[FunctionWithRequirements[Any, A], Callable[..., Any]]]): A list of functions that are available to the code executor. Default is an empty list.
        functions_module (str, optional): The name of the module that will be created to store the functions. Defaults to "functions".
    """

    SUPPORTED_LANGUAGES: ClassVar[List[str]] = [
        "bash",
        "shell",
        "sh",
        "pwsh",
        "powershell",
        "ps1",
        "python",
    ]

    FUNCTION_PROMPT_TEMPLATE: ClassVar[
        str
    ] = """You have access to the following user defined functions. They can be accessed from the module called `$module_name` by their function names.

For example, if there was a function called `foo` you could import it by writing `from $module_name import foo`

$functions"""

    def __init__(
        self,
        image: str = "python:3-slim",
        container_name: Optional[str] = None,
        *,
        timeout: int = 60,
        work_dir: Union[Path, str] = Path("./code_files"),
        bind_dir: Optional[Union[Path, str]] = None,
        auto_remove: bool = True,
        stop_container: bool = True,
        functions: Sequence[
            Union[
                FunctionWithRequirements[Any, A],
                Callable[..., Any],
                FunctionWithRequirementsStr,
            ]
        ] = [],
        functions_module: str = "functions",
    ):
        if timeout < 1:
            raise ValueError("Timeout must be greater than or equal to 1.")

        if isinstance(work_dir, str):
            work_dir = Path(work_dir)
        work_dir.mkdir(exist_ok=True)

        if bind_dir is None:
            bind_dir = work_dir
        elif isinstance(bind_dir, str):
            bind_dir = Path(bind_dir)

        if container_name is None:
            self.container_name = f"agentic-bench-code-exec-{uuid.uuid4()}"
        else:
            self.container_name = container_name

        self._timeout = timeout
        self._work_dir: Path = work_dir
        self._bind_dir: Path = bind_dir

        self._auto_remove = auto_remove
        self._stop_container = stop_container
        self._image = image

        if not functions_module.isidentifier():
            raise ValueError("Module name must be a valid Python identifier")

        self._functions_module = functions_module
        self._functions = functions
        # Setup could take some time so we intentionally wait for the first code block to do it.
        self._setup_functions_complete = False
        self.websocket:Optional[WebSocket]= None
        self.stream_output:Optional[StreamResponse] = None
        # else:
        #     self._setup_functions_complete = True

        try:
            from docker.models.containers import Container
        except ImportError as e:
            raise RuntimeError(
                "Missing dependecies for DockerCommandLineCodeExecutor"
            ) from e

        self._container: Container | None = None
        self._running = False

    @property
    def timeout(self) -> int:
        """(Experimental) The timeout for code execution."""
        return self._timeout

    @property
    def work_dir(self) -> Path:
        """(Experimental) The working directory for the code execution."""
        return self._work_dir

    @property
    def bind_dir(self) -> Path:
        """(Experimental) The binding directory for the code execution container."""
        return self._bind_dir

    async def install_packages(self, packages):
        import docker
        client = docker.from_env()
        command = f"pip install {' '.join(packages)}"
        if self.stream_output and self.websocket:
            self.stream_output.steps.append(
                "Installing the code dependencies in your docker environment before the code execution"
            )
            await self.websocket.send_text(
                json.dumps(asdict(self.stream_output))
            )
        exit_code, output = self._container.exec_run(command)
        if exit_code == 0:
            print("packages installed successfully")
        else:
            print("packages installation failed")

    async def _setup_functions(
        self, code_blocks: List[CodeBlock], cancellation_token: CancellationToken
    ) -> None:
        await self.start()
        required_packages = code_blocks[0].packages
        if len(required_packages) > 0:
            log="Ensuring packages are installed in executor."
            logging.info(log)
            if self.stream_output and self.websocket:
                self.stream_output.steps.append(
                    log
                )
                await self.websocket.send_text(
                    json.dumps(asdict(self.stream_output))
                )


            packages = shlex.join(required_packages)
            # result = await self._execute_code_dont_check_setup(
            #     [CodeBlock(code=f"python -m pip install {packages}",packages=packages, language="sh")], cancellation_token
            # )
            try:
                await self.install_packages(required_packages)
            except Exception as e:
                raise ValueError(f"Pip install failed")

        # Attempt to load the function file to check for syntax errors, imports etc.
        # exec_result = await self._execute_code_dont_check_setup(
        #     code_blocks, cancellation_token
        # )

        # if exec_result.exit_code != 0:
        #     raise ValueError(f"Functions failed to load: {exec_result.output}")

        self._setup_functions_complete = True

    async def _execute_code_dont_check_setup(
        self, code_blocks: List[CodeBlock], cancellation_token: CancellationToken
    ) -> CommandLineCodeResult:
        if self._container is None and not self._running:
            print("None and not running")
            raise ValueError(
                "Container is not created and not running. Must first be started with either start or a context manager."
            )
        elif not self._running:
            print("Not none but not running")
            await self.restart()
            print(self._running)
        if len(code_blocks) == 0:
            raise ValueError("No code blocks to execute.")

        outputs: List[str] = []
        files: List[Path] = []
        last_exit_code = 0
        for code_block in code_blocks:
            lang = code_block.language.lower()
            code = silence_pip(code_block.code, lang)
            # Check if there is a filename comment
            try:
                filename = get_file_name_from_content(code, self._work_dir)
            except ValueError:
                outputs.append("Filename is not in the workspace")
                last_exit_code = 1
                break
            if self.stream_output and self.websocket:
                self.stream_output.steps.append(
                    f"Saving the code in a file under the directory: {self._work_dir}"
                )
                await self.websocket.send_text(
                    json.dumps(asdict(self.stream_output))
                )
            if not filename:
                filename = f"tmp_code_{sha256(code.encode()).hexdigest()}.{lang}"

            code_path = self._work_dir / filename
            with code_path.open("w", encoding="utf-8") as fout:
                fout.write(code)
            files.append(code_path)

            human_input_or_command_line_args = code_block.human_input_or_command_line_args

            command_line_args = extract_command_line_args(lang, filename, human_input_or_command_line_args)
            print("extracted command_line_args", command_line_args)

            command = ["timeout", str(self._timeout), lang_to_cmd(lang), filename, *command_line_args]
            if self.stream_output and self.websocket:
                self.stream_output.steps.append(
                    "Executing the generated code in your safe environment"
                )
                await self.websocket.send_text(
                    json.dumps(asdict(self.stream_output))
                )
            result = await asyncio.to_thread(self._container.exec_run, command)  # type: ignore
            exit_code = result.exit_code
            output = result.output.decode("utf-8")
            if exit_code == 124:
                output += "\n Timeout"
            outputs.append(output)

            last_exit_code = exit_code
            if exit_code != 0:
                break

        code_file = str(files[0]) if files else None
        return CommandLineCodeResult(
            exit_code=last_exit_code, output="".join(outputs), code_file=code_file
        )

    async def execute_code_blocks(
        self, code_blocks: List[CodeBlock], 
        websocket:WebSocket,stream_output:StreamResponse, cancellation_token: CancellationToken
    ) -> CommandLineCodeResult:
        """(Experimental) Execute the code blocks and return the result.

        Args:
            code_blocks (List[CodeBlock]): The code blocks to execute.

        Returns:
            CommandlineCodeResult: The result of the code execution."""
        self.websocket=websocket
        self.stream_output=stream_output
        def raise_not_implemented() -> None:
            raise NotImplementedError(
                "Cancellation is not yet supported for DockerCommandLineCodeExecutor"
            )
        cancellation_token.add_callback(lambda: raise_not_implemented())

        if not self._setup_functions_complete:
            await self._setup_functions(code_blocks, cancellation_token)

        return await self._execute_code_dont_check_setup(
            code_blocks, cancellation_token
        )

    async def restart(self) -> None:
        if self._container is None and not self._running:
            print("None and not running")
            raise ValueError(
                "Container is not running. Must first be started with either start or a context manager."
            )

        """(Experimental) Restart the code executor."""
        await asyncio.to_thread(self._container.restart)  # type: ignore
        if self._container.status != "running":
            self._running = False
            logs_str = self._container.logs().decode("utf-8")
            raise ValueError(f"Failed to restart container. Logs: {logs_str}")

    async def stop(self) -> None:
        """(Experimental) Stop the code executor."""

        if not self._running:
            return

        try:
            import docker
            from docker.errors import NotFound
        except ImportError as e:
            raise RuntimeError(
                "Missing dependecies for DockerCommandLineCodeExecutor."
            ) from e

        client = docker.from_env()
        try:
            container = await asyncio.to_thread(
                client.containers.get, self.container_name
            )
            await asyncio.to_thread(container.stop)
        except NotFound:
            pass
        finally:
            self._running = False

    async def start(self) -> None:
        try:
            import asyncio_atexit
            import docker
            from docker.errors import DockerException, ImageNotFound
        except ImportError as e:
            raise RuntimeError(
                "Missing dependecies for DockerCommandLineCodeExecutor."
            ) from e

        # Start a container from the image, read to exec commands later
        try:
            client = docker.from_env()
        except DockerException as e:
            if "FileNotFoundError" in str(e):
                raise RuntimeError(
                    "Failed to connect to Docker. Please ensure Docker is installed and running."
                ) from e
            raise
        except Exception as e:
            raise RuntimeError(
                f"Unexpected error while connecting to Docker: {str(e)}"
            ) from e

        # Check if the image exists
        try:
            await asyncio.to_thread(client.images.get, self._image)
        except ImageNotFound:
            # TODO logger
            logging.info(f"Pulling image {self._image}...")
            # Let the docker exception escape if this fails.
            await asyncio.to_thread(client.images.pull, self._image)
        if self._container is None:
            self._container = await asyncio.to_thread(
                client.containers.create,
                self._image,
                name=self.container_name,
                entrypoint="/bin/sh",
                tty=True,
                detach=True,
                auto_remove=self._auto_remove,
                volumes={
                    str(self._bind_dir.resolve()): {"bind": "/code_files", "mode": "rw"}
                },
                working_dir="/code_files",
            )
        await asyncio.to_thread(self._container.start)
        await _wait_for_ready(self._container)

        async def cleanup() -> None:
            await self.stop()
            asyncio_atexit.unregister(cleanup)  # type: ignore
        if self._stop_container:
            asyncio_atexit.register(cleanup)  # type: ignore

        # Check if the container is running
        if self._container.status != "running":
            logs_str = self._container.logs().decode("utf-8")
            raise ValueError(
                f"Failed to start container from image {self._image}. Logs: {logs_str}"
            )
        self._running = True

    async def __aenter__(self) -> Self:
        await self.start()
        return self

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> Optional[bool]:
        await self.stop()
        return None
