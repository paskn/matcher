# Group Assignment Logic Documentation

## Overview

The `assign_groups` function in `app/main.py` implements a sophisticated algorithm for assigning users to project groups based on their preferences. This document explains the logic, parameters, test cases, and potential edge cases.

## Function Signature

```python
def assign_groups(page):
```

### Input Parameters

The function receives a `page` object with the following structure:

- `users`: Dictionary mapping user names to their preference dictionaries
- `projects`: List of available project names
- `cap_type`: Either "hard" or "soft" - determines how strictly group size limits are enforced
- `group_size`: Target number of users per group
- `variation`: Allowed variation from target group size (only used with "soft" cap)

## Algorithm Logic

### Step 1: Initialization and Validation

```python
users = page['users']
projects = page['projects']
num_users = len(users)
num_projects = len(projects)
cap_type = page.get('cap_type', 'soft')
group_size = page.get('group_size', num_users // num_projects if num_projects > 0 else 1)
variation = page.get('variation', 0)
```

- Extracts configuration parameters from the page object
- Calculates default group size as `num_users // num_projects` if not specified
- Handles edge case where no projects exist (defaults to group size of 1)

### Step 2: Empty Users Check

```python
if num_users == 0:
    page['groups'] = {project: [] for project in projects}
    return
```

Early return for the case where no users need to be assigned.

### Step 3: Data Structure Setup

```python
groups = {project: [] for project in projects}
assigned_users = set()

user_preferences = []
for user_name, preferences in users.items():
    sorted_prefs = sorted(preferences.items(), key=lambda item: item[1])
    user_preferences.append({'name': user_name, 'prefs': sorted_prefs})
```

- Initializes empty groups for each project
- Creates a set to track assigned users
- Processes user preferences by sorting them in ascending order (1 = most preferred)

### Step 4: Assignment Logic (Hard Cap vs Soft Cap)

#### Hard Cap Logic

When `cap_type == 'hard'`, the algorithm strictly enforces the `group_size` limit:

```python
for preference_level in range(1, num_projects + 1):
    for user in user_preferences:
        if user['name'] in assigned_users:
            continue
        for project, pref_value in user['prefs']:
            if pref_value == preference_level:
                if len(groups[project]) < group_size:
                    groups[project].append(user['name'])
                    assigned_users.add(user['name'])
                    break
```

1. **Preference Priority**: Iterates through preference levels (1 to num_projects)
2. **User Processing**: For each preference level, processes all users
3. **Assignment**: Assigns user to their preferred project if group has space
4. **Strict Limits**: Never exceeds `group_size` for any group

**Fallback for Remaining Users**:
```python
remaining_users = [user for user in user_preferences if user['name'] not in assigned_users]
for user in remaining_users:
    for project in projects:
        if len(groups[project]) < group_size:
            groups[project].append(user['name'])
            assigned_users.add(user['name'])
            break
```

#### Soft Cap Logic

When `cap_type == 'soft'`, the algorithm allows flexibility around the target group size:

```python
min_group_size = max(1, group_size - variation)
max_group_size = group_size + variation
```

**First Pass - Preference-Based Assignment**:
```python
for preference_level in range(1, num_projects + 1):
    for user in user_preferences:
        if user['name'] in assigned_users:
            continue
        for project, pref_value in user['prefs']:
            if pref_value == preference_level:
                if len(groups[project]) < max_group_size:
                    groups[project].append(user['name'])
                    assigned_users.add(user['name'])
                    break
```

**Second Pass - Balance Groups**:
```python
remaining_users = [user for user in user_preferences if user['name'] not in assigned_users]
for user in remaining_users:
    available_groups = {p: len(g) for p, g in groups.items() if len(g) < max_group_size}
    if not available_groups:
        smallest_group = min(groups, key=lambda k: len(groups[k]))
    else:
        smallest_group = min(available_groups, key=available_groups.get)
    
    groups[smallest_group].append(user['name'])
    assigned_users.add(user['name'])
```

- Prioritizes groups that haven't reached `max_group_size`
- If all groups are full, assigns to the smallest group
- Ensures balanced distribution

## Existing Test Cases

### Test 1: `test_even_distribution`

**Purpose**: Validates that the algorithm can produce equal-sized groups when mathematically possible.

**Setup**:
- 5 projects
- 50 users (10 users per project)
- Soft cap with group_size=10, variation=0
- Users have rotating preferences to ensure even distribution

**Expected Result**: Each project gets exactly 10 users.

