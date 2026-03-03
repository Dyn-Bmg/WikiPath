"""
This module implements a bounded "Six Degrees of Separation" search between
two Wikipedia pages using a beam search algorithm.
"""
import aiohttp
import asyncio
import api 
from collections import deque
import semantic_ranker 
from sentence_transformers import SentenceTransformer



async def finder(start_page: str, target_page: str) -> tuple[bool,list[str],int]:
    """
    Perform the path finding search with 6 degrees of seperation.

    Args:
        start_page (str): Starting page title
        target_page (str): Target page title

    Returns:
        tuple[bool,list[str],int]: Tuple containing: (check, path_list, lnumber of links checked) 
                                where check is True, path_list exists if a path is found and False, and empty respectively, if not.
    """         
    sem = asyncio.Semaphore(5)
    texify = lambda t: t.replace(' ', '_')
    async with aiohttp.ClientSession() as session:
        target_description = await api.get_description(session,target_page,sem)
    seen = {start_page,}
    page_queue = deque([start_page])
    count = 0
    link_counter = 0
    precursor = {start_page:None} # Dictionary of page and precursor page leading to the page as key value pair

    while page_queue and count <= 6:
        nodes = []
        links_result = []
        description_dict = {} 
        while page_queue:
            node = page_queue.popleft()
            if node == target_page: #Target page found
                # Create path link by looping through page node in precoursor hash table to find its precursor
                path_list = []
                while node in precursor:
                    path_list.append(node)
                    node = precursor[node]
                path_list.reverse() # reverse list to begin -> target format
                return (True, path_list, link_counter)


            else:
                node = texify(node)
                nodes.append(node)

        if nodes:
            async with aiohttp.ClientSession() as session:
                async with asyncio.TaskGroup() as tg:
                    links_coroutine_list = [tg.create_task(api.get_links(session,node,seen,sem)) for node in nodes]
                for link_coroutine in links_coroutine_list:
                    links_info = link_coroutine.result()
                    page_name,links_list = links_info
                    links_result.extend(links_list) 
                    path_mini = {link:page_name for link in links_list}
                    precursor.update({k:v for k,v in path_mini.items() if k not in precursor})
                async with asyncio.TaskGroup() as tg:
                    decriptions_coroutine_list = [tg.create_task(api.get_description(session,link,sem)) for link in links_result]
                for description_coroutine in decriptions_coroutine_list:
                    description_info = description_coroutine.result()
                    link_counter += 1
                    if description_info:
                        description_dict[description_info[1]] = description_info[0]
            
            if description_dict:
                descriptions = [target_description[1]] + [desp for desp in description_dict]
                model = SentenceTransformer("all-MiniLM-L6-v2", local_files_only = True)
                best = semantic_ranker.ranker(model,descriptions,description_dict)
                print (best)
                page_queue= deque(best)
                count += 1

    # Path not found within 6 degrees of seperation
    return (False, [], link_counter)






