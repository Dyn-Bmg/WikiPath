from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import aiohttp
import asyncio
from bs4 import BeautifulSoup
import heapq
from collections import deque

def is_valid_link(link: str,seen: set) -> bool:
    """
    Determine whether a Wikipedia href is worth following.
    Args:
        link (str): Raw href string
        seen (set): Set of visited page titles

    Returns:
        bool: True if the link should be followed, False otherwise
    """
    #
    EXCLUDED_PREFIXES = [
        "./Category:",
        "./Template:",
        "./Wikipedia:",
        "./Help:",
        "./File:",
        "./Image:",
        "./Talk:",
        "./User:",
        "./User_talk:",
        "./Portal:",
        "./Draft:",
        "./Module:",
        "./MediaWiki:",
        "./Special:",
        "./Book:",
        "./TimedText:",
        "./Gadget:",
        "./Template_talk:",
    ]
    
    EXCLUDED_SUFFIXES = [
        "_(identifier)",
    ]
    
    if any(link.startswith(prefix) for prefix in EXCLUDED_PREFIXES):
        return False
    
    if any(link.endswith(suffix) for suffix in EXCLUDED_SUFFIXES):
        return False
    
    if "#" in link:
        return False
    
    if not link or link.strip() == "":
        return False
    
    #Normalise to the format used in 'seen'
    if link.replace('_', ' ').replace('./', '') in seen:
        return False
    
    return True



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
        Return empty list on failure.
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
        return []

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
        Return None if no description or error.
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
                if not data['pages']:
                    return None
                wiki_description = data["pages"][0].get("description")
                if wiki_description:
                    wiki_description = page + ": " + wiki_description
                    await asyncio.sleep(0.5)
                    return (page,wiki_description)
                else:
                    return None
    except Exception as e:
        print(f"exception {e}")
        return None

def ranker(sentences: list[str], dic: dict[str]) -> list[str]:
    """
    Rank candidate pages by semantic similarity to the target page.

    Args:
        sentences (list[str]): A list of page descriptions with the target page description at index 0
        dic (dict[str]): A dictionary iwth key:value pair of description:page_title

    Returns:
        list[str]: list of 5 page titles most similar to the target in descending order.
    """
    model = SentenceTransformer("all-MiniLM-L6-v2", local_files_only = True)

    embeddings = model.encode(sentences)
    ranking = {}

    for i in range(1,len(sentences)):
        similarity = cosine_similarity(
            [embeddings[0]],
            [embeddings[i]]
        )
        ranking[dic[sentences[i]]] = similarity[0][0]
    top5 = heapq.nlargest(5, ranking.keys(), key=lambda x: ranking[x])
    return top5

async def main():
    """
    Perform the path finding search.
    """
    sem = asyncio.Semaphore(5)
    texify = lambda t: t.replace(' ', '_')
    start_page = 'Matt Damon'
    target_page = 'Spider-Man'
    async with aiohttp.ClientSession() as session:
        target_description = await get_description(session,target_page,sem)
    seen = {start_page,}
    page_queue = deque([start_page])
    count = 0
    link_counter = 0
    path_s = {start_page:None}

    while page_queue and count <= 6:
        nodes = []
        links_result = [] 
        while page_queue:
            node = page_queue.popleft()
            if node == target_page:
                page_queue.clear()
                nodes.clear()

            else:
                node = texify(node)
                nodes.append(node)
                hash_table = {}

        if nodes:
            async with aiohttp.ClientSession() as session:
                async with asyncio.TaskGroup() as tg:
                    links_coroutine_list = [tg.create_task(get_links(session,node,seen,sem)) for node in nodes]
                for link_coroutine in links_coroutine_list:
                    links_info = link_coroutine.result()
                    page_name,links_list = links_info
                    links_result.extend(links_list) 
                    path_mini = {link:page_name for link in links_list}
                    path_s.update({k:v for k,v in path_mini.items() if k not in path_s})
                async with asyncio.TaskGroup() as tg:
                    decriptions_coroutine_list = [tg.create_task(get_description(session,link,sem)) for link in links_result]
                for description_coroutine in decriptions_coroutine_list:
                    description_info = description_coroutine.result()
                    link_counter += 1
                    if description_info:
                        hash_table[description_info[1]] = description_info[0]
            
            if hash_table:
                descriptions = [target_description[1]] + [desp for desp in hash_table]
                best = ranker(descriptions,hash_table)
                print (best)
                page_queue= deque(best)
                count += 1

    
    if count < 7:
        print("FOUND!!!!!!")
        down = target_page
        path_list = []
        while down in path_s:
            path_list.append(down)
            down = path_s[down]
        path_list.reverse()
        print(path_list)
    else:
        print("NOT FOUND")

    print(f"Process ended with {link_counter} links inspected")


asyncio.run(main())



