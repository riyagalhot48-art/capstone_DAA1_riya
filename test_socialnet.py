import io
import itertools
import os
import random
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from socialnet import (SocialGraph, bfs, dfs, dfs_recursive, bfs_levels, connected_components,
                       mutual_connections, shortest_path, bidirectional_shortest_path,
                       degrees_of_separation, recommend_friends, reachable_within, most_connected,
                       clustering_coefficient, network_summary, random_network, scale_free_network)
from socialnet.cli import build_parser, run

SAMPLE = os.path.join(os.path.dirname(__file__), "..", "data", "sample_network.csv")


def line_graph(n):
    return SocialGraph.from_edges((i, i + 1) for i in range(n - 1))


def brute_distance(g, s, t):
    """Independent oracle: Bellman-Ford style relaxation, not BFS."""
    INF = float("inf")
    d = {u: INF for u in g.users()}
    d[s] = 0
    for _ in range(g.num_users):
        changed = False
        for a, b in g.connections():
            if d[a] + 1 < d[b]:
                d[b] = d[a] + 1; changed = True
            if d[b] + 1 < d[a]:
                d[a] = d[b] + 1; changed = True
        if not changed:
            break
    return None if d[t] == INF else d[t]


class GraphTests(unittest.TestCase):
    def test_add_and_count(self):
        g = SocialGraph()
        g.add_connection("a", "b"); g.add_connection("b", "a"); g.add_connection("b", "c")
        self.assertEqual((g.num_users, g.num_connections), (3, 2))
        self.assertTrue(g.has_connection("a", "b") and g.has_connection("b", "a"))
        self.assertEqual(sorted(map(sorted, g.connections())), [["a", "b"], ["b", "c"]])

    def test_self_loop_rejected(self):
        with self.assertRaises(ValueError):
            SocialGraph().add_connection("a", "a")

    def test_unknown_user(self):
        with self.assertRaises(KeyError):
            SocialGraph().neighbors("ghost")

    def test_remove_connection(self):
        g = SocialGraph.from_edges([(1, 2), (2, 3)])
        g.remove_connection(1, 2)
        self.assertFalse(g.has_connection(1, 2)); self.assertEqual(g.num_connections, 1)

    def test_csv_roundtrip(self):
        g = SocialGraph.from_csv(SAMPLE)
        self.assertIn("Zoya", g); self.assertEqual(g.degree("Zoya"), 0)
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "x.csv"); g.to_csv(p)
            h = SocialGraph.from_csv(p)
        self.assertEqual(h.num_connections, g.num_connections)


class TraversalTests(unittest.TestCase):
    def setUp(self):
        #   1 - 2 - 4
        #   |   |
        #   3 - 5     6 (separate)
        self.g = SocialGraph.from_edges([(1, 2), (1, 3), (2, 4), (2, 5), (3, 5)])
        self.g.add_user(6)

    def test_bfs_visits_component_nearest_first(self):
        order = bfs(self.g, 1)
        self.assertEqual(set(order), {1, 2, 3, 4, 5})
        d = bfs_levels(self.g, 1)
        self.assertEqual([d[u] for u in order], sorted(d[u] for u in order))  # non-decreasing depth

    def test_dfs_variants_agree_on_reachable_set(self):
        self.assertEqual(set(dfs(self.g, 1)), set(dfs_recursive(self.g, 1)))
        self.assertEqual(set(dfs(self.g, 1)), set(bfs(self.g, 1)))
        self.assertEqual(len(dfs(self.g, 1)), len(set(dfs(self.g, 1))))   # no duplicates

    def test_dfs_goes_deep_before_wide(self):
        g = SocialGraph.from_edges([("r", "a"), ("r", "b"), ("a", "a1"), ("a", "a2")])
        order = dfs_recursive(g, "r")
        first = order[1]
        other = "b" if first == "a" else "a"
        if first == "a":
            self.assertLess(order.index("a1"), order.index(other))

    def test_iterative_dfs_handles_deep_graph(self):
        g = line_graph(50_000)               # would overflow recursion
        self.assertEqual(len(dfs(g, 0)), 50_000)

    def test_components(self):
        comps = connected_components(self.g)
        self.assertEqual([len(c) for c in comps], [5, 1])

    def test_start_must_exist(self):
        with self.assertRaises(KeyError):
            bfs(self.g, 99)


