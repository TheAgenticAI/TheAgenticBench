import json
import os
import time
import logfire
import asyncio
import logging
from typing import List, Optional, Tuple, Dict, Any
from dataclasses import dataclass
from functools import wraps
from agentic_bench.utils.markdown_browser import RequestsMarkdownBrowser
from pydantic_ai import Agent, RunContext
from pydantic_ai.messages import (
    SystemPromptPart,
    UserPromptPart,
    ModelRequest,
    ModelResponse,
    ModelMessage,
)
from pydantic_ai.models.openai import OpenAIModel
from dotenv import load_dotenv

load_dotenv()

# Custom exceptions
class FileSurferError(Exception):
    """Base exception class for FileSurfer"""

    pass

class BrowserNotInitializedError(FileSurferError):
    """Raised when browser is not initialized"""

    pass

class FileNotFoundError(FileSurferError):
    """Raised when file is not found"""

    pass

class NavigationError(FileSurferError):
    """Raised when navigation fails"""

    pass

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def error_handler(func):
    """Decorator for handling errors in async functions"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except FileSurferError as e:
            logger.error(f"FileSurfer error in {func.__name__}: {str(e)}")
            raise
        except Exception as e:
            logger.error(
                f"Unexpected error in {func.__name__}: {str(e)}", exc_info=True
            )
            raise FileSurferError(f"An unexpected error occurred: {str(e)}")
    return wrapper

@dataclass
class FileToolDependencies:
    browser: RequestsMarkdownBrowser

class FileSurfer:
    """An agent that uses tools to read and navigate local files with robust error handling."""

    def __init__(
        self,
        agent: Agent,
        name: str = "File Surfer Agent",
        browser: Optional[RequestsMarkdownBrowser] = None,
        system_prompt: str = "You are a helpful AI Assistant. When given a user query, use available functions to help the user with their request.",
        viewport_size: int = 1024 * 5,
        downloads_folder: str = "coding",
    ) -> None:
        """
        Initialize FileSurfer with error handling.

        Args:
            agent: The AI agent to use
            browser: Optional browser instance
            system_prompt: System prompt for the agent
            viewport_size: Size of the viewport
            downloads_folder: Folder for downloads

        Raises:
            FileSurferError: If initialization fails
        """
        try:
            self._agent: Agent = agent
            self._name: str = name
            self.description = "An agent that uses tools to read and navigate local files with robust error handling."
            self._browser: RequestsMarkdownBrowser = browser or RequestsMarkdownBrowser(
                viewport_size=viewport_size, downloads_folder=downloads_folder
            )
            self._chat_history: List[ModelMessage] = []
            self._system_prompt = system_prompt
            self._viewport_size = viewport_size
            self._downloads_folder = downloads_folder
            self._register_tools()
            logger.info("FileSurfer initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize FileSurfer: {str(e)}", exc_info=True)
            raise FileSurferError(f"Failed to initialize FileSurfer: {str(e)}")

    @property
    def name(self) -> str:
        """Get the agent's name"""
        return self._name

    @name.setter
    def name(self, value: str) -> None:
        """Set the agent's name"""
        self._name = value

    def _register_tools(self) -> None:
        """Register tools with error handling"""
        try:
            self._register_file_tools()
            self._register_navigation_tools()
            self._register_search_tools()
            logger.info("Tools registered successfully")
        except Exception as e:
            logger.error(f"Failed to register tools: {str(e)}", exc_info=True)
            raise FileSurferError(f"Failed to register tools: {str(e)}")

    def _register_file_tools(self) -> None:
        """Register file-related tools"""
        @self._agent.tool
        @error_handler
        async def open_local_file(
            ctx: RunContext[FileToolDependencies], path: str
        ) -> str:
            """Open a local file with error handling"""
            try:
                ctx.deps.browser.open_local_file(path)
                header, content = self._get_browser_state()
                return f"{header.strip()}\n=======================\n{content}"
            except Exception as e:
                logger.error(f"Failed to open file {path}: {str(e)}", exc_info=True)
                raise FileNotFoundError(f"Failed to open file {path}: {str(e)}")

    def _register_navigation_tools(self) -> None:
        """Register navigation tools"""
        @self._agent.tool
        @error_handler
        async def page_up(ctx: RunContext[FileToolDependencies]) -> str:
            """Scroll viewport up with error handling"""
            try:
                ctx.deps.browser.page_up()
                header, content = self._get_browser_state()
                return f"{header.strip()}\n=======================\n{content}"
            except Exception as e:
                logger.error(
                    f"Navigation error during page_up: {str(e)}", exc_info=True
                )
                raise NavigationError(f"Failed to scroll up: {str(e)}")

        @self._agent.tool
        @error_handler
        async def page_down(ctx: RunContext[FileToolDependencies]) -> str:
            """Scroll viewport down with error handling"""
            try:
                ctx.deps.browser.page_down()
                header, content = self._get_browser_state()
                return f"{header.strip()}\n=======================\n{content}"
            except Exception as e:
                logger.error(
                    f"Navigation error during page_down: {str(e)}", exc_info=True
                )
                raise NavigationError(f"Failed to scroll down: {str(e)}")

    def _register_search_tools(self) -> None:
        """Register search-related tools"""
        @self._agent.tool
        @error_handler
        async def find_on_page_ctrl_f(
            ctx: RunContext[FileToolDependencies], search_string: str
        ) -> str:
            """Search on page with error handling"""
            try:
                ctx.deps.browser.find_on_page(search_string)
                header, content = self._get_browser_state()
                return f"{header.strip()}\n=======================\n{content}"
            except Exception as e:
                logger.error(
                    f"Search error for string '{search_string}': {str(e)}",
                    exc_info=True,
                )
                raise NavigationError(
                    f"Failed to search for '{search_string}': {str(e)}"
                )

        @self._agent.tool
        @error_handler
        async def find_next(ctx: RunContext[FileToolDependencies]) -> str:
            """Find next occurrence with error handling"""
            try:
                ctx.deps.browser.find_next()
                header, content = self._get_browser_state()
                return f"{header.strip()}\n=======================\n{content}"
            except Exception as e:
                logger.error(f"Error finding next occurrence: {str(e)}", exc_info=True)
                raise NavigationError(f"Failed to find next occurrence: {str(e)}")

    def _get_browser_state(self) -> Tuple[str, str]:
        """
        Get browser state with error handling

        Returns:
            Tuple[str, str]: Header and content

        Raises:
            BrowserNotInitializedError: If browser is not initialized
        """
        try:
            if self._browser is None:
                self._browser = RequestsMarkdownBrowser(
                    viewport_size=self._viewport_size,
                    downloads_folder=self._downloads_folder,
                )

            header = self._generate_header()
            return (header, self._browser.viewport)
        except Exception as e:
            logger.error(f"Failed to get browser state: {str(e)}", exc_info=True)
            raise BrowserNotInitializedError(f"Failed to get browser state: {str(e)}")

    def _generate_header(self) -> str:
        """Generate browser header with error handling"""
        try:
            header = [f"Address: {self._browser.address}"]

            if self._browser.page_title:
                header.append(f"Title: {self._browser.page_title}")

            current_page = self._browser.viewport_current_page
            total_pages = len(self._browser.viewport_pages)
            header.append(
                f"Viewport position: Showing page {current_page+1} of {total_pages}."
            )

            # Add history information
            address = self._browser.address
            for i in range(len(self._browser.history) - 2, -1, -1):
                if self._browser.history[i][0] == address:
                    header.append(
                        f"You previously visited this page {round(time.time() - self._browser.history[i][1])} seconds ago."
                    )
                    break

            return "\n".join(header)
        except Exception as e:
            logger.error(f"Failed to generate header: {str(e)}", exc_info=True)
            raise BrowserNotInitializedError(f"Failed to generate header: {str(e)}")

    @error_handler
    async def generate_reply(
        self, user_message: str
    ) -> Tuple[bool, str, List[ModelMessage]]:
        """
        Generate reply to user message with error handling

        Args:
            user_message: User's input message

        Returns:
            Tuple[bool, str]: Success status and response

        Raises:
            FileSurferError: If reply generation fails
        """
        try:
            if self._browser is None:
                self._browser = RequestsMarkdownBrowser(
                    viewport_size=self._viewport_size,
                    downloads_folder=self._downloads_folder,
                )

            context_message = UserPromptPart(
                content=f"Your browser is currently open to the page '{self._browser.page_title}' at the address '{self._browser.address}'.",
            )

            message_history = self._build_message_history(context_message)
            deps = FileToolDependencies(browser=self._browser)

            response = await self._agent.run(
                user_prompt=user_message, message_history=message_history, deps=deps
            )

            self._chat_history = response.all_messages()
            logger.info("Successfully generated reply")

            # Convert response.data to the expected tuple format
            return (
                True,
                str(response.data),
                response.all_messages(),
            )  # Now returns Tuple[bool, str, List[ModelMessage]]

        except Exception as e:
            logger.error(f"Failed to generate reply: {str(e)}", exc_info=True)
            return False, str(e), []  # Return failure status and error message

    def _build_message_history(
        self, context_message: UserPromptPart
    ) -> List[ModelMessage]:
        """Build message history with error handling"""
        try:
            if not self._chat_history:
                system_message = SystemPromptPart(content=self._system_prompt)
                return [
                    ModelRequest(
                        parts=[system_message, context_message], kind="request"
                    )
                ]

            message_history = []
            for message in self._chat_history:
                if message.kind == "request":
                    message_history.append(
                        ModelRequest(parts=message.parts, kind=message.kind)
                    )
                else:
                    message_history.append(
                        ModelResponse(parts=message.parts, kind=message.kind)
                    )

            message_history.append(
                ModelRequest(parts=[context_message], kind="request")
            )
            return message_history

        except Exception as e:
            logger.error(f"Failed to build message history: {str(e)}", exc_info=True)
            raise FileSurferError(f"Failed to build message history: {str(e)}")

