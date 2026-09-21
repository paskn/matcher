import itertools
import json
import os
import random
import sys
import tempfile
import unittest

# Add the project root to the path so we can import the app module
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import app.main as main
from app.main import InfeasibleGroups, assign_groups, rank_cost, size_bounds


def ranking(order, projects):
    """Build a preference dict from projects listed in order of preference."""
    return {p: order.index(p) + 1 for p in projects}


def skewed_users(projects, n, seed):
    """Users whose rankings favour early projects, as at a real event."""
    rng = random.Random(seed)
    weights = [2 ** -i for i in range(len(projects))]
    users = {}
    for i in range(n):
        pool, w, order = list(projects), list(weights), []
        while pool:
            k = rng.choices(range(len(pool)), w)[0]
            order.append(pool.pop(k))
            w.pop(k)
        users[f'User {i}'] = ranking(order, projects)
    return users


class TestAssignGroups(unittest.TestCase):

    def assert_valid(self, page):
        """Every user in exactly one group, every group within bounds."""
        groups = page['groups']
        members = [u for g in groups.values() for u in g]
        self.assertCountEqual(members, page['users'].keys())
        min_size, max_size = size_bounds(page)
        for project, group in groups.items():
            self.assertGreaterEqual(len(group), min_size, project)
            self.assertLessEqual(len(group), max_size, project)

    def test_skewed_preferences_fill_unpopular_projects(self):
        """The failure seen at the last event: unpopular projects got 1 person."""
        projects = list('ABCDE')
        for seed in range(20):
            page = {'projects': projects, 'users': skewed_users(projects, 28, seed),
                    'min_size': 5, 'max_size': 7}
            assign_groups(page)
            self.assert_valid(page)

    def test_everyone_wants_the_same_project(self):
        projects = ['A', 'B', 'C']
        users = {f'User {i}': ranking(['A', 'B', 'C'], projects) for i in range(12)}
        page = {'projects': projects, 'users': users, 'min_size': 3, 'max_size': 5}
        assign_groups(page)
        self.assert_valid(page)
        self.assertEqual(len(page['groups']['A']), 5)

    def test_first_choices_when_possible(self):
        projects = ['A', 'B']
        users = {
            'User 1': ranking(['A', 'B'], projects),
            'User 2': ranking(['A', 'B'], projects),
            'User 3': ranking(['B', 'A'], projects),
            'User 4': ranking(['B', 'A'], projects),
        }
        page = {'projects': projects, 'users': users, 'min_size': 2, 'max_size': 2}
        assign_groups(page)
        self.assertCountEqual(page['groups']['A'], ['User 1', 'User 2'])
        self.assertCountEqual(page['groups']['B'], ['User 3', 'User 4'])

    def test_solution_is_optimal(self):
        """Compare with brute force over all assignments on a small case."""
        projects = ['A', 'B', 'C']
        users = skewed_users(projects, 7, seed=3)
        page = {'projects': projects, 'users': users, 'min_size': 2, 'max_size': 3}
        assign_groups(page)

        def total_cost(assignment):
            return sum(rank_cost(users[u][p], main.DEFAULT_COSTS) for u, p in assignment.items())

        names = list(users)
        best = None
        for choice in itertools.product(projects, repeat=len(names)):
            sizes = [choice.count(p) for p in projects]
            if min(sizes) < 2 or max(sizes) > 3:
                continue
            cost = total_cost(dict(zip(names, choice)))
            best = cost if best is None else min(best, cost)
        got = {u: p for p, g in page['groups'].items() for u in g}
        self.assertEqual(total_cost(got), best)

    def test_too_few_people_raises(self):
        projects = ['A', 'B', 'C']
        users = {f'User {i}': ranking(projects, projects) for i in range(5)}
        page = {'projects': projects, 'users': users, 'min_size': 2, 'max_size': 4}
        with self.assertRaises(InfeasibleGroups):
            assign_groups(page)
        self.assertNotIn('groups', page)

    def test_too_many_people_raises(self):
        projects = ['A', 'B']
        users = {f'User {i}': ranking(projects, projects) for i in range(9)}
        page = {'projects': projects, 'users': users, 'min_size': 2, 'max_size': 4}
        with self.assertRaises(InfeasibleGroups):
            assign_groups(page)

    def test_exact_bounds(self):
        projects = ['A', 'B', 'C']
        users = skewed_users(projects, 12, seed=1)
        for size in (2, 4):
            n = size * len(projects)
            page = {'projects': projects, 'users': dict(list(users.items())[:n]),
                    'min_size': size, 'max_size': size}
            assign_groups(page)
            self.assert_valid(page)

    def test_user_named_like_project(self):
        projects = ['one', 'two']
        users = {
            'one': ranking(['two', 'one'], projects),
            'two': ranking(['one', 'two'], projects),
        }
        page = {'projects': projects, 'users': users, 'min_size': 1, 'max_size': 1}
        assign_groups(page)
        self.assertEqual(page['groups'], {'one': ['two'], 'two': ['one']})

    def test_missing_preference_counts_as_last(self):
        projects = ['A', 'B']
        users = {'User 1': {'A': 1}, 'User 2': {'A': 1, 'B': 2}, 'User 3': {'B': 1}}
        page = {'projects': projects, 'users': users, 'min_size': 1, 'max_size': 2}
        assign_groups(page)
        self.assert_valid(page)

    def test_no_users(self):
        page = {'projects': ['A', 'B'], 'users': {}, 'min_size': 2, 'max_size': 3}
        assign_groups(page)
        self.assertEqual(page['groups'], {'A': [], 'B': []})

    def test_no_projects(self):
        page = {'projects': [], 'users': {'User 1': {}}, 'min_size': 1, 'max_size': 1}
        assign_groups(page)
        self.assertEqual(page['groups'], {})

    def test_custom_costs_recorded(self):
        projects = ['A', 'B']
        users = skewed_users(projects, 4, seed=0)
        page = {'projects': projects, 'users': users, 'min_size': 2, 'max_size': 2}
        assign_groups(page, [0, 1])
        self.assertIn('[0, 1]', page['algorithm'])


