# Group Assignment Logic

## Goal

`assign_groups(page, costs=None)` in `app/main.py` puts every participant in exactly one project.
Every project runs with between `min_size` and `max_size` members.
No project is cancelled or left undersized.
Within those rules, the total cost of the rankings people receive is minimal.

## Costs

Each rank has a cost. The default is `-100, 50, 100, 200` for ranks 1 to 4.
Ranks beyond the list keep growing by the last step: 300, 400, and so on.
A missing rank counts as the last choice.

The gaps between costs set the trade-off.
The default has a large gap between ranks 1 and 2.
The solver therefore protects first choices strongly, even if that pushes a few people further down.
The admin can pass other costs through the "Recompute" form.

## Method

The problem is a min-cost flow on this graph:

- Each person supplies 1 unit of flow.
- Each person has an edge to every project with capacity 1 and the cost of their rank for it.
- Each project has an edge to a sink with capacity `max_size`.

The sink edges also need a lower bound of `min_size`.
`networkx.min_cost_flow` has no lower bounds, so the code uses the standard reduction.
Each project node gets demand `min_size`.
The sink's demand drops by `projects × min_size`.
Each sink edge keeps capacity `max_size - min_size`.

Nodes are tuples such as `('user', name)` and `('project', name)`.
A person named like a project therefore cannot collide with it.

## Feasibility

A solution exists exactly when `projects × min_size <= people <= projects × max_size`.
Every person can join every project, so no other constraint applies.
Outside that range the function raises `InfeasibleGroups` and leaves the page unchanged.
The close route then keeps the page open and shows the admin the valid range.
The admin page shows the range and the current headcount for each page.

## Legacy pages

Pages created before `min_size` and `max_size` existed store `cap_type`, `group_size` and `variation`.
`size_bounds` maps them:

- soft: `max(1, group_size - |variation|)` to `group_size + |variation|`
- hard: `1` to `group_size`

## Input validation

- Each rank from 1 to the number of projects must appear exactly once. Ties would make costs meaningless.
- Names are unique, ignoring case and surrounding spaces. A repeat would overwrite someone else's vote.
- Only a logged-in admin can close a page.
