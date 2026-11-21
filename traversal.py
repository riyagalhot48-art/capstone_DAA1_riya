"""Graph traversal algorithms: BFS and DFS.

Both run in O(V + E) time and O(V) extra space on an adjacency list.
"""
from __future__ import annotations

from collections import deque
from typing import Dict, List, Optional, Set

from .graph import SocialGraph, User


def bfs(graph: SocialGraph, start: User) -> List[User]:
    """Breadth-first visiting order from *start* (nearest users first)."""
    graph._require(start)
    visited: Set[User] = {start}
    order: List[User] = []
    queue = deque([start])
    while queue:
        u = queue.popleft()
        order.append(u)
        for v in graph.neighbors(u):
            if v not in visited:
                visited.add(v)
                queue.append(v)
    return order


def bfs_levels(graph: SocialGraph, start: User, max_depth: Optional[int] = None) -> Dict[User, int]:
    """Distance (number of hops) from *start* to every reachable user."""
    graph._require(start)
    dist: Dict[User, int] = {start: 0}
    queue = deque([start])
    while queue:
        u = queue.popleft()
        if max_depth is not None and dist[u] >= max_depth:
            continue
        for v in graph.neighbors(u):
            if v not in dist:
                dist[v] = dist[u] + 1
                queue.append(v)
    return dist


def dfs(graph: SocialGraph, start: User) -> List[User]:
    """Iterative depth-first visiting order (safe for very deep graphs)."""
    graph._require(start)
    visited: Set[User] = set()
    order: List[User] = []
    stack = [start]
    while stack:
        u = stack.pop()
        if u in visited:
            continue
        visited.add(u)
        order.append(u)
        for v in graph.neighbors(u):
            if v not in visited:
                stack.append(v)
    return order


def dfs_recursive(graph: SocialGraph, start: User) -> List[User]:
    """Textbook recursive DFS (limited by Python's recursion depth)."""
    graph._require(start)
    visited: Set[User] = set()
    order: List[User] = []

    def visit(u: User) -> None:
        visited.add(u)
        order.append(u)
        for v in graph.neighbors(u):
            if v not in visited:
                visit(v)

    visit(start)
    return order


def connected_components(graph: SocialGraph) -> List[Set[User]]:
    """All communities (connected components), largest first."""
    seen: Set[User] = set()
    comps: List[Set[User]] = []
    for u in graph.users():
        if u not in seen:
            comp = set(bfs(graph, u))
            seen |= comp
            comps.append(comp)
    comps.sort(key=len, reverse=True)
    return comps
