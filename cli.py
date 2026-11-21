"""Command-line interface.

Examples
--------
python -m socialnet.cli summary
python -m socialnet.cli bfs Riya
python -m socialnet.cli path Riya Meera
python -m socialnet.cli mutual Riya Samaira
python -m socialnet.cli recommend Riya -k 3
python -m socialnet.cli communities
python -m socialnet.cli influencers
python -m socialnet.cli --file my_network.csv summary
"""
from __future__ import annotations

import argparse
import os
import sys

from .graph import SocialGraph
from . import analysis as an
from .traversal import bfs, dfs, connected_components

DEFAULT = os.path.join(os.path.dirname(__file__), "..", "data", "sample_network.csv")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="socialnet", description="Social network analysis toolkit")
    p.add_argument("--file", default=DEFAULT, help="CSV edge list (user_a,user_b)")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("summary", help="network statistics")
    for name in ("bfs", "dfs"):
        s = sub.add_parser(name, help=f"{name.upper()} traversal order from a user")
        s.add_argument("user")
    s = sub.add_parser("path", help="shortest connection path")
    s.add_argument("a"); s.add_argument("b")
    s = sub.add_parser("mutual", help="mutual connections")
    s.add_argument("a"); s.add_argument("b")
    s = sub.add_parser("recommend", help="people you may know")
    s.add_argument("user"); s.add_argument("-k", type=int, default=5)
    s = sub.add_parser("within", help="users within N hops")
    s.add_argument("user"); s.add_argument("hops", type=int)
    sub.add_parser("communities", help="connected components")
    s = sub.add_parser("influencers", help="most connected users")
    s.add_argument("-k", type=int, default=5)
    return p


def run(args: argparse.Namespace, out=sys.stdout) -> int:
    g = SocialGraph.from_csv(args.file)
    w = lambda *a: print(*a, file=out)
    try:
        if args.cmd == "summary":
            for k, v in an.network_summary(g).items():
                w(f"{k.replace('_', ' ').title():<20}{v}")
        elif args.cmd == "bfs":
            w(" -> ".join(map(str, bfs(g, args.user))))
        elif args.cmd == "dfs":
            w(" -> ".join(map(str, dfs(g, args.user))))
        elif args.cmd == "path":
            path = an.shortest_path(g, args.a, args.b)
            if path is None:
                w(f"{args.a} and {args.b} are not connected.")
            else:
                w(" -> ".join(path))
                w(f"Degrees of separation: {len(path) - 1}")
        elif args.cmd == "mutual":
            m = sorted(an.mutual_connections(g, args.a, args.b), key=str)
            w(f"{len(m)} mutual connection(s): {', '.join(m) if m else '-'}")
        elif args.cmd == "recommend":
            recs = an.recommend_friends(g, args.user, args.k)
            if not recs:
                w("No recommendations available.")
            for u, c in recs:
                w(f"{u:<12}{c} mutual friend(s)")
        elif args.cmd == "within":
            for u, d in sorted(an.reachable_within(g, args.user, args.hops).items(), key=lambda kv: (kv[1], str(kv[0]))):
                w(f"{u:<12}{d} hop(s)")
        elif args.cmd == "communities":
            for i, c in enumerate(connected_components(g), 1):
                w(f"Community {i} ({len(c)}): {', '.join(sorted(map(str, c)))}")
        elif args.cmd == "influencers":
            for u, d in an.most_connected(g, args.k):
                w(f"{u:<12}{d} connections")
    except KeyError as e:
        w(f"Error: {e.args[0]}")
        return 1
    return 0


def main(argv=None) -> int:
    return run(build_parser().parse_args(argv))


if __name__ == "__main__":
    raise SystemExit(main())
