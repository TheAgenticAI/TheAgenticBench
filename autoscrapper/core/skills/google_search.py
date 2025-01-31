from typing import Annotated
import requests
import os

from core.utils.logger import logger

async def google_search(query: str, num: int = 10) -> Annotated[str, "Performs a Google search and returns formatted results"]:
    """
    Performs a Google search using the Custom Search JSON API and returns formatted results.

    Parameters:
    - query: The search query string.
    - num: The number of search results to return (default is 10, max is 10).

    Returns:
    - Formatted string containing search results including titles, URLs, and snippets.
    """
    try:
        api_key = os.getenv('GOOGLE_API_KEY')
        cx = os.getenv('GOOGLE_CX')

        if not api_key or not cx:
            raise ValueError("GOOGLE_API_KEY or GOOGLE_CX environment variables are not set.")

    
        base_url = "https://www.googleapis.com/customsearch/v1"
        params = {
            "key": api_key,
            "cx": cx,
            "q": query,
            "num": min(num, 10)  # Ensure num doesn't exceed 10
        }
    
        response = requests.get(base_url, params=params)
        response.raise_for_status()  # Raises an HTTPError for bad responses
        results = response.json()

        formatted_results = f"Search Results for '{query}':\n"
        formatted_results += f"Total Results: {results.get('searchInformation', {}).get('formattedTotalResults', 'N/A')}\n"
        formatted_results += f"Search Time: {results.get('searchInformation', {}).get('formattedSearchTime', 'N/A')} seconds\n\n"

        for item in results.get("items", []):
            formatted_results += f"Title: {item.get('title', 'N/A')}\n"
            formatted_results += f"URL: {item.get('link', 'N/A')}\n"
            formatted_results += f"Snippet: {item.get('snippet', 'N/A')}\n\n"
        
        logger.info(f"Google search results for query '{query}'")
        logger.info(formatted_results)
        return formatted_results

    except requests.RequestException as e:
        return f"Error performing Google search: {str(e)}"
    except ValueError as e:
        return str(e)
    except Exception as e:
        return f"An unexpected error occurred: {str(e)}"