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

if __name__ == '__main__':
    unittest.main()
