import asyncio
import logging
import os
from typing import Any, Dict, List

import aiohttp
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables from .env if present
load_dotenv()

async def search_market_data(query: str) -> List[Dict[str, str]]:
    """
    Search market data using Tavily Search API.
    
    Args:
        query: The search query string.
        
    Returns:
        A list of dictionaries containing 'content' and 'url' from top results.
    """
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        logger.error("TAVILY_API_KEY environment variable is not set.")
        return []

    url = "https://api.tavily.com/search"
    payload = {
        "api_key": api_key,
        "query": query,
        "search_depth": "advanced",
        "include_raw_content": False,
        "max_results": 3
    }

    try:
        timeout = aiohttp.ClientTimeout(total=30)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(url, json=payload) as response:
                if response.status != 200:
                    text = await response.text()
                    logger.error(f"Tavily API returned status code {response.status}: {text}")
                    return []
                
                try:
                    data: Dict[str, Any] = await response.json()
                except Exception as json_err:
                    logger.error(f"Failed to parse JSON response: {json_err}")
                    return []

                if "results" not in data:
                    logger.error("Key 'results' missing in Tavily API response.")
                    return []
                
                results = data["results"]
                if not isinstance(results, list):
                    logger.error("'results' field is not a list in Tavily API response.")
                    return []

                raw_contents = []
                for idx, result in enumerate(results[:3]):
                    if not isinstance(result, dict):
                        continue
                    content = result.get("content", "")
                    res_url = result.get("url", "")
                    if content:
                        raw_contents.append({
                            "content": str(content),
                            "url": str(res_url)
                        })

                return raw_contents

    except Exception as e:
        logger.error(f"An unexpected error occurred during search: {e}")

    return []
