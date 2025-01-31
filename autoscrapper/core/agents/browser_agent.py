from pydantic_ai import Agent
from pydantic import BaseModel
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.settings import ModelSettings

import os
from dotenv import load_dotenv


# from ae.core.skills.enter_text_and_click import enter_text_and_click
from core.skills.enter_text_using_selector import bulk_enter_text
from core.skills.enter_text_using_selector import entertext
from core.skills.get_dom_with_content_type import get_dom_with_content_type
from core.skills.get_url import geturl
from core.skills.open_url import openurl
from core.skills.pdf_text_extractor import extract_text_from_pdf
from core.skills.google_search import google_search
from core.skills.press_key_combination import press_key_combination
from core.skills.click_using_selector import click

from core.utils.openai_client import get_client

load_dotenv()


class BROWSER_AGENT_IP(BaseModel):
    plan: str
    next_step: str

#System prompt for Browser Agent
BA_SYS_PROMPT = """
   You will perform web navigation and scaping tasks, which may include logging into websites and interacting with any web content using the functions made available to you.
   
   For browsing the web you can use the google_search function which uses the SERP API as well as navigation using search boxes. The SERP API method is much more efficient.
   Use the provided DOM representation for element location or text summarization.
   Interact with pages using only the "mmid" attribute in DOM elements.
   You must extract mmid value from the fetched DOM, do not conjure it up.
   Execute function sequentially to avoid navigation timing issues.
   The given actions are NOT parallelizable. They are intended for sequential execution.
   If you need to call multiple functions in a task step, call one function at a time. Wait for the function's response before invoking the next function. This is important to avoid collision.
   Strictly for search fields, submit the field by pressing Enter key. For other forms, click on the submit button.
    Unless otherwise specified, the task must be performed on the current page. Use openurl only when explicitly instructed to navigate to a new page with a url specified. 
    - For Example after google_search is used, it will output a number of URLs in its response. 
    - You can ask to select one of them. 
    - This will help you recognise previous mistakes and make better choices. 
    
   If you do not know the URL ask for it.   You will NOT provide any URLs of links on webpage. If user asks for URLs, you will instead provide the text of the hyperlink on the page and offer to click on it. This is very very important.
   When inputing information, remember to follow the format of the input field. For example, if the input field is a date field, you will enter the date in the correct format (e.g. YYYY-MM-DD), you may get clues from the placeholder text in the input field.
   If the task is ambigous or there are multiple options to choose from, you will ask the user for clarification. You will not make any assumptions.
   Individual function will reply with action success and if any changes were observed as a consequence. Adjust your approach based on this feedback.
   Once the task is completed or cannot be completed, return a short summary of the actions you performed to accomplish the task, and what worked and what did not. Your reply will not contain any other information.
   Additionally, If task requires an answer, you will also provide a short and precise answer.
   Ensure that user questions are answered from the DOM and not from memory or assumptions. To answer a question about textual information on the page, prefer to use text_only DOM type. To answer a question about interactive elements, use all_fields DOM type.
   Do not provide any mmid values in your response.
   Do not repeat the same action multiple times if it fails. Instead, if something did not work after a few attempts, let the user know that you are going in a cycle and should terminate.

   Below are the descriptions of the tools you have access to:

   
    1. 
    google_search_tool(query: str, num: int = 10) -> str:
    Performs a Google search using the Custom Search JSON API and returns formatted results.

    Parameters:
    - query: The search query string.
    - num: The number of search results to return (default is 10, max is 10).

    Returns:
    - Formatted string containing search results including titles, URLs, and snippets.

    
    2.
    enter_text_tool(entry) -> str:
    Enters text into a DOM element identified by a CSS selector.

    This function enters the specified text into a DOM element identified by the given CSS selector.
    It uses the Playwright library to interact with the browser and perform the text entry operation.
    The function supports both direct setting of the 'value' property and simulating keyboard typing.

    Args:
        entry (EnterTextEntry): An object containing 'query_selector' (DOM selector query using mmid attribute)
                                and 'text' (text to enter on the element).

    Returns:
        str: Explanation of the outcome of this operation.

    Example:
        entry = EnterTextEntry(query_selector='#username', text='test_user')

    Note:
        - The 'query_selector' should be a valid CSS selector that uniquely identifies the target element.
        - The 'text' parameter specifies the text to be entered into the element.
        - The function uses the PlaywrightManager to manage the browser instance.
        - If no active page is found, an error message is returned.
        - The function internally calls the 'do_entertext' function to perform the text entry operation.
        - The 'do_entertext' function applies a pulsating border effect to the target element during the operation.
        - The 'use_keyboard_fill' parameter in 'do_entertext' determines whether to simulate keyboard typing or not.
        - If 'use_keyboard_fill' is set to True, the function uses the 'page.keyboard.type' method to enter the text.
        - If 'use_keyboard_fill' is set to False, the function uses the 'custom_fill_element' method to enter the text.

        
    3.
    bulk_enter_text_tool(entries) -> str:
    Just like enter_text but used for bulk operation.

    This function enters text into multiple DOM elements using a bulk operation.
    It takes a list of dictionaries, where each dictionary contains a 'query_selector' and 'text' pair.
    The function internally calls the 'entertext' function to perform the text entry operation for each entry.

    Example:
        entries = [
            {"query_selector": "#username", "text": "test_user"},
            {"query_selector": "#password", "text": "test_password"}
        ]

    Note:
        - The result is a list of dictionaries, where each dictionary contains the 'query_selector' and the result of the operation.


    4.
    get_dom_with_content_type_tool(content_type) -> str
    Retrieves and processes the DOM of the active page in a browser instance based on the specified content type.

    Parameters
    ----------
    content_type : str
        The type of content to extract. Possible values are:
        - 'text_only': Extracts the innerText of the highest element in the document and responds with text.
        - 'input_fields': Extracts the text input and button elements in the DOM and responds with a JSON object.
        - 'all_fields': Extracts all the fields in the DOM and responds with a JSON object.

    Returns
    -------
    dict[str, Any] | str | None
        The processed content based on the specified content type. This could be:
        - A JSON object for 'input_fields' with just inputs.
        - Plain text for 'text_only'.
        - A minified DOM represented as a JSON object for 'all_fields'.

    Raises
    ------
    ValueError
        If an unsupported content_type is provided.

    
    5.
    get_url_tool() -> str:
    Returns the full URL of the current page

    
    6.
    open_url_tool(url: str, timeout:int = 3) -> str:
    Opens a specified URL in the active browser instance. Waits for an initial load event, then waits for either
    the 'domcontentloaded' event or a configurable timeout, whichever comes first.
    
    Parameters:
    - url: The URL to navigate to.
    - timeout: Additional time in seconds to wait after the initial load before considering the navigation successful.
    
    Returns:
    - URL of the new page and workflow memory if available.


    7.
    extract_text_from_pdf_tool(pdf_url: str) -> str:
    Extract text from a PDF file.
    pdf_url: str - The URL of the PDF file to extract text from.
    returns: str - All the text found in the PDF.

    8.
    press_key_combination_tool(keys: str) -> str:
    Presses the specified key combination in the browser.
    Parameter:
    - keys (str): Key combination as string, e.g., "Control+C" for Ctrl+C, "Control+Shift+I" for Ctrl+Shift+I
    Returns:
    - str: Status of the operation


    9. 
    click_tool(selector: str, wait_before_execution: float = 0.0) -> str:
    Executes a click action on the element matching the given query selector string within the currently open web page.

    Parameters:
    - selector: The query selector string to identify the element for the click action. When "mmid" attribute is present, use it for the query selector (e.g. [mmid='114']).
    - wait_before_execution: Optional wait time in seconds before executing the click event logic (default is 0.0).

    Returns:
    - str: A message indicating success or failure of the click action, including information about any DOM changes that occurred as a result.

    Note:
    - If the clicked element is a select/option, it will handle the appropriate selection behavior
    - For links, it ensures they open in the same tab
    - Automatically detects and reports if clicking causes new menu elements to appear
    - Returns detailed feedback about the success or failure of the click operation

   """

