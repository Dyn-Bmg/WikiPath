# 🔗 WikiPath

> Navigate from any Wikipedia page to any other in six clicks or fewer.

WikiPath is a Python tool that finds link paths between any two Wikipedia articles using **async BFS** with a **semantic beam search** — prioritising the most promising links at each step using sentence embeddings.

---

## How It Works

WikiPath explores Wikipedia's link graph in breadth-first layers, but instead of blindly expanding every link, it ranks candidate pages at each hop using **cosine similarity** against the target page's description. Only the top 5 semantically closest pages are carried forward.

```
Start Page → [BFS Layer] → Semantic Ranking → Top 5 → [BFS Layer] → ... → Target Page
```

**Stack:**
- [`aiohttp`](https://docs.aiohttp.org/) — async HTTP requests to the Wikimedia REST API
- [`BeautifulSoup`](https://www.crummy.com/software/BeautifulSoup/) — HTML parsing for outgoing wiki links
- [`sentence-transformers`](https://www.sbert.net/) — semantic embeddings (`all-MiniLM-L6-v2`)
- [`scikit-learn`](https://scikit-learn.org/) — cosine similarity scoring

---

## Getting Started

### Prerequisites
- Python 3.11+
- The `all-MiniLM-L6-v2` model cached locally (see below)


### Download the Embedding Model
```python
from sentence_transformers import SentenceTransformer
SentenceTransformer("all-MiniLM-L6-v2")  # run once to download and cache
```

### Run
```bash
python main.py
```
```
Enter start page title: Tems
Enter end page title: Spider-Man
```

**Example output:**
```
PATH FOUND!!!!!!
Tems-> Black Panther: Wakanda Forever (soundtrack)-> Iron Man-> Spider-Man
Check ended with a total of 6534 checked
```

---

## Project Structure

| Module | Responsibility |
|---|---|
| `main.py` | Entry point — handles user I/O |
| `path_finder.py` | Orchestrates BFS layers, manages precursor map for path reconstruction |
| `api.py` | Fetches page HTML and short descriptions from the Wikimedia REST API |
| `link_validator.py` | Strips non-article namespaces (Category, File, Template, etc.) and visited pages |
| `semantic_ranker.py` | Encodes descriptions and returns the top 5 by cosine similarity to the target |

---

## Constraints

| Parameter | Value |
|---|---|
| Max depth | 6 hops |
| Beam width | 5 pages per layer |
| Max concurrent requests | 5 (via `asyncio.Semaphore`) |
| Rate limiting | 1s after link fetches, 0.5s after description fetches |

---

## Limitations

- Pages without short descriptions are skipped during ranking, which can affect path quality
- Beam search is a heuristic — it can miss valid short paths that don't score well semantically


---

## License

MIT
