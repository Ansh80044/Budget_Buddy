from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from app.utils.helpers import login_required, safe_float, get_current_month_year
from app.services import supabase_service as db
from app.services import analysis_service, budget_service
from app.services.ai_service import EXPENSE_CATEGORIES
import calendar

budget_bp = Blueprint('budget', __name__)


@budget_bp.route('/budget')
@login_required
def budget():
    user_id = session['user_id']
    year, month = get_current_month_year()
    profile = db.get_profile(user_id)
    monthly_income = float(profile.get('monthly_income', 0)) if profile else 0.0

    current_budget = db.get_budget(user_id, year, month)
    transactions = db.get_transactions_by_month(user_id, year, month)
    analysis = analysis_service.analyze_spending(transactions, year, month)

    # Get all-time category spending for recommendation
    all_tx = db.get_transactions(user_id, limit=500)
    all_analysis = analysis_service.analyze_spending(all_tx)

    recommendation = budget_service.generate_budget_recommendation(
        monthly_income,
        float(current_budget['savings_target']) if current_budget else 0,
        all_analysis['category_spending']
    )

    goals = db.get_goals(user_id)
    month_name = calendar.month_name[month]

    return render_template(
        'budget.html',
        budget=current_budget,
        monthly_income=monthly_income,
        analysis=analysis,
        recommendation=recommendation,
        categories=EXPENSE_CATEGORIES,
        goals=goals,
        month_name=month_name,
        year=year,
        month=month,
        profile=profile
    )


@budget_bp.route('/budget/save', methods=['POST'])
@login_required
def save_budget():
    user_id = session['user_id']
    year, month = get_current_month_year()
    amount = safe_float(request.form.get('amount', 0))
    savings_target = safe_float(request.form.get('savings_target', 0))

    existing = db.get_budget(user_id, year, month)
    try:
        if existing:
            db.update_budget(existing['id'], user_id, {'amount': amount, 'savings_target': savings_target})
            budget_id = existing['id']
        else:
            result = db.create_budget({'user_id': user_id, 'month': month, 'year': year, 'amount': amount, 'savings_target': savings_target})
            budget_id = result.data[0]['id'] if (result and hasattr(result, 'data') and result.data) else None

        # Save category limits if budget_id was found/created
        if budget_id:
            categories = request.form.getlist('category_name[]')
            limits = request.form.getlist('category_limit[]')
            for cat, lim in zip(categories, limits):
                limit_amount = safe_float(lim)
                if cat and limit_amount > 0:
                    db.upsert_budget_category(budget_id, cat, limit_amount)

        flash('Budget saved successfully!', 'success')
    except Exception as e:
        flash(f'Error saving budget: {str(e)}', 'error')

    return redirect(url_for('budget.budget'))


@budget_bp.route('/api/budget/recommend', methods=['POST'])
@login_required
def api_recommend():
    user_id = session['user_id']
    data = request.get_json()
    monthly_income = safe_float(data.get('monthly_income', 0))
    savings_target = safe_float(data.get('savings_target', 0))

    all_tx = db.get_transactions(user_id, limit=500)
    all_analysis = analysis_service.analyze_spending(all_tx)

    recommendation = budget_service.generate_budget_recommendation(
        monthly_income, savings_target, all_analysis['category_spending']
    )
    return jsonify(recommendation)
