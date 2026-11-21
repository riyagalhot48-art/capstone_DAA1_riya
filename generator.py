"""Synthetic social-network generators (seeded => reproducible)."""
from __future__ import annotations

import random

from .graph import SocialGraph


def random_network(n: int, avg_degree: float = 8.0, seed: int = 42) -> SocialGraph:
    """Random graph with n users and about n*avg_degree/2 edges.

    A random spanning chain is added first so the network is connected,
    which keeps benchmark queries meaningful.
    """
    rng = random.Random(seed)
    g = SocialGraph()
    order = list(range(n))
    rng.shuffle(order)
    for a, b in zip(order, order[1:]):
        g.add_connection(a, b)
    target_edges = int(n * avg_degree / 2)
    while g.num_connections < target_edges:
        a, b = rng.randrange(n), rng.randrange(n)
        if a != b:
            g.add_connection(a, b)
    return g


def scale_free_network(n: int, m: int = 4, seed: int = 42) -> SocialGraph:
    """Barabasi-Albert preferential attachment: a few 'celebrity' hubs with
    very many followers, like real social platforms."""
    if n <= m:
        raise ValueError("n must be greater than m")
    rng = random.Random(seed)
    g = SocialGraph()
    targets = list(range(m))
    repeated: list = []
    for new in range(m, n):
        for t in set(targets):
            g.add_connection(new, t)
        repeated.extend(targets)
        repeated.extend([new] * m)
        targets = [rng.choice(repeated) for _ in range(m)]
    return g
