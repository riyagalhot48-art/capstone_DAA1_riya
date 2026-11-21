"""Undirected social-network graph stored as an adjacency list.

Users are vertices and friendships are edges.  Using a dict of sets gives
O(1) average-time edge insertion / lookup and O(V + E) space.
"""
from __future__ import annotations

import csv
from typing import Dict, Hashable, Iterable, Iterator, Set, Tuple

User = Hashable


class SocialGraph:
    """Undirected, unweighted graph (no self-loops, no parallel edges)."""

    def __init__(self) -> None:
        self._adj: Dict[User, Set[User]] = {}
        self._m = 0                      # edge count, kept in O(1)

    # ------------------------------------------------------------------ build
    def add_user(self, user: User) -> None:
        self._adj.setdefault(user, set())

    def add_connection(self, a: User, b: User) -> None:
        if a == b:
            raise ValueError(f"A user cannot be connected to themselves: {a!r}")
        self.add_user(a)
        self.add_user(b)
        if b not in self._adj[a]:
            self._adj[a].add(b)
            self._adj[b].add(a)
            self._m += 1

    def remove_connection(self, a: User, b: User) -> None:
        self._require(a)
        self._require(b)
        if b in self._adj[a]:
            self._adj[a].discard(b)
            self._adj[b].discard(a)
            self._m -= 1

    # ---------------------------------------------------------------- queries
    def has_user(self, user: User) -> bool:
        return user in self._adj

    def has_connection(self, a: User, b: User) -> bool:
        return a in self._adj and b in self._adj[a]

    def neighbors(self, user: User) -> Set[User]:
        self._require(user)
        return self._adj[user]

    def degree(self, user: User) -> int:
        return len(self.neighbors(user))

    def users(self) -> Iterator[User]:
        return iter(self._adj)

    def connections(self) -> Iterator[Tuple[User, User]]:
        """Yield every edge exactly once."""
        seen: Set[User] = set()
        for u, nbrs in self._adj.items():
            for v in nbrs:
                if v not in seen:
                    yield (u, v)
            seen.add(u)

    @property
    def num_users(self) -> int:
        return len(self._adj)

    @property
    def num_connections(self) -> int:
        return self._m

    def __contains__(self, user: User) -> bool:
        return self.has_user(user)

    def __len__(self) -> int:
        return self.num_users

    def __repr__(self) -> str:
        return f"SocialGraph(users={self.num_users}, connections={self.num_connections})"

    # ------------------------------------------------------------------- I/O
    @classmethod
    def from_edges(cls, edges: Iterable[Tuple[User, User]]) -> "SocialGraph":
        g = cls()
        for a, b in edges:
            g.add_connection(a, b)
        return g

    @classmethod
    def from_csv(cls, path: str) -> "SocialGraph":
        """Load a CSV with two columns: user_a,user_b (header optional).

        A single-column row declares an isolated user.
        """
        g = cls()
        with open(path, newline="", encoding="utf-8") as fh:
            for i, row in enumerate(csv.reader(fh)):
                row = [c.strip() for c in row if c.strip()]
                if not row or (i == 0 and row[0].lower() in {"user_a", "source", "from"}):
                    continue
                if len(row) == 1:
                    g.add_user(row[0])
                else:
                    g.add_connection(row[0], row[1])
        return g

    def to_csv(self, path: str) -> None:
        with open(path, "w", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh)
            w.writerow(["user_a", "user_b"])
            for a, b in self.connections():
                w.writerow([a, b])

    # --------------------------------------------------------------- helpers
    def _require(self, user: User) -> None:
        if user not in self._adj:
            raise KeyError(f"Unknown user: {user!r}")