class TestHelpers(unittest.TestCase):

    def test_rank_cost_extends_past_list(self):
        costs = [-100, 50, 100, 200]
        self.assertEqual([rank_cost(r, costs) for r in range(1, 7)],
                         [-100, 50, 100, 200, 300, 400])

    def test_rank_cost_single_value(self):
        self.assertEqual(rank_cost(3, [5]), 5)

    def test_legacy_soft_bounds(self):
        page = {'cap_type': 'soft', 'group_size': 6, 'variation': 2}
        self.assertEqual(size_bounds(page), (4, 8))

    def test_legacy_soft_bounds_clamped(self):
        page = {'cap_type': 'soft', 'group_size': 2, 'variation': -5}
        self.assertEqual(size_bounds(page), (1, 7))

    def test_legacy_hard_bounds(self):
        page = {'cap_type': 'hard', 'group_size': 5, 'variation': 0}
        self.assertEqual(size_bounds(page), (1, 5))


class TestRoutes(unittest.TestCase):

    def setUp(self):
        fd, self.data_file = tempfile.mkstemp(suffix='.json')
        os.close(fd)
        self.old_data_file = main.DATA_FILE
        main.DATA_FILE = self.data_file
        with open(self.data_file, 'w') as f:
            json.dump({'event': {'name': 'Event', 'projects': ['A', 'B'], 'users': {},
                                 'closed': False, 'min_size': 1, 'max_size': 2}}, f)
        main.app.config['TESTING'] = True
        self.client = main.app.test_client()

    def tearDown(self):
        main.DATA_FILE = self.old_data_file
        os.remove(self.data_file)

    def login(self):
        with self.client.session_transaction() as s:
            s['logged_in'] = True

    def vote(self, name, a, b):
        return self.client.post('/event/submit', data={
            'user_name': name, 'preference_A': a, 'preference_B': b})

    def users(self):
        return main.get_data()['event']['users']

    def test_vote_saved(self):
        self.vote('Ann', 1, 2)
        self.assertEqual(self.users(), {'Ann': {'A': 1, 'B': 2}})

    def test_duplicate_name_rejected(self):
        self.vote('Ann', 1, 2)
        self.vote(' ann ', 2, 1)
        self.assertEqual(self.users(), {'Ann': {'A': 1, 'B': 2}})

    def test_tied_ranks_rejected(self):
        self.vote('Ann', 1, 1)
        self.assertEqual(self.users(), {})


if __name__ == '__main__':
    unittest.main()
