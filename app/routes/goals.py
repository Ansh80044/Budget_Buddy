from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from app.utils.helpers import login_required, safe_float
from app.services import supabase_service as db
from datetime import date

goals_bp = Blueprint('goals', __name__)


@goals_bp.route('/goals')
@login_required
def goals():
    user_id = session['user_id']
    all_goals = db.get_goals(user_id)
    return render_template('goals.html', goals=all_goals, today=str(date.today()))


@goals_bp.route('/goals/add', methods=['POST'])
@login_required
def add_goal():
    user_id = session['user_id']
    name = request.form.get('name', '').strip()
    target_amount = safe_float(request.form.get('target_amount', 0))
    saved_amount = safe_float(request.form.get('saved_amount', 0))
    deadline = request.form.get('deadline', '').strip() or None

    if not name or target_amount <= 0:
        flash('Please provide a goal name and valid target amount.', 'error')
        return redirect(url_for('goals.goals'))

    data = {
        'user_id': user_id,
        'name': name,
        'target_amount': target_amount,
        'saved_amount': saved_amount,
        'deadline': deadline
    }
    try:
        db.create_goal(data)
        flash('Savings goal created!', 'success')
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
    return redirect(url_for('goals.goals'))


@goals_bp.route('/goals/<goal_id>/update', methods=['POST'])
@login_required
def update_goal(goal_id):
    user_id = session['user_id']
    name = request.form.get('name', '').strip()
    target_amount = safe_float(request.form.get('target_amount', 0))
    saved_amount = safe_float(request.form.get('saved_amount', 0))
    deadline = request.form.get('deadline', '').strip() or None

    update_data = {
        'name': name,
        'target_amount': target_amount,
        'saved_amount': saved_amount,
        'deadline': deadline
    }
    try:
        db.update_goal(goal_id, user_id, update_data)
        flash('Goal updated!', 'success')
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
    return redirect(url_for('goals.goals'))


@goals_bp.route('/goals/<goal_id>/delete', methods=['POST'])
@login_required
def delete_goal(goal_id):
    user_id = session['user_id']
    try:
        db.delete_goal(goal_id, user_id)
        flash('Goal deleted.', 'success')
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
    return redirect(url_for('goals.goals'))


@goals_bp.route('/goals/<goal_id>/contribute', methods=['POST'])
@login_required
def contribute_goal(goal_id):
    user_id = session['user_id']
    goal = db.get_goal(goal_id, user_id)
    if not goal:
        flash('Goal not found.', 'error')
        return redirect(url_for('goals.goals'))

    contribution = safe_float(request.form.get('contribution', 0))
    new_saved = float(goal.get('saved_amount', 0)) + contribution

    try:
        db.update_goal(goal_id, user_id, {'saved_amount': new_saved})
        flash(f'Added ₹{contribution:,.0f} to {goal["name"]}!', 'success')
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
    return redirect(url_for('goals.goals'))