# Example usage
if __name__ == "__main__":
    try:
        # Configure logfire
        logfire.configure(
            send_to_logfire="if-token-present", token=os.getenv("LOGFIRE_TOKEN")
        )

        # Initialize OpenAI model
        model = OpenAIModel(
            model_name=os.getenv("AGENTIC_BENCH_MODEL_NAME", "gpt-4o"),
            api_key=os.getenv("AGENTIC_BENCH_MODEL_API_KEY"),
            base_url=os.getenv("AGENTIC_BENCH_MODEL_BASE_URL"),
        )

        # Initialize agent and file surfer
        agent = Agent(model, deps_type=FileToolDependencies)
        file_surfer = FileSurfer(
            agent=agent,
            browser=RequestsMarkdownBrowser(
                viewport_size=1024 * 5, downloads_folder="coding"
            ),
        )

        # Main interaction loop
        while True:
            try:
                user_message = input("\nEnter your question (type 'exit' to quit): ")
                if user_message.lower() == "exit":
                    break

                result = asyncio.run(
                    file_surfer.generate_reply(user_message=user_message)
                )
                print("Response:", result)

            except KeyboardInterrupt:
                logger.info("Program terminated by user")
                break
            except Exception as e:
                logger.error(f"Error processing message: {str(e)}", exc_info=True)
                print(f"An error occurred: {str(e)}")

    except Exception as e:
        logger.critical(f"Critical error in main: {str(e)}", exc_info=True)
        raise
