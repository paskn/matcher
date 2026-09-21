
from flask import Flask, render_template, request, redirect, url_for, abort, session, flash
import json
import os
import re
import networkx as nx

app = Flask(__name__)
app.secret_key = os.urandom(24)

DATA_FILE = 'data.json'

def get_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, 'r') as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=4)

def slugify(s):
    s = s.lower().strip()
    s = re.sub(r'[\s_]+', '-', s)
    s = re.sub(r'[^a-z0-9-]', '', s)
    return s

@app.route('/')
def index():
    if 'logged_in' in session:
        return redirect(url_for('admin'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        password = request.form.get('password')
        if password == os.environ.get('ADMIN_PASSWORD'):
            session['logged_in'] = True
            return redirect(url_for('admin'))
        else:
            flash('Invalid password')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        page_name = request.form.get('page_name')
        projects = [p.strip() for p in request.form.get('projects', '').split(',') if p.strip()]
        try:
            min_size = int(request.form.get('min_size'))
            max_size = int(request.form.get('max_size'))
        except (TypeError, ValueError):
            flash('Group sizes must be whole numbers.')
            return redirect(url_for('admin'))
        if not 1 <= min_size <= max_size:
            flash('Group sizes need 1 <= minimum <= maximum.')
            return redirect(url_for('admin'))
        if len(set(projects)) != len(projects):
            flash('Project names must be unique.')
            return redirect(url_for('admin'))

        if page_name and projects:
            data = get_data()
            slug = slugify(page_name)
            page_id = slug
            i = 1
            while page_id in data:
                page_id = f'{slug}-{i}'
                i += 1
            data[page_id] = {
                'name': page_name,
                'projects': projects,
                'users': {},
                'closed': False,
                'min_size': min_size,
                'max_size': max_size
            }
            save_data(data)
            return redirect(url_for('admin'))
    pages = get_data()
    ranges = {page_id: feasible_range(page) for page_id, page in pages.items()}
    bounds = {page_id: size_bounds(page) for page_id, page in pages.items()}
    return render_template('admin.html', pages=pages, ranges=ranges, bounds=bounds,
                           default_costs=DEFAULT_COSTS)

@app.route('/admin/delete/<page_id>', methods=['POST'])
def delete_page(page_id):
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    data = get_data()
    if page_id in data:
        del data[page_id]
        save_data(data)
    return redirect(url_for('admin'))

@app.route('/admin/sizes/<page_id>', methods=['POST'])
def set_sizes(page_id):
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    data = get_data()
    page = data.get(page_id)
    if not page:
        abort(404)
    try:
        min_size = int(request.form.get('min_size'))
        max_size = int(request.form.get('max_size'))
    except (TypeError, ValueError):
        flash('Group sizes must be whole numbers.')
        return redirect(url_for('admin'))
    if not 1 <= min_size <= max_size:
        flash('Group sizes need 1 <= minimum <= maximum.')
        return redirect(url_for('admin'))
    # Groups on a closed page must match its sizes, so regroup right away.
    # Work on a copy: if the new sizes cannot fit the headcount, nothing is saved.
    updated = dict(page, min_size=min_size, max_size=max_size)
    if updated['closed']:
        try:
            assign_groups(updated)
        except InfeasibleGroups as e:
            flash(str(e))
            return redirect(url_for('admin'))
    data[page_id] = updated
    save_data(data)
    return redirect(url_for('admin'))

@app.route('/<page_id>')
def choice(page_id):
    data = get_data()
    page = data.get(page_id)
    if not page:
        abort(404)
    return render_template('choice.html', page=page, page_id=page_id)

@app.route('/<page_id>/submit', methods=['POST'])
def submit(page_id):
    data = get_data()
    page = data.get(page_id)
    if not page or page['closed']:
        abort(404)
    
    user_name = (request.form.get('user_name') or '').strip()
    if not user_name:
        flash('Please enter your name.')
        return redirect(url_for('choice', page_id=page_id))
    # Names are the only identity. A silent overwrite would erase someone
    # else's vote, so near-duplicates are rejected.
    if user_name.casefold() in {u.casefold() for u in page['users']}:
        flash(f'The name "{user_name}" is already taken. Add a surname or initial.')
        return redirect(url_for('choice', page_id=page_id))

    preferences = {}
    try:
        for project in page['projects']:
            preferences[project] = int(request.form.get(f'preference_{project}'))
    except (TypeError, ValueError):
        flash('Please rank every project.')
        return redirect(url_for('choice', page_id=page_id))
    # Tied ranks make the costs meaningless, so each rank must be used once.
    num_projects = len(page['projects'])
    if sorted(preferences.values()) != list(range(1, num_projects + 1)):
        flash(f'Use each rank from 1 to {num_projects} exactly once.')
        return redirect(url_for('choice', page_id=page_id))

    page['users'][user_name] = preferences
    save_data(data)
    flash(f'Thanks, {user_name}. Your ranking is saved.')

    return redirect(url_for('choice', page_id=page_id))

@app.route('/<page_id>/close', methods=['POST'])
def close(page_id):
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    data = get_data()
    page = data.get(page_id)
    if not page:
        abort(404)

    try:
        assign_groups(page)
    except InfeasibleGroups as e:
        # Keep the page open so the admin can adjust sizes or collect more votes.
        flash(str(e))
        return redirect(url_for('admin'))
    page['closed'] = True
    save_data(data)

    return redirect(url_for('results', page_id=page_id))

def equal_sizes(num_users, num_projects):
    """Tightest (min_size, max_size) that fits the headcount exactly."""
    # Floor and ceiling of the mean make groups differ by at most one person.
    # This pair is always feasible when there is at least one person per project.
    return num_users // num_projects, -(-num_users // num_projects)

@app.route('/<page_id>/close-equal', methods=['POST'])
def close_equal(page_id):
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    data = get_data()
    page = data.get(page_id)
    if not page:
        abort(404)

    num_users = len(page['users'])
    num_projects = len(page['projects'])
    # Every project must run, so each needs at least one person.
    if num_users < num_projects:
        flash(f'{num_users} people cannot fill {num_projects} projects. '
              f'Each project needs at least one person.')
        return redirect(url_for('admin'))

    min_size, max_size = equal_sizes(num_users, num_projects)
    # Work on a copy so a failure leaves the stored sizes untouched.
    updated = dict(page, min_size=min_size, max_size=max_size)
    try:
        assign_groups(updated)
    except InfeasibleGroups as e:
        flash(str(e))
        return redirect(url_for('admin'))
    updated['closed'] = True
    data[page_id] = updated
    save_data(data)

    return redirect(url_for('results', page_id=page_id))

@app.route('/<page_id>/reopen', methods=['POST'])
def reopen(page_id):
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    data = get_data()
    page = data.get(page_id)
    if not page:
        abort(404)
    
    page['closed'] = False
    page.pop('groups', None)
    page.pop('algorithm', None)
    save_data(data)
    
    return redirect(url_for('admin'))

@app.route('/<page_id>/results')
def results(page_id):
    data = get_data()
    page = data.get(page_id)
    if not page or not page['closed']:
        abort(404)
    
    return render_template('results.html', page=page)

@app.route('/admin/recompute/<page_id>', methods=['POST'])
def recompute(page_id):
    if 'logged_in' not in session:
        return redirect(url_for('login'))

    data = get_data()
    page = data.get(page_id)
    if not page:
        abort(404)

    costs_str = request.form.get('costs', '').strip()
    try:
        costs = [int(x) for x in costs_str.split(',')] if costs_str else None
    except ValueError:
        flash(f'Costs must be comma-separated integers, got "{costs_str}".')
        return redirect(url_for('admin'))

    try:
        assign_groups(page, costs)
    except InfeasibleGroups as e:
        flash(str(e))
        return redirect(url_for('admin'))
    # Later regroupings, e.g. after a size change, reuse these costs.
    if costs:
        page['costs'] = costs

    save_data(data)
    return redirect(url_for('admin'))

DEFAULT_COSTS = [-100, 50, 100, 200]

class InfeasibleGroups(ValueError):
    pass

def size_bounds(page):
    """Return (min_size, max_size) for every group on the page."""
    if 'min_size' in page:
        return page['min_size'], page['max_size']
    # Pages created before min/max fields existed stored a target size and a
    # variation. A hard cap had no lower bound, so it maps to a minimum of 1.
    group_size = page.get('group_size', 1)
    variation = abs(page.get('variation', 0))
    if page.get('cap_type') == 'hard':
        return 1, group_size
    return max(1, group_size - variation), group_size + variation

def feasible_range(page):
    """Headcounts for which every project can run within its size bounds."""
    min_size, max_size = size_bounds(page)
    num_projects = len(page['projects'])
    return num_projects * min_size, num_projects * max_size

def rank_cost(rank, costs):
    """Cost of giving someone their `rank`-th choice (1 = first choice)."""
    if rank <= len(costs):
        return costs[rank - 1]
    # Ranks beyond the cost list keep growing by the last step. Otherwise the
    # solver would treat a 5th and a 10th choice as equally bad.
    step = costs[-1] - costs[-2] if len(costs) > 1 else 0
    return costs[-1] + (rank - len(costs)) * step

def assign_groups(page, costs=None):
    """Assign every user to exactly one project, minimising total rank cost.

    Every project receives between min_size and max_size members. No project
    is left empty or undersized, because events cannot cancel projects.
    Raises InfeasibleGroups when the headcount cannot fit those bounds.
    """
    users = page['users']
    projects = page['projects']
    costs = costs or page.get('costs') or DEFAULT_COSTS
    num_users = len(users)
    num_projects = len(projects)

    if num_projects == 0:
        page['groups'] = {}
        return
    if num_users == 0:
        page['groups'] = {project: [] for project in projects}
        return

    min_size, max_size = size_bounds(page)
    if min_size > max_size:
        raise InfeasibleGroups(f'Minimum group size {min_size} exceeds maximum {max_size}.')
    low, high = feasible_range(page)
    if not low <= num_users <= high:
        raise InfeasibleGroups(
            f'{num_users} people cannot fill {num_projects} projects of '
            f'{min_size}-{max_size} people each. '
            f'The headcount must be between {low} and {high}.'
        )

    # Tuple node names keep users and projects apart when a person's name
    # matches a project name.
    G = nx.DiGraph()
    # Min-cost flow has no native lower bound on edges. The standard reduction
    # pre-routes min_size units through each project->dest edge: the project
    # node must absorb min_size units, dest absorbs that much less, and the
    # edge keeps only the remaining capacity max_size - min_size.
    G.add_node(('dest',), demand=num_users - num_projects * min_size)
    for project in projects:
        G.add_node(('project', project), demand=min_size)
        G.add_edge(('project', project), ('dest',), capacity=max_size - min_size, weight=0)

    for user_name, preferences in users.items():
        G.add_node(('user', user_name), demand=-1)
        for project in projects:
            # A missing rank counts as the last choice.
            rank = preferences.get(project, num_projects)
            G.add_edge(('user', user_name), ('project', project),
                       capacity=1, weight=rank_cost(rank, costs))

    flowdict = nx.min_cost_flow(G)

    groups = {project: [] for project in projects}
    for user_name in users:
        for (_, project), flow in flowdict[('user', user_name)].items():
            if flow:
                groups[project].append(user_name)

    page['groups'] = groups
    page['algorithm'] = f'min-cost, group size {min_size}-{max_size}, costs {costs}'

if __name__ == '__main__':
    app.run(debug=True)
