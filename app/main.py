
from flask import Flask, render_template, request, redirect, url_for, abort, session, flash
import json
import os
import uuid

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
        projects = request.form.get('projects').split(',')
        if page_name and projects:
            data = get_data()
            page_id = str(uuid.uuid4())
            data[page_id] = {
                'name': page_name,
                'projects': [p.strip() for p in projects],
                'users': {},
                'closed': False
            }
            save_data(data)
            return redirect(url_for('admin'))
    return render_template('admin.html', pages=get_data())

@app.route('/admin/delete/<page_id>', methods=['POST'])
def delete_page(page_id):
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    data = get_data()
    if page_id in data:
        del data[page_id]
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
    
    user_name = request.form.get('user_name')
    preferences = {}
    for project in page['projects']:
        preferences[project] = int(request.form.get(f'preference_{project}'))

    if user_name and preferences:
        page['users'][user_name] = preferences
        save_data(data)

    return redirect(url_for('choice', page_id=page_id))

@app.route('/<page_id>/close', methods=['POST'])
def close(page_id):
    data = get_data()
    page = data.get(page_id)
    if not page:
        abort(404)
    
    page['closed'] = True
    assign_groups(page)
    save_data(data)
    
    return redirect(url_for('results', page_id=page_id))

@app.route('/<page_id>/results')
def results(page_id):
    data = get_data()
    page = data.get(page_id)
    if not page or not page['closed']:
        abort(404)
    
    return render_template('results.html', page=page)

def assign_groups(page):
    users = page['users']
    projects = page['projects']
    num_users = len(users)
    num_projects = len(projects)

    if num_users == 0:
        page['groups'] = {project: [] for project in projects}
        return

    ideal_group_size = num_users / num_projects
    groups = {project: [] for project in projects}
    assigned_users = set()

    # Create a list of users with their preferences sorted
    user_preferences = []
    for user_name, preferences in users.items():
        sorted_prefs = sorted(preferences.items(), key=lambda item: item[1])
        user_preferences.append({'name': user_name, 'prefs': sorted_prefs})

    # Assign users to their most preferred groups
    for preference_level in range(1, num_projects + 1):
        for user in user_preferences:
            if user['name'] in assigned_users:
                continue

            for project, pref_value in user['prefs']:
                if pref_value == preference_level:
                    if len(groups[project]) < ideal_group_size:
                        groups[project].append(user['name'])
                        assigned_users.add(user['name'])
                        break

    # Assign remaining users to the smallest groups
    remaining_users = [user for user in user_preferences if user['name'] not in assigned_users]
    for user in remaining_users:
        smallest_group = min(groups, key=lambda k: len(groups[k]))
        groups[smallest_group].append(user['name'])
        assigned_users.add(user['name'])

    page['groups'] = groups

if __name__ == '__main__':
    app.run(debug=True)
