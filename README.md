# Social Network Connection & Recommendation Analysis

Capstone Project 4 - **Design & Analysis of Algorithms**
Riya (2501010329), K.R Mangalam University (B.Tech CSE, Section E)

A social network analysis toolkit in pure Python. Users are **vertices**, connections are **edges**.
It explores the network with **BFS** and **DFS**, finds **mutual connections**, the **shortest connection path**
between two users, suggests **people you may know**, detects **communities**, and **benchmarks** the algorithms on
networks from 100 to 100 000 users.

| | |
|---|---|
| Language | Python 3.9+ (standard library only; `matplotlib` for charts) |
| Tests | 24 unit tests, including a brute-force oracle cross-check |
| Report | [`docs/REPORT.md`](docs/REPORT.md) - complexity analysis + measured results |

## Features
* **BFS / DFS** traversal (iterative and recursive DFS), connected components (communities)
* **Mutual connections** between any two users
* **Shortest connection path** (BFS) and an optimised **bidirectional BFS**
* **Degrees of separation**, users within *k* hops
* **Friend recommendations** ranked by number of mutual friends
* **Influence metrics**: most-connected users, clustering coefficient, network density
* **Synthetic network generators**: random and scale-free (hub-based)
* **Performance benchmark** with CSV + charts, and a **network visualiser**
* Command-line interface and CSV import/export

## Quick start
```bash
git clone <your-repo-url> && cd social-network-analysis
pip install -r requirements.txt          # only needed for charts
python -m unittest discover -s tests -v  # run the tests

python -m socialnet summary
python -m socialnet bfs Riya
python -m socialnet dfs Riya
python -m socialnet path Riya Meera
python -m socialnet mutual Riya Samaira
python -m socialnet recommend Riya -k 3
python -m socialnet within Riya 2
python -m socialnet communities
python -m socialnet influencers

python -m socialnet --file my_network.csv summary    # your own data (user_a,user_b per line)
python -m socialnet.visualize --path Riya Meera      # results/network_path.png
python -m socialnet.benchmark --quick                # ~10 s;  omit --quick for the full run
```

### Example output
```
$ python -m socialnet path Riya Nicky
Riya -> Samaira -> Nicky
Degrees of separation: 2

$ python -m socialnet mutual Riya Samaira
1 mutual connection(s): Mansi

$ python -m socialnet recommend Riya -k 3
Kavya       1 mutual friend(s)
Nicky       1 mutual friend(s)
Priya       1 mutual friend(s)
```

### Use as a library
```python
from socialnet import SocialGraph, shortest_path, mutual_connections, recommend_friends

g = SocialGraph.from_edges([("A", "B"), ("B", "C"), ("A", "D"), ("D", "C"), ("C", "E")])
shortest_path(g, "A", "E")          # ['A', 'B', 'C', 'E']  (or via D)
mutual_connections(g, "A", "C")     # {'B', 'D'}
recommend_friends(g, "A")           # [('C', 2)]
```

## Complexity summary
| Operation | Time | Space |
|---|---|---|
| BFS / DFS / components | O(V + E) | O(V) |
| Shortest path (BFS) | O(V + E) | O(V) |
| Shortest path (bidirectional) | about O(b^(d/2)) typical | O(V) |
| Mutual connections | O(min(deg a, deg b)) | O(min(deg a, deg b)) |
| Graph storage (adjacency list) | - | O(V + E) |

## Results (100 000 users, 400 000 connections)
| Algorithm | Time |
|---|---|
| Full BFS | about 0.31 s |
| Full DFS | about 0.40 s |
| Shortest path - BFS | about 56 ms / query |
| Shortest path - bidirectional BFS | about 0.35 ms / query (about 160x faster) |

![benchmark](results/benchmark_random.png)

## Project structure
```
socialnet/
  graph.py       SocialGraph (adjacency list, CSV I/O)
  traversal.py   BFS, DFS, components
  analysis.py    mutual friends, shortest path, recommendations, metrics
  generator.py   random + scale-free networks
  benchmark.py   timing across graph sizes -> results/
  visualize.py   network drawing with highlighted path
  cli.py         command-line interface
tests/           unit tests
data/            sample network (CSV)
docs/REPORT.md   analysis report
results/         benchmark CSV and charts
```

## Author
Riya (2501010329)
Faculty mentor: Anvi Aggarwal

## License
MIT
