from flask import Blueprint, render_template, session, jsonify
from app.utils.helpers import login_required, get_current_month_year
from app.services import supabase_service as db
from app.services import analysis_service, prediction_service, budget_service
import calendar

reports_bp = Blueprint('reports', __name__)


@reports_bp.route('/reports')
@login_required
def reports():
    user_id = session['user_id']
    year, month = get_current_month_year()

    all_transactions = db.get_transactions(user_id, limit=500)
    month_transactions = db.get_transactions_by_month(user_id, year, month)

    analysis = analysis_service.analyze_spending(month_transactions, year, month)
    all_analysis = analysis_service.analyze_spending(all_transactions)

    profile = db.get_profile(user_id)
    monthly_income = float(profile.get('monthly_income', 0)) if profile else 0.0

    budget = db.get_budget(user_id, year, month)
    budget_amount = float(budget['amount']) if budget else 0.0
    savings_target = float(budget['savings_target']) if budget else 0.0

    prediction = prediction_service.try_ml_prediction(
        all_analysis['monthly_trend'],
        analysis['total_expenses'],
        analysis['avg_daily_spending'],
        year, month
    )

    goals = db.get_goals(user_id)
    total_goal_target = sum(float(g.get('target_amount', 0)) for g in goals)
    total_saved = sum(float(g.get('saved_amount', 0)) for g in goals)

    month_name = calendar.month_name[month]

    return render_template('reports.html',
        analysis=analysis,
        all_analysis=all_analysis,
        monthly_income=monthly_income,
        budget_amount=budget_amount,
        savings_target=savings_target,
        prediction=prediction,
        goals=goals,
        total_goal_target=total_goal_target,
        total_saved=total_saved,
        month_name=month_name,
        year=year,
        month=month,
        profile=profile
    )


@reports_bp.route('/api/reports/data')
@login_required
def api_reports_data():
    user_id = session['user_id']
    year, month = get_current_month_year()

    all_tx = db.get_transactions(user_id, limit=500)
    month_tx = db.get_transactions_by_month(user_id, year, month)

    analysis = analysis_service.analyze_spending(month_tx, year, month)
    all_analysis = analysis_service.analyze_spending(all_tx)

    profile = db.get_profile(user_id)
    monthly_income = float(profile.get('monthly_income', 0)) if profile else 0.0
    budget = db.get_budget(user_id, year, month)
    budget_amount = float(budget['amount']) if budget else 0.0

    return jsonify({
        'category_spending': analysis['category_spending'],
        'monthly_trend': all_analysis['monthly_trend'],
        'weekly_spending': analysis['weekly_spending'],
        'total_expenses': analysis['total_expenses'],
        'total_income': analysis['total_income'],
        'monthly_income': monthly_income,
        'budget_amount': budget_amount,
        'largest_expenses': analysis['largest_expenses']
    })
