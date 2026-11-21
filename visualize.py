"""Draw the network (and optionally highlight a shortest path) with matplotlib.

python -m socialnet.visualize --path Riya Meera   -> results/network_path.png
"""
from __future__ import annotations

import argparse
import math
import os

from .analysis import shortest_path
from .graph import SocialGraph
from .traversal import connected_components

DEFAULT = os.path.join(os.path.dirname(__file__), "..", "data", "sample_network.csv")
RESULTS = os.path.join(os.path.dirname(__file__), "..", "results")


def layout(graph: SocialGraph):
    """Each community gets its own circle; communities sit side by side."""
    pos = {}
    comps = connected_components(graph)
    cx = 0.0
    for comp in comps:
        nodes = sorted(map(str, comp))
        r = max(0.6, 0.35 * len(nodes) ** 0.8) if len(nodes) > 1 else 0
        for i, u in enumerate(nodes):
            ang = 2 * math.pi * i / max(1, len(nodes))
            pos[u] = (cx + r * math.cos(ang), r * math.sin(ang))
        cx += 2 * r + 1.8
    return pos


def draw(graph: SocialGraph, path=None, out=None) -> str:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    pos = layout(graph)
    on_path = set(zip(path, path[1:])) | set(zip(path[1:], path)) if path else set()
    fig, ax = plt.subplots(figsize=(11, 6))
    for a, b in graph.connections():
        hot = (a, b) in on_path
        ax.plot([pos[a][0], pos[b][0]], [pos[a][1], pos[b][1]],
                color="#d62728" if hot else "#b0b7c3", lw=3 if hot else 1, zorder=1)
    for u, (x, y) in pos.items():
        hot = path is not None and u in path
        ax.scatter(x, y, s=700, color="#ffb3b3" if hot else "#9ecae1", edgecolor="#1f3a68", zorder=2)
        ax.text(x, y, u, ha="center", va="center", fontsize=8, zorder=3)
    title = "Social network"
    if path:
        title += f" - shortest path: {' > '.join(path)}"
    ax.set_title(title, fontsize=11); ax.axis("off"); ax.set_aspect("equal")
    fig.tight_layout()
    out = out or os.path.join(RESULTS, "network_path.png" if path else "network.png")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    fig.savefig(out, dpi=150); plt.close(fig)
    return out


def main(argv=None) -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", default=DEFAULT)
    ap.add_argument("--path", nargs=2, metavar=("A", "B"))
    ap.add_argument("--out")
    a = ap.parse_args(argv)
    g = SocialGraph.from_csv(a.file)
    path = shortest_path(g, *a.path) if a.path else None
    print("Saved", draw(g, path, a.out))


if __name__ == "__main__":
    main()
