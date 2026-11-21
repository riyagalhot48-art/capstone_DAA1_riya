"""Performance analysis of traversal / path algorithms on growing networks.

Run:  python -m socialnet.benchmark            (full run, writes results/)
      python -m socialnet.benchmark --quick    (smaller sizes, ~10 s)
"""
from __future__ import annotations

import argparse
import csv
import os
import random
import statistics
import time
from typing import Callable, Dict, List

from .analysis import bidirectional_shortest_path, shortest_path
from .generator import random_network, scale_free_network
from .traversal import bfs, dfs, dfs_recursive

RESULTS = os.path.join(os.path.dirname(__file__), "..", "results")


def _time(fn: Callable[[], object], repeats: int) -> float:
    """Median wall-clock time in milliseconds."""
    samples = []
    for _ in range(repeats):
        t0 = time.perf_counter()
        fn()
        samples.append((time.perf_counter() - t0) * 1000)
    return statistics.median(samples)


def run(sizes: List[int], repeats: int = 5, avg_degree: float = 8.0, kind: str = "random") -> List[Dict]:
    rows = []
    for n in sizes:
        g = random_network(n, avg_degree) if kind == "random" else scale_free_network(n, m=int(avg_degree // 2))
        rng = random.Random(7)
        users = list(g.users())
        start = users[0]
        pairs = [(rng.choice(users), rng.choice(users)) for _ in range(20)]
        rec = n <= 3000   # recursive DFS would hit Python's recursion limit
        row = {
            "network": kind, "users": n, "connections": g.num_connections,
            "bfs_ms": _time(lambda: bfs(g, start), repeats),
            "dfs_ms": _time(lambda: dfs(g, start), repeats),
            "dfs_recursive_ms": _time(lambda: dfs_recursive(g, start), repeats) if rec else float("nan"),
            "path_bfs_ms": _time(lambda: [shortest_path(g, a, b) for a, b in pairs], repeats) / len(pairs),
            "path_bidir_ms": _time(lambda: [bidirectional_shortest_path(g, a, b) for a, b in pairs], repeats) / len(pairs),
        }
        rows.append(row)
        print(f"[{kind}] n={n:>7}  m={row['connections']:>8}  BFS={row['bfs_ms']:8.2f}ms  "
              f"DFS={row['dfs_ms']:8.2f}ms  path={row['path_bfs_ms']:7.3f}ms  bidir={row['path_bidir_ms']:7.3f}ms")
    return rows


def save_csv(rows: List[Dict], path: str) -> None:
    with open(path, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


def plot(rows: List[Dict], out_dir: str) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    rand = [r for r in rows if r["network"] == "random"]
    x = [r["users"] for r in rand]
    fig, ax = plt.subplots(1, 2, figsize=(12, 4.5))
    ax[0].plot(x, [r["bfs_ms"] for r in rand], "o-", label="BFS")
    ax[0].plot(x, [r["dfs_ms"] for r in rand], "s-", label="DFS (iterative)")
    xr = [r["users"] for r in rand if r["dfs_recursive_ms"] == r["dfs_recursive_ms"]]
    ax[0].plot(xr, [r["dfs_recursive_ms"] for r in rand if r["dfs_recursive_ms"] == r["dfs_recursive_ms"]], "^--", label="DFS (recursive)")
    ax[0].set_xscale("log"); ax[0].set_yscale("log")
    ax[0].set_xlabel("Number of users (V)"); ax[0].set_ylabel("Time (ms, median)")
    ax[0].set_title("Full traversal: BFS vs DFS  (O(V+E))"); ax[0].grid(True, which="both", alpha=.3); ax[0].legend()

    ax[1].plot(x, [r["path_bfs_ms"] for r in rand], "o-", label="BFS shortest path")
    ax[1].plot(x, [r["path_bidir_ms"] for r in rand], "s-", label="Bidirectional BFS")
    ax[1].set_xscale("log"); ax[1].set_yscale("log")
    ax[1].set_xlabel("Number of users (V)"); ax[1].set_ylabel("Time per query (ms, median)")
    ax[1].set_title("Shortest connection path between two users"); ax[1].grid(True, which="both", alpha=.3); ax[1].legend()
    fig.tight_layout()
    fig.savefig(os.path.join(out_dir, "benchmark_random.png"), dpi=150)
    plt.close(fig)

    sf = [r for r in rows if r["network"] == "scale_free"]
    if sf:
        fig, ax = plt.subplots(figsize=(6.5, 4.5))
        for key, lab in (("bfs_ms", "BFS"), ("dfs_ms", "DFS"), ("path_bfs_ms", "Path (BFS)"), ("path_bidir_ms", "Path (bidirectional)")):
            ax.plot([r["users"] for r in sf], [r[key] for r in sf], "o-", label=lab)
        ax.set_xscale("log"); ax.set_yscale("log"); ax.grid(True, which="both", alpha=.3)
        ax.set_xlabel("Number of users (V)"); ax.set_ylabel("Time (ms, median)")
        ax.set_title("Scale-free (hub-based) networks"); ax.legend()
        fig.tight_layout(); fig.savefig(os.path.join(out_dir, "benchmark_scale_free.png"), dpi=150); plt.close(fig)


def main(argv=None) -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--repeats", type=int, default=5)
    a = ap.parse_args(argv)
    sizes = [100, 500, 1000, 5000] if a.quick else [100, 500, 1000, 5000, 10000, 50000, 100000]
    os.makedirs(RESULTS, exist_ok=True)
    rows = run(sizes, a.repeats, kind="random") + run(sizes, a.repeats, kind="scale_free")
    save_csv(rows, os.path.join(RESULTS, "benchmark_results.csv"))
    try:
        plot(rows, RESULTS)
        print(f"\nSaved CSV and charts to {os.path.abspath(RESULTS)}")
    except ImportError:
        print("matplotlib not installed - CSV saved, charts skipped (pip install matplotlib)")


if __name__ == "__main__":
    main()
