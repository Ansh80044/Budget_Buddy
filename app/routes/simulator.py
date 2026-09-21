from flask import Blueprint, render_template, request, session, jsonify
from app.utils.helpers import login_required, safe_float, get_current_month_year
from app.services import supabase_service as db
from app.services import analysis_service
import calendar

simulator_bp = Blueprint('simulator', __name__)


@simulator_bp.route('/simulator')
@login_required
def simulator():
    user_id = session['user_id']
    year, month = get_current_month_year()

    profile = db.get_profile(user_id)
    monthly_income = float(profile.get('monthly_income', 0)) if profile else 0.0

    month_tx = db.get_transactions_by_month(user_id, year, month)
    analysis = analysis_service.analyze_spending(month_tx, year, month)

    budget = db.get_budget(user_id, year, month)
    budget_amount = float(budget['amount']) if budget else 0.0
    savings_target = float(budget['savings_target']) if budget else 0.0

    total_expenses = analysis['total_expenses']
    current_balance = monthly_income - total_expenses

    goals = db.get_goals(user_id)

    return render_template(
        'simulator.html',
        monthly_income=monthly_income,
        total_expenses=total_expenses,
        current_balance=current_balance,
        budget_amount=budget_amount,
        savings_target=savings_target,
        category_spending=analysis['category_spending'],
        goals=goals,
        profile=profile
    )


@simulator_bp.route('/api/simulator/run', methods=['POST'])
@login_required
def run_simulation():
    """
    Run a what-if simulation WITHOUT modifying real data.
    All calculations happen here in Python (backend).
    """
    user_id = session['user_id']
    data = request.get_json()

    scenario = data.get('scenario', 'purchase')

    year, month = get_current_month_year()
    profile = db.get_profile(user_id)
    monthly_income = float(profile.get('monthly_income', 0)) if profile else 0.0

    month_tx = db.get_transactions_by_month(user_id, year, month)
    analysis = analysis_service.analyze_spending(month_tx, year, month)

    budget = db.get_budget(user_id, year, month)
    budget_amount = float(budget['amount']) if budget else 0.0
    savings_target = float(budget['savings_target']) if budget else 0.0

    total_expenses = analysis['total_expenses']
    category_spending = dict(analysis['category_spending'])

    days_in_month = calendar.monthrange(year, month)[1]
    import datetime
    days_elapsed = datetime.date.today().day
    days_remaining = max(days_in_month - days_elapsed, 0)

    # ── Simulation logic ──
    sim_income = monthly_income
    sim_expenses = total_expenses
    sim_budget = budget_amount
    sim_savings_target = savings_target
    sim_category = dict(category_spending)
    notes = []

    if scenario == 'purchase':
        purchase_amount = safe_float(data.get('amount', 0))
        purchase_desc = data.get('description', 'Purchase')
        sim_expenses += purchase_amount
        notes.append(f"Added hypothetical purchase '{purchase_desc}' for ₹{purchase_amount:,.0f}")

    elif scenario == 'reduce_category':
        category = data.get('category', '')
        reduce_by = safe_float(data.get('reduce_by', 0))
        if category in sim_category:
            sim_category[category] = max(0, sim_category[category] - reduce_by)
            sim_expenses = sum(sim_category.values())
            notes.append(f"Reduced '{category}' spending by ₹{reduce_by:,.0f}")

    elif scenario == 'increase_income':
        extra_income = safe_float(data.get('amount', 0))
        sim_income += extra_income
        notes.append(f"Added extra income of ₹{extra_income:,.0f}")

    elif scenario == 'savings_boost':
        extra_savings = safe_float(data.get('amount', 0))
        sim_savings_target += extra_savings
        notes.append(f"Increased savings target by ₹{extra_savings:,.0f}")

    elif scenario == 'change_budget':
        new_budget = safe_float(data.get('amount', 0))
        sim_budget = new_budget
        notes.append(f"Changed budget to ₹{new_budget:,.0f}")

    # Recalculate derived values
    sim_balance = sim_income - sim_expenses
    sim_remaining_budget = sim_budget - sim_expenses
    sim_budget_usage_pct = (sim_expenses / sim_budget * 100) if sim_budget > 0 else 0
    sim_potential_savings = sim_income - sim_expenses
    sim_savings_gap = sim_savings_target - sim_potential_savings

    # Predict after simulation
    sim_avg_daily = sim_expenses / days_elapsed if days_elapsed > 0 else 0
    sim_predicted = sim_expenses + (sim_avg_daily * days_remaining)

    return jsonify({
        'scenario': scenario,
        'notes': notes,
        'before': {
            'income': monthly_income,
            'expenses': total_expenses,
            'balance': monthly_income - total_expenses,
            'remaining_budget': budget_amount - total_expenses,
            'budget_usage_pct': round((total_expenses / budget_amount * 100) if budget_amount > 0 else 0, 1),
            'potential_savings': monthly_income - total_expenses,
            'predicted_spending': round(total_expenses + (analysis['avg_daily_spending'] * days_remaining), 0)
        },
        'after': {
            'income': sim_income,
            'expenses': round(sim_expenses, 0),
            'balance': round(sim_balance, 0),
            'remaining_budget': round(sim_remaining_budget, 0),
            'budget_usage_pct': round(sim_budget_usage_pct, 1),
            'potential_savings': round(sim_potential_savings, 0),
            'savings_gap': round(sim_savings_gap, 0),
            'predicted_spending': round(sim_predicted, 0),
            'category_spending': {k: round(v, 0) for k, v in sim_category.items()}
        },
        'over_budget': sim_expenses > sim_budget,
        'meets_savings': sim_potential_savings >= sim_savings_target
    })