class AnalysisTests(unittest.TestCase):
    def setUp(self):
        self.g = SocialGraph.from_csv(SAMPLE)

    def test_mutual(self):
        self.assertEqual(mutual_connections(self.g, "Riya", "Samaira"), {"Mansi"})
        self.assertEqual(mutual_connections(self.g, "Riya", "Zoya"), set())

    def test_shortest_path_basic(self):
        p = shortest_path(self.g, "Riya", "Nicky")
        self.assertEqual(p, ["Riya", "Samaira", "Nicky"])
        self.assertEqual(degrees_of_separation(self.g, "Riya", "Nicky"), 2)
        self.assertEqual(shortest_path(self.g, "Riya", "Riya"), ["Riya"])

    def test_disconnected_returns_none(self):
        self.assertIsNone(shortest_path(self.g, "Riya", "Zoya"))
        self.assertIsNone(bidirectional_shortest_path(self.g, "Riya", "Zoya"))
        self.assertIsNone(degrees_of_separation(self.g, "Riya", "Zoya"))

    def test_path_is_valid_walk(self):
        p = shortest_path(self.g, "Riya", "Meera")
        for a, b in zip(p, p[1:]):
            self.assertTrue(self.g.has_connection(a, b))

    def test_matches_independent_oracle_on_random_graphs(self):
        rng = random.Random(1)
        for seed in range(25):
            n = rng.randint(5, 40)
            g = SocialGraph()
            for u in range(n):
                g.add_user(u)
            for _ in range(rng.randint(0, 2 * n)):
                a, b = rng.randrange(n), rng.randrange(n)
                if a != b:
                    g.add_connection(a, b)
            for s, t in itertools.islice(itertools.product(range(n), repeat=2), 0, 200):
                want = brute_distance(g, s, t)
                p1 = shortest_path(g, s, t)
                p2 = bidirectional_shortest_path(g, s, t)
                got1 = None if p1 is None else len(p1) - 1
                got2 = None if p2 is None else len(p2) - 1
                self.assertEqual(got1, want, (seed, s, t))
                self.assertEqual(got2, want, (seed, s, t))
                if p2:
                    self.assertEqual((p2[0], p2[-1]), (s, t))
                    for a, b in zip(p2, p2[1:]):
                        self.assertTrue(g.has_connection(a, b))

    def test_recommendations(self):
        recs = dict(recommend_friends(self.g, "Riya", k=10))
        self.assertNotIn("Riya", recs)
        for friend in self.g.neighbors("Riya"):
            self.assertNotIn(friend, recs)
        self.assertEqual(recs["Nicky"], 1)          # via Samaira
        self.assertEqual(recs["Priya"], 1)          # via Aashi
        # candidate sharing two friends outranks one sharing a single friend
        g = SocialGraph.from_edges([("u", "a"), ("u", "b"), ("a", "x"), ("b", "x"), ("a", "y")])
        self.assertEqual(recommend_friends(g, "u"), [("x", 2), ("y", 1)])

    def test_reachable_within(self):
        r = reachable_within(self.g, "Riya", 1)
        self.assertEqual(set(r), {"Samaira", "Mansi", "Aashi"})
        self.assertTrue(all(v == 1 for v in r.values()))

    def test_influence_and_clustering(self):
        top = most_connected(self.g, 1)[0]
        self.assertEqual(top[1], max(self.g.degree(u) for u in self.g.users()))
        tri = SocialGraph.from_edges([(1, 2), (2, 3), (1, 3)])
        self.assertEqual(clustering_coefficient(tri, 1), 1.0)
        star = SocialGraph.from_edges([(0, 1), (0, 2), (0, 3)])
        self.assertEqual(clustering_coefficient(star, 0), 0.0)

    def test_summary(self):
        s = network_summary(self.g)
        self.assertEqual((s["users"], s["connections"], s["communities"]), (16, 21, 2))


class GeneratorTests(unittest.TestCase):
    def test_random_is_connected_and_reproducible(self):
        a, b = random_network(300, seed=5), random_network(300, seed=5)
        self.assertEqual(sorted(map(sorted, a.connections())), sorted(map(sorted, b.connections())))
        self.assertEqual(len(connected_components(a)), 1)
        self.assertEqual(a.num_connections, 1200)

    def test_scale_free_has_hubs(self):
        g = scale_free_network(2000, m=4)
        degs = sorted((g.degree(u) for u in g.users()), reverse=True)
        self.assertGreater(degs[0], 5 * (sum(degs) / len(degs)))


class CLITests(unittest.TestCase):
    def call(self, *argv):
        out = io.StringIO()
        code = run(build_parser().parse_args(argv), out)
        return code, out.getvalue()

    def test_commands(self):
        for argv in (["summary"], ["bfs", "Riya"], ["dfs", "Riya"], ["path", "Riya", "Nicky"],
                     ["mutual", "Riya", "Samaira"], ["recommend", "Riya"], ["within", "Riya", "2"],
                     ["communities"], ["influencers"]):
            code, text = self.call(*argv)
            self.assertEqual(code, 0, argv); self.assertTrue(text.strip())

    def test_unknown_user_and_disconnected(self):
        code, text = self.call("path", "Riya", "Nobody")
        self.assertEqual(code, 1); self.assertIn("Unknown user", text)
        code, text = self.call("path", "Riya", "Zoya")
        self.assertIn("not connected", text)


if __name__ == "__main__":
    unittest.main()
