"""Social-network analysis built on BFS: mutual friends, shortest path,
degrees of separation, friend recommendations and influence metrics."""
from __future__ import annotations

from collections import deque
from typing import Dict, List, Optional, Set, Tuple

from .graph import SocialGraph, User
from .traversal import bfs_levels, connected_components


def mutual_connections(graph: SocialGraph, a: User, b: User) -> Set[User]:
    """Users connected to both *a* and *b* (set intersection)."""
    return graph.neighbors(a) & graph.neighbors(b)


def shortest_path(graph: SocialGraph, source: User, target: User) -> Optional[List[User]]:
    """Shortest connection path via BFS (unweighted => BFS is optimal).

    Returns the users from *source* to *target*, or None if not connected.
    O(V + E).
    """
    graph._require(source)
    graph._require(target)
    if source == target:
        return [source]
    parent: Dict[User, User] = {source: source}
    queue = deque([source])
    while queue:
        u = queue.popleft()
        for v in graph.neighbors(u):
            if v not in parent:
                parent[v] = u
                if v == target:
                    return _rebuild(parent, source, target)
                queue.append(v)
    return None


def bidirectional_shortest_path(graph: SocialGraph, source: User, target: User) -> Optional[List[User]]:
    """Bidirectional BFS: search from both ends and meet in the middle.

    Explores about O(b^(d/2)) nodes instead of O(b^d) on well-connected graphs.
    Always returns a shortest path (levels are expanded completely).
    """
    graph._require(source)
    graph._require(target)
    if source == target:
        return [source]
    pf: Dict[User, Optional[User]] = {source: None}
    pb: Dict[User, Optional[User]] = {target: None}
    qf, qb = deque([source]), deque([target])

    def expand(queue, mine, other) -> Optional[User]:
        meet = None
        for _ in range(len(queue)):               # exactly one BFS level
            u = queue.popleft()
            for v in graph.neighbors(u):
                if v not in mine:
                    mine[v] = u
                    queue.append(v)
                    if v in other and meet is None:
                        meet = v
        return meet

    while qf and qb:
        meet = expand(qf, pf, pb) if len(qf) <= len(qb) else expand(qb, pb, pf)
        if meet is not None:
            half1, node = [], meet
            while node is not None:
                half1.append(node)
                node = pf[node]
            half1.reverse()
            node = pb[meet]
            while node is not None:
                half1.append(node)
                node = pb[node]
            return half1
    return None


def degrees_of_separation(graph: SocialGraph, a: User, b: User) -> Optional[int]:
    path = shortest_path(graph, a, b)
    return None if path is None else len(path) - 1


def recommend_friends(graph: SocialGraph, user: User, k: int = 5) -> List[Tuple[User, int]]:
    """"People you may know": friends-of-friends ranked by mutual friends.

    Returns up to *k* tuples (candidate, number_of_mutual_friends).
    Ties are broken alphabetically so the output is deterministic.
    """
    friends = graph.neighbors(user)
    score: Dict[User, int] = {}
    for f in friends:
        for fof in graph.neighbors(f):
            if fof != user and fof not in friends:
                score[fof] = score.get(fof, 0) + 1
    ranked = sorted(score.items(), key=lambda kv: (-kv[1], str(kv[0])))
    return ranked[:k]


def reachable_within(graph: SocialGraph, user: User, hops: int) -> Dict[User, int]:
    """Everyone within *hops* connections (excluding the user)."""
    d = bfs_levels(graph, user, max_depth=hops)
    d.pop(user, None)
    return d


def most_connected(graph: SocialGraph, k: int = 5) -> List[Tuple[User, int]]:
    """Top-k users by degree (a simple influence measure)."""
    return sorted(((u, graph.degree(u)) for u in graph.users()),
                  key=lambda kv: (-kv[1], str(kv[0])))[:k]


def clustering_coefficient(graph: SocialGraph, user: User) -> float:
    """Fraction of a user's friends who are also friends with each other."""
    nbrs = list(graph.neighbors(user))
    d = len(nbrs)
    if d < 2:
        return 0.0
    links = sum(1 for i in range(d) for j in range(i + 1, d)
                if graph.has_connection(nbrs[i], nbrs[j]))
    return 2 * links / (d * (d - 1))


def network_summary(graph: SocialGraph) -> Dict[str, float]:
    comps = connected_components(graph)
    n, m = graph.num_users, graph.num_connections
    return {
        "users": n,
        "connections": m,
        "average_degree": round(2 * m / n, 2) if n else 0.0,
        "density": round(2 * m / (n * (n - 1)), 4) if n > 1 else 0.0,
        "communities": len(comps),
        "largest_community": len(comps[0]) if comps else 0,
    }


def _rebuild(parent: Dict[User, User], source: User, target: User) -> List[User]:
    path = [target]
    while path[-1] != source:
        path.append(parent[path[-1]])
    path.reverse()
    return path
