import unittest
import sys
import os

# Add the project root to the path so we can import the app module
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.main import assign_groups

class TestAssignGroups(unittest.TestCase):
    """
    Test suite for the assign_groups function.
    """

    def test_even_distribution(self):
        """
        Tests if assign_groups can reliably produce equal size groups.
        5 projects, 50 users should result in 10 users per group.
        """
        projects = [f'Project {i}' for i in range(1, 6)]
        users = {f'User {i}': {p: (i + j) % 5 + 1 for j, p in enumerate(projects)} for i in range(50)}
        page = {
            'projects': projects,
            'users': users,
            'cap_type': 'soft',
            'group_size': 10,
            'variation': 0
        }
        assign_groups(page)
        groups = page['groups']

        for project in projects:
            self.assertEqual(len(groups[project]), 10)

    def test_all_users_assigned(self):
        """
        Tests that assign_groups assigns every user to a group.
        No user should be left unassigned.
        """
        projects = [f'Project {i}' for i in range(1, 4)]
        users = {f'User {i}': {p: (i + j) % 3 + 1 for j, p in enumerate(projects)} for i in range(23)}
        page = {
            'projects': projects,
            'users': users,
            'cap_type': 'soft',
            'group_size': 8,
            'variation': 2
        }
        assign_groups(page)
        groups = page['groups']

        assigned_users = set()
        for project_users in groups.values():
            for user in project_users:
                assigned_users.add(user)
        
        self.assertEqual(len(assigned_users), len(users))
        self.assertEqual(set(users.keys()), assigned_users)

    def test_no_users(self):
        """
        Tests behavior with no users.
        """
        projects = ['Project A', 'Project B']
        users = {}
        page = {
            'projects': projects,
            'users': users,
        }
        assign_groups(page)
        groups = page['groups']
        self.assertEqual(groups, {'Project A': [], 'Project B': []})

    def test_no_projects(self):
        """
        Tests behavior with no projects.
        """
        projects = []
        users = {'User 1': {}}
        page = {
            'projects': projects,
            'users': users,
        }
        assign_groups(page)
        groups = page['groups']
        self.assertEqual(groups, {})
        # Also check that no users were assigned, as there are no groups.
        assigned_users = set()
        for project_users in groups.values():
            for user in project_users:
                assigned_users.add(user)
        self.assertEqual(len(assigned_users), 0)

    def test_single_user_single_project(self):
        """
        Tests with a single user and a single project.
        """
        projects = ['Project A']
        users = {'User 1': {'Project A': 1}}
        page = {
            'projects': projects,
            'users': users,
        }
        assign_groups(page)
        groups = page['groups']
        self.assertEqual(groups, {'Project A': ['User 1']})

    def test_single_user_multiple_projects(self):
        """
        Tests with a single user and multiple projects.
        """
        projects = ['Project A', 'Project B']
        users = {'User 1': {'Project A': 1, 'Project B': 2}}
        page = {
            'projects': projects,
            'users': users,
        }
        assign_groups(page)
        groups = page['groups']
        self.assertEqual(groups['Project A'], ['User 1'])
        self.assertEqual(groups['Project B'], [])

    def test_multiple_users_single_project(self):
        """
        Tests with multiple users and a single project.
        """
        projects = ['Project A']
        users = {
            'User 1': {'Project A': 1},
            'User 2': {'Project A': 1}
        }
        page = {
            'projects': projects,
            'users': users,
        }
        assign_groups(page)
        groups = page['groups']
        self.assertEqual(len(groups['Project A']), 2)
        self.assertIn('User 1', groups['Project A'])
        self.assertIn('User 2', groups['Project A'])

    def test_hard_cap_impossible_constraints(self):
        """
        Tests hard cap where not all users can be assigned.
        """
        projects = ['Project A']
        users = {
            'User 1': {'Project A': 1},
            'User 2': {'Project A': 1},
            'User 3': {'Project A': 1},
        }
        page = {
            'projects': projects,
            'users': users,
            'cap_type': 'hard',
            'group_size': 2,
        }
        assign_groups(page)
        groups = page['groups']
        
        assigned_users = set()
        for project_users in groups.values():
            for user in project_users:
                assigned_users.add(user)
        
        self.assertEqual(len(groups['Project A']), 2)
        self.assertEqual(len(assigned_users), 2)
        self.assertLess(len(assigned_users), len(users))

    def test_hard_cap_exact_capacity_match(self):
        """
        Tests hard cap with an exact capacity match.
        """
        projects = ['Project A', 'Project B']
        users = {
            'User 1': {'Project A': 1, 'Project B': 2},
            'User 2': {'Project A': 1, 'Project B': 2},
            'User 3': {'Project B': 1, 'Project A': 2},
            'User 4': {'Project B': 1, 'Project A': 2},
        }
        page = {
            'projects': projects,
            'users': users,
            'cap_type': 'hard',
            'group_size': 2,
        }
        assign_groups(page)
        groups = page['groups']

        self.assertEqual(len(groups['Project A']), 2)
        self.assertEqual(len(groups['Project B']), 2)
        self.assertIn('User 1', groups['Project A'])
        self.assertIn('User 2', groups['Project A'])
        self.assertIn('User 3', groups['Project B'])
        self.assertIn('User 4', groups['Project B'])

        assigned_users = set()
        for project_users in groups.values():
            for user in project_users:
                assigned_users.add(user)
        self.assertEqual(len(assigned_users), len(users))

    def test_skewed_preferences_soft_cap(self):
        """
        Tests soft cap with heavily skewed preferences.
        """
        projects = ['Project A', 'Project B']
        users = {f'User {i}': {'Project A': 1, 'Project B': 2} for i in range(10)}
        page = {
            'projects': projects,
            'users': users,
            'cap_type': 'soft',
            'group_size': 5,
            'variation': 1
        }
        assign_groups(page)
        groups = page['groups']
        
        self.assertEqual(len(groups['Project A']), 6)
        self.assertEqual(len(groups['Project B']), 4)

    def test_skewed_preferences_hard_cap(self):
        """
        Tests hard cap with heavily skewed preferences.
        """
        projects = ['Project A', 'Project B']
        users = {f'User {i}': {'Project A': 1, 'Project B': 2} for i in range(10)}
        page = {
            'projects': projects,
            'users': users,
            'cap_type': 'hard',
            'group_size': 5,
        }
        assign_groups(page)
        groups = page['groups']

        self.assertEqual(len(groups['Project A']), 5)
        self.assertEqual(len(groups['Project B']), 5)

    def test_group_size_zero(self):
        """
        Tests group_size = 0. This should be handled gracefully.
        The logic should default to a group size that prevents errors.
        """
        projects = ['Project A', 'Project B']
        users = {f'User {i}': {'Project A': 1, 'Project B': 2} for i in range(10)}
        page = {
            'projects': projects,
            'users': users,
            'cap_type': 'hard',
            'group_size': 0,
        }
        assign_groups(page)
        groups = page['groups']
        
        # The behavior for group_size=0 is that no one gets assigned in hard cap
        # because the condition `len(groups[project]) < group_size` is never true.
        self.assertEqual(len(groups['Project A']), 0)
        self.assertEqual(len(groups['Project B']), 0)

    def test_group_size_larger_than_users(self):
        """
        Tests group_size larger than the total number of users.
        """
        projects = ['Project A', 'Project B']
        users = {f'User {i}': {'Project A': 1, 'Project B': 2} for i in range(3)}
        page = {
            'projects': projects,
            'users': users,
            'cap_type': 'soft',
            'group_size': 5,
            'variation': 1
        }
        assign_groups(page)
        groups = page['groups']
        
        assigned_users = set()
        for project_users in groups.values():
            for user in project_users:
                assigned_users.add(user)
        
        self.assertEqual(len(users), len(assigned_users))
        self.assertEqual(len(groups['Project A']), 3)
        self.assertEqual(len(groups['Project B']), 0)

    def test_soft_cap_zero_variation(self):
        """
        Tests soft cap with zero variation, which should behave like a hard cap.
        """
        projects = ['Project A', 'Project B']
        users = {f'User {i}': {'Project A': 1, 'Project B': 2} for i in range(10)}
        page = {
            'projects': projects,
            'users': users,
            'cap_type': 'soft',
            'group_size': 5,
            'variation': 0
        }
        assign_groups(page)
        groups = page['groups']

        # With skewed preferences, the first group gets filled to max_group_size,
        # which is 5. The rest are then balanced.
        self.assertEqual(len(groups['Project A']), 5)
        self.assertEqual(len(groups['Project B']), 5)

    def test_variation_larger_than_group_size(self):
        """
        Tests variation larger than group_size.
        min_group_size should be clamped at 1.
        """
        projects = ['Project A', 'Project B']
        users = {f'User {i}': {'Project A': 1, 'Project B': 2} for i in range(10)}
        page = {
            'projects': projects,
            'users': users,
            'cap_type': 'soft',
            'group_size': 2,
            'variation': 5 # min_group_size would be -3, but clamped to 1
        }
        assign_groups(page)
        groups = page['groups']
        
        # max_group_size is 7. All 10 users prefer Project A.
        # 7 go to A. 3 go to B.
        self.assertEqual(len(groups['Project A']), 7)
        self.assertEqual(len(groups['Project B']), 3)

    def test_all_users_identical_preferences(self):
        """
        Tests the case where all users have the exact same preferences.
        """
        projects = ['Project A', 'Project B', 'Project C']
        users = {f'User {i}': {'Project A': 1, 'Project B': 2, 'Project C': 3} for i in range(10)}
        page = {
            'projects': projects,
            'users': users,
            'cap_type': 'soft',
            'group_size': 4,
            'variation': 1
        }
        assign_groups(page)
        groups = page['groups']

        # max_group_size is 5.
        # 5 users go to Project A.
        # 5 users go to Project B.
        # 0 users go to Project C.
        self.assertEqual(len(groups['Project A']), 5)
        self.assertEqual(len(groups['Project B']), 5)
        self.assertEqual(len(groups['Project C']), 0)

    def test_group_size_one(self):
        """
        Tests group_size = 1.
        """
        projects = [f'Project {i}' for i in range(1, 6)]
        users = {f'User {i}': {p: (i + j) % 5 + 1 for j, p in enumerate(projects)} for i in range(5)}
        page = {
            'projects': projects,
            'users': users,
            'cap_type': 'hard',
            'group_size': 1,
        }
        assign_groups(page)
        groups = page['groups']

        for project in projects:
            self.assertEqual(len(groups[project]), 1)

    def test_negative_variation(self):
        """
        Tests negative variation values.
        The logic should handle this gracefully by taking the absolute value.
        """
        projects = ['Project A', 'Project B']
        users = {f'User {i}': {'Project A': 1, 'Project B': 2} for i in range(10)}
        page = {
            'projects': projects,
            'users': users,
            'cap_type': 'soft',
            'group_size': 5,
            'variation': -2
        }
        assign_groups(page)
        groups = page['groups']

        # With abs(variation), max_group_size is 7. All 10 users prefer Project A.
        # 7 go to A. Then the rest are balanced into B.
        self.assertEqual(len(groups['Project A']), 7)
        self.assertEqual(len(groups['Project B']), 3)

    def test_missing_preferences(self):
        """
        Tests users with missing preferences for some projects.
        The implementation should handle this gracefully.
        """
        projects = ['Project A', 'Project B']
        users = {
            'User 1': {'Project A': 1}, # Missing Project B
            'User 2': {'Project A': 1, 'Project B': 2}
        }
        page = {
            'projects': projects,
            'users': users,
        }
        assign_groups(page)
        groups = page['groups']

        self.assertIn('User 1', groups['Project A'])
        self.assertIn('User 2', groups['Project B'])

    def test_switching_cap_type(self):
        """
        Tests switching between hard and soft cap with the same data.
        """
        projects = ['Project A', 'Project B']
        users = {f'User {i}': {'Project A': 1, 'Project B': 2} for i in range(10)}
        
        # Hard cap
        page_hard = {
            'projects': projects,
            'users': users,
            'cap_type': 'hard',
            'group_size': 5,
        }
        assign_groups(page_hard)
        groups_hard = page_hard['groups']
        self.assertEqual(len(groups_hard['Project A']), 5)
        self.assertEqual(len(groups_hard['Project B']), 5)

        # Soft cap
        page_soft = {
            'projects': projects,
            'users': users,
            'cap_type': 'soft',
            'group_size': 5,
            'variation': 2
        }
        assign_groups(page_soft)
        groups_soft = page_soft['groups']
        self.assertEqual(len(groups_soft['Project A']), 7)
        self.assertEqual(len(groups_soft['Project B']), 3)

    def test_anti_correlated_preferences(self):
        """
        Tests anti-correlated preferences (users prefer different projects).
        """
        projects = ['Project A', 'Project B']
        users = {
            'User 1': {'Project A': 1, 'Project B': 2},
            'User 2': {'Project A': 1, 'Project B': 2},
            'User 3': {'Project B': 1, 'Project A': 2},
            'User 4': {'Project B': 1, 'Project A': 2},
        }
        page = {
            'projects': projects,
            'users': users,
            'cap_type': 'hard',
            'group_size': 2,
        }
        assign_groups(page)
        groups = page['groups']

        self.assertEqual(len(groups['Project A']), 2)
        self.assertEqual(len(groups['Project B']), 2)
        self.assertIn('User 1', groups['Project A'])
        self.assertIn('User 2', groups['Project A'])
        self.assertIn('User 3', groups['Project B'])
        self.assertIn('User 4', groups['Project B'])

if __name__ == '__main__':
    unittest.main()