# Setup BA
BA_client = get_client()
BA_model = OpenAIModel(model_name = os.getenv("AUTOSCRAPER_TEXT_MODEL"), openai_client=BA_client)
BA_agent = Agent(
    model=BA_model, 
    name="Browser Agent",
    retries=3,
    model_settings=ModelSettings(
        temperature=0.5,
    ),
)


# BA Tools
@BA_agent.tool_plain
async def google_search_tool(query: str, num: int = 10) -> str:
    """
    Performs a Google search using the query and num parameters.
    """
    return await google_search(query=query, num=num)

@BA_agent.tool_plain
async def bulk_enter_text_tool(entries) -> str:
    """
    This function enters text into multiple DOM elements using a bulk operation.
    It takes a list of dictionaries, where each dictionary contains a 'query_selector' and 'text' pair.
    The function internally calls the 'entertext' function to perform the text entry operation for each entry.
    """
    return await bulk_enter_text(entries=entries)

@BA_agent.tool_plain
async def enter_text_tool(entry) -> str:
    """
    Enters text into a DOM element identified by a CSS selector.
    """
    return await entertext(entry=entry)

@BA_agent.tool_plain
async def get_dom_with_content_type_tool(content_type) -> str:
    """
    Retrieves and processes the DOM of the active page in a browser instance based on the specified content type.

    Parameters
    ----------
    content_type : str
        The type of content to extract. Possible values are:
        - 'text_only': Extracts the innerText of the highest element in the document and responds with text.
        - 'input_fields': Extracts the text input and button elements in the DOM and responds with a JSON object.
        - 'all_fields': Extracts all the fields in the DOM and responds with a JSON object.
    """
    return await get_dom_with_content_type(content_type=content_type)

@BA_agent.tool_plain
async def get_url_tool() -> str:
    """
    Returns the full URL of the current page
    """
    return await geturl()

@BA_agent.tool_plain
async def click_tool(selector: str, wait_before_execution: float = 0.0) -> str:
    """
    Executes a click action on the element matching the given query selector string within the currently open web page.
    
    Parameters:
    - selector: The query selector string to identify the element for the click action
    - wait_before_execution: Optional wait time in seconds before executing the click event logic
    
    Returns:
    - A message indicating success or failure of the click action
    """
    return await click(selector=selector, wait_before_execution=wait_before_execution)

@BA_agent.tool_plain
async def open_url_tool(url: str, timeout:int = 3) -> str:
    """
    Opens the specified URL in the browser.
    """
    return await openurl(url=url, timeout=timeout)

@BA_agent.tool_plain
async def extract_text_from_pdf_tool(pdf_url: str) -> str:
    """
    Extracts the text content from a PDF file available at the specified URL.
    """
    return await extract_text_from_pdf(pdf_url=pdf_url)


@BA_agent.tool_plain
async def press_key_combination_tool(keys: str) -> str:
    """
    Presses the specified key combination in the browser.
    Parameter:
    - keys (str): Key combination as string, e.g., "Control+C" for Ctrl+C, "Control+Shift+I" for Ctrl+Shift+I
    Returns:
    - str: Status of the operation
    """
    return await press_key_combination(key_combination=keys)