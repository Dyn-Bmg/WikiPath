"""
This module provides async utilities for interacting with the Wikimedia
REST API using aiohttp
"""
import asyncio
import aiohttp
from bs4 import BeautifulSoup
from link_validator import is_valid_link

async def get_links(session: aiohttp.ClientSession, page: str, seen: set, sem: asyncio.Semaphore) -> tuple[str, list[str]]:
    """
    Fetch all valid outgoing Wikipedia link titles from a given page.

    Args:
        session (aiohttp.ClientSession): An active "aiohttp.ClientSession"
        page (str): The Wikipedia page title
        seen (set): Set of visited page titles
        sem (asyncio.Semaphore): Semaphore that caps concurrent outgoing HTTP requests

    Returns:
        tuple[str, list[str]]: Tuple of (page_title,list of valid links).
        Return empty tuple on failure.
    """
    
    url = 'https://en.wikipedia.org/w/rest.php/v1/page/' + page + '/html'
    
    headers = {
        'User-Agent': 'WikiThread/1.0 (contact@example.com)'
    }
    try:
        async with sem:
            async with session.get(url, headers=headers) as response:
                wiki_text = await response.text()
                soup = BeautifulSoup(wiki_text, 'lxml-xml')
                table = soup.find_all('a', {'rel': "mw:WikiLink"})
                links = [link.get('href') for link in table ]
                links = list(set(links))
                links = [link.replace('_', ' ').replace('./', '') for link in links if is_valid_link(link,seen)]
                seen.update({link for link in links})
                await asyncio.sleep(1)
                page = page.replace('_', ' ').replace('./', '')
                return page,links
    except Exception as e:
        print(f"exception {e}")
        return ()

async def get_description(session: aiohttp.ClientSession, page: str, sem: asyncio.Semaphore) -> tuple[str,str]:
    """
    Retrieve the short description of a Wikipedia page via the search API.

    Args:
        session (aiohttp.ClientSession): An active "aiohttp.ClientSession"
        page (str): The wikipedia Page title
        sem (asyncio.Semaphore): Semaphore that caps concurrent outgoing HTTP requests

    Returns:
        tuple[str,str]: A tuple (page_title, description),
        with descritption in the format "page_title: short description".
        Return empty Tuple if no description or error.
    """
    url = 'https://en.wikipedia.org/w/rest.php/v1/search/page'
    params = {
    'q': page,
    'limit': '1'
    }
    headers = {
        'User-Agent': 'WikiThread/1.0 (contact@example.com)'
    }
    try:
        async with sem:
            async with session.get(url, headers=headers, params = params) as response:
                data = await response.json()
                pages = data.get("pages",[])
                if pages:
                    wiki_description = pages[0].get("description")
                    if wiki_description:
                        wiki_description = page + ": " + wiki_description
                        await asyncio.sleep(0.5)
                        return (page,wiki_description)
                else:
                    return ()
    except Exception as e:
        print(f"exception {e}")
        return ()