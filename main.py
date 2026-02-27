from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import aiohttp
import asyncio
from bs4 import BeautifulSoup
import heapq
from collections import deque

def is_valid_article(link: str,seen) -> bool:
    
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
    
    if link.replace('_', ' ').replace('./', '') in seen:
        return False
    
    return True



async def func(session,page,seen,sem):
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
                links = [link.replace('_', ' ').replace('./', '') for link in links if is_valid_article(link,seen)]
                seen.update({link for link in links})
                await asyncio.sleep(1)
                page = page.replace('_', ' ').replace('./', '')
                return page,links
    except Exception as e:
        print(f"exception {e}")
        return []

async def get_description(session,page,sem):
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

def checker(sentences,dic):
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
    sem = asyncio.Semaphore(5)
    texify = lambda t: t.replace(' ', '_')
    begin = 'Matt Damon'
    end = 'Spider-Man'
    async with aiohttp.ClientSession() as session:
        ending = await get_description(session,end,sem)
    seen = {begin,}
    ans = [ending[1]]
    queue = deque([begin])
    count = 0
    l_count = 0
    path_s = {begin:None}

    while queue and count <= 6:
        nodes = []
        links_result = []
        while queue:
            node = queue.popleft()
            if node == end:
                queue.clear()
                nodes.clear()

            else:
                node = texify(node)
                nodes.append(node)
                hash_table = {}

        if nodes:
            async with aiohttp.ClientSession() as session:
                async with asyncio.TaskGroup() as tg:
                    p_links = [tg.create_task(func(session,node,seen,sem)) for node in nodes]
                for result in p_links:
                    page_info = result.result()
                    page,links_list = page_info
                    links_result.extend(links_list) 
                    path_mini = {link:page for link in links_list}
                    path_s.update({k:v for k,v in path_mini.items() if k not in path_s})
                async with asyncio.TaskGroup() as tg:
                    results = [tg.create_task(get_description(session,link,sem)) for link in links_result]
                for result in results:
                    info = result.result()
                    l_count += 1
                    if info:
                        page,descp = info
                        hash_table[descp] = page
            
            if hash_table:
                descriptions = ans + [desp for desp in hash_table]
                best = checker(descriptions,hash_table)
                print (best)
                queue= deque(best)
                count += 1

    
    if count < 7:
        print("FOUND!!!!!!")
        down = end
        path_link = []
        while down in path_s:
            path_link.append(down)
            down = path_s[down]
        path_link.reverse()
        print(path_link)
    else:
        print("NOT FOUND")
    print(f"Process ended with {l_count} links inspected")

asyncio.run(main())



