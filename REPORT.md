# Analysis Report: Social Network Connection & Recommendation Analysis

**Team Code Divas** - B.Tech CSE, K.R Mangalam University
Riya (2501010329, Team Leader), Samaira (2501010330), Mansi (2501010339), Aashi (2501010343), Nicky (2501010281)

## 1. Problem
Model a social network where **users are vertices** and **connections are edges**, then use **BFS** and **DFS** to
explore connections, find **mutual connections**, determine the **shortest connection path** between two users and
analyse how traversal performance changes with network size.

## 2. Design
| Concern | Choice | Why |
|---|---|---|
| Representation | Adjacency list (`dict[user] -> set[user]`) | O(V+E) space; O(1) average edge insert/lookup; fast neighbour iteration. An adjacency matrix would need O(V^2) space (10^10 cells for 100 000 users). |
| Graph type | Undirected, unweighted, no self-loops or duplicates | A friendship is mutual and all hops cost the same. |
| Edge count | Maintained incrementally | `num_connections` is O(1) (an early version recounted all users and made the generator quadratic - found and fixed during benchmarking). |

## 3. Algorithms and complexity
Let V = users and E = connections.

| Feature | Algorithm | Time | Extra space |
|---|---|---|---|
| Explore connections (nearest first) | BFS (queue) | O(V + E) | O(V) |
| Explore connections (deep first) | DFS - iterative (stack) and recursive | O(V + E) | O(V) |
| Mutual connections of a and b | Set intersection of neighbour sets | O(min(deg a, deg b)) | O(min(deg a, deg b)) |
| Shortest connection path | BFS with parent pointers | O(V + E) | O(V) |
| Shortest path (optimised) | Bidirectional BFS | about O(b^(d/2)) on well-connected graphs, O(V+E) worst case | O(V) |
| Degrees of separation / users within k hops | BFS with depth limit | O(V + E) | O(V) |
| Communities | BFS from every unvisited user | O(V + E) | O(V) |
| Friend recommendation | Friends-of-friends ranked by mutual-friend count | O(sum of deg(f) over friends f) | O(that) |
| Influence | Degree ranking / clustering coefficient | O(V log V) / O(d^2) | O(V) |

**Why BFS gives the shortest path:** BFS visits users in non-decreasing distance order, so the first time it reaches the
target it has used the fewest possible hops. DFS offers no such guarantee, so it is used for exploration and
reachability, not for shortest paths.

**Why DFS is iterative by default:** Python's recursion limit (about 1000) makes the recursive version crash on long
chains (a 50 000-user chain is covered by a unit test). The iterative version has the same O(V+E) cost and no depth limit.

## 4. Experimental setup
* Synthetic networks, fixed random seeds (reproducible): `random` (about 8 connections per user, connected) and
  `scale_free` (preferential attachment with hubs, like real platforms).
* Sizes: 100 to 100 000 users. Times are the **median** of 3 runs; path times are averaged over 20 random user pairs.
* Reproduce with `python -m socialnet.benchmark`. Machine-dependent absolute times; the *trends* are what matter.

## 5. Results

### 5.1 Random network
| Users (V) | Connections (E) | BFS (ms) | DFS iter. (ms) | Path: BFS (ms/query) | Path: bidirectional (ms/query) | Speed-up |
|---:|---:|---:|---:|---:|---:|---:|
| 100 | 400 | 0.06 | 0.08 | 0.010 | 0.008 | 1x |
| 500 | 2,000 | 0.38 | 0.49 | 0.083 | 0.022 | 4x |
| 1,000 | 4,000 | 0.77 | 1.00 | 0.113 | 0.029 | 4x |
| 5,000 | 20,000 | 6.55 | 7.21 | 0.948 | 0.069 | 14x |
| 10,000 | 40,000 | 10.79 | 11.69 | 1.819 | 0.085 | 21x |
| 50,000 | 200,000 | 116.06 | 126.01 | 18.457 | 0.265 | 70x |
| 100,000 | 400,000 | 311.17 | 402.24 | 56.109 | 0.350 | 160x |

![random](../results/benchmark_random.png)

### 5.2 Scale-free (hub) network
| Users (V) | Connections (E) | BFS (ms) | DFS iter. (ms) | Path: BFS (ms/query) | Path: bidirectional (ms/query) | Speed-up |
|---:|---:|---:|---:|---:|---:|---:|
| 100 | 367 | 0.06 | 0.06 | 0.007 | 0.006 | 1x |
| 500 | 1,956 | 0.26 | 0.33 | 0.034 | 0.013 | 3x |
| 1,000 | 3,949 | 0.53 | 0.69 | 0.078 | 0.018 | 4x |
| 5,000 | 19,930 | 3.04 | 3.88 | 0.611 | 0.051 | 12x |
| 10,000 | 39,919 | 6.49 | 8.30 | 1.046 | 0.067 | 16x |
| 50,000 | 199,883 | 60.67 | 73.92 | 7.619 | 0.195 | 39x |
| 100,000 | 399,870 | 152.37 | 184.13 | 18.039 | 0.206 | 88x |

![scale-free](../results/benchmark_scale_free.png)

## 6. Discussion
1. **BFS and DFS scale linearly.** Going from 10 000 to 100 000 users (10x) multiplies full-traversal time by roughly
   10-30x on the random network, which is consistent with O(V+E) (the extra factor comes from cache effects on larger
   data). On the log-log chart both lines are parallel straight lines.
2. **BFS and DFS cost the same asymptotically**; in practice they differ by only a few percent. Choose by purpose:
   BFS for distance-based questions, DFS for exhaustive exploration.
3. **Bidirectional BFS is dramatically faster for path queries** - at 100 000 users it is about 160x faster than
   one-sided BFS on the random network and about 90x on the scale-free network, because two small searches replace one
   large one. This matches the O(b^(d/2)) versus O(b^d) argument.
4. **Hubs make path queries cheaper.** At equal size the scale-free network answered path queries faster than the random
   one (18 ms vs 56 ms for one-sided BFS at 100 000 users), consistent with hubs creating short cuts between users.
5. **Correctness.** Shortest paths from both BFS variants were checked against an independent Bellman-Ford-style oracle
   on 25 random graphs (up to 200 user pairs each) - all distances match.

## 7. Limitations and future work
* Graph is held in memory; very large networks would need a disk-backed or distributed store.
* Edges are unweighted; closeness strength (e.g. message frequency) could be added with Dijkstra.
* Recommendations use only mutual-friend counts; Jaccard similarity, shared interests or PageRank would improve quality.
* Python's constant factors are high; the same design in C++/Java would be faster in absolute terms.