**Code**:
```python
projects = [f'Project {i}' for i in range(1, 6)]
users = {f'User {i}': {p: (i + j) % 5 + 1 for j, p in enumerate(projects)} for i in range(50)}
page = {
    'projects': projects,
    'users': users,
    'cap_type': 'soft',
    'group_size': 10,
    'variation': 0
}
```

### Test 2: `test_all_users_assigned`

**Purpose**: Ensures no user is left unassigned, even with uneven numbers.

**Setup**:
- 3 projects
- 23 users (cannot be evenly divided)
- Soft cap with group_size=8, variation=2
- Allows groups to have 6-10 users

**Expected Result**: All 23 users are assigned across the 3 projects.

**Code**:
```python
projects = [f'Project {i}' for i in range(1, 4)]
users = {f'User {i}': {p: (i + j) % 3 + 1 for j, p in enumerate(projects)} for i in range(23)}
page = {
    'projects': projects,
    'users': users,
    'cap_type': 'soft',
    'group_size': 8,
    'variation': 2
}
```

## Edge Cases for Future Testing

### 1. **Empty or Minimal Data**
- [ ] No users (`users = {}`)
- [ ] No projects (`projects = []`)
- [ ] Single user, single project
- [ ] Single user, multiple projects
- [ ] Multiple users, single project

### 2. **Extreme Group Sizes**
- [ ] `group_size = 0` (should handle gracefully)
- [ ] `group_size = 1` (minimal groups)
- [ ] `group_size` larger than total users
- [ ] Very large `group_size` (e.g., 1000) with few users

### 3. **Variation Edge Cases**
- [ ] `variation = 0` (strict group sizes)
- [ ] `variation` larger than `group_size`
- [ ] Negative `variation` values
- [ ] Very large `variation` values

### 4. **Preference Edge Cases**
- [ ] All users have identical preferences
- [ ] Users with missing preferences for some projects
- [ ] Users with duplicate preference values
- [ ] Preferences with values outside expected range (e.g., 0, negative, >num_projects)
- [ ] Users with only partial preferences (not all projects ranked)

### 5. **Hard Cap vs Soft Cap Edge Cases**
- [ ] Hard cap with impossible constraints (too many users for available spots)
- [ ] Hard cap with exact capacity match
- [ ] Soft cap with zero variation (should behave like hard cap)
- [ ] Switching between hard and soft cap with same data

### 6. **User Distribution Scenarios**
- [ ] Heavily skewed preferences (everyone wants the same project)
- [ ] Anti-correlated preferences (users prefer different projects)
- [ ] Sequential preferences (User 1 prefers 1,2,3..., User 2 prefers 2,3,1...)
- [ ] Random/shuffled preferences

### 7. **Data Type and Format Edge Cases**
- [ ] Non-string user names (numbers, special characters)
- [ ] Non-string project names
- [ ] Unicode characters in names
- [ ] Very long user/project names
- [ ] Empty string names

### 8. **Performance and Scale Edge Cases**
- [ ] Large number of users (1000+)
- [ ] Large number of projects (100+)
- [ ] Large user-to-project ratios
- [ ] Memory usage with large datasets

### 9. **Configuration Edge Cases**
- [ ] Missing configuration parameters
- [ ] Invalid configuration types (string instead of int)
- [ ] `cap_type` values other than "hard" or "soft"
- [ ] Page object missing required keys

### 10. **Mathematical Edge Cases**
- [ ] Prime number of users with even number of projects
- [ ] Fibonacci sequences in user/project counts
- [ ] Users exactly equal to total capacity
- [ ] Users slightly over/under total capacity

## Recommendations for Test Implementation

When implementing these edge cases as tests, consider:

1. **Assertion Strategies**:
   - Verify all users are assigned (no user left behind)
   - Check group size constraints are respected
   - Validate preference satisfaction where possible
   - Ensure deterministic behavior for identical inputs

2. **Test Organization**:
   - Group related edge cases into test classes
   - Use parameterized tests for similar scenarios with different inputs
   - Add descriptive test names and docstrings

3. **Error Handling**:
   - Test that the function handles invalid inputs gracefully
   - Verify appropriate fallback behaviors
   - Consider adding input validation to the function if needed

## Performance Characteristics

- **Time Complexity**: O(U × P × P) where U = users, P = projects
- **Space Complexity**: O(U + P) for data structures
- **Scalability**: Suitable for typical web application loads (hundreds of users/projects)

## Future Improvements

1. **Optimization**: Consider more efficient algorithms for large datasets
2. **Preferences**: Support for weighted preferences or partial rankings
3. **Constraints**: Additional constraints like skill matching or team diversity
4. **Reporting**: Return assignment statistics and satisfaction metrics