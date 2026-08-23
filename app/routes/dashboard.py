from flask import Blueprint, render_template, session
from app.utils.helpers import login_required, get_current_month_year, days_elapsed_this_month, days_remaining_this_month
from app.services import supabase_service as db
from app.services import analysis_service, prediction_service, budget_service
import calendar

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/dashboard')
@login_required
def dashboard():
    user_id = session['user_id']
    year, month = get_current_month_year()

    profile = db.get_profile(user_id)
    monthly_income = float(profile.get('monthly_income', 0)) if profile else 0.0

    # Transactions for this month
    transactions = db.get_transactions_by_month(user_id, year, month)
    all_transactions = db.get_transactions(user_id, limit=500)

    # Spending analysis
    analysis = analysis_service.analyze_spending(transactions, year, month)
    all_analysis = analysis_service.analyze_spending(all_transactions)

    total_expenses = analysis['total_expenses']
    category_spending = analysis['category_spending']
    avg_daily = analysis['avg_daily_spending']

    # Budget for this month
    budget = db.get_budget(user_id, year, month)
    budget_amount = float(budget['amount']) if budget else 0.0
    savings_target = float(budget['savings_target']) if budget else 0.0
    budget_categories = budget.get('budget_categories', []) if budget else []

    # Prediction
    days_elapsed = days_elapsed_this_month()
    days_in_month = calendar.monthrange(year, month)[1]
    prediction = prediction_service.try_ml_prediction(
        all_analysis['monthly_trend'],
        total_expenses,
        avg_daily,
        year, month
    )
    predicted_spending = prediction['predicted_spending']
    days_remaining = prediction['days_remaining']

    # Budget summary
    budget_summary = budget_service.get_budget_summary(total_expenses, budget_amount, monthly_income)

    # Risk detection
    risks = budget_service.detect_budget_risks(
        total_expenses, budget_amount, predicted_spending, savings_target,
        monthly_income, days_elapsed, days_in_month, category_spending, budget_categories
    )

    # Savings goals
    goals = db.get_goals(user_id)
    total_saved = sum(float(g.get('saved_amount', 0)) for g in goals)

    # Recent transactions (5)
    recent_transactions = (db.get_transactions(user_id, limit=5))

    month_name = calendar.month_name[month]

    return render_template('dashboard.html',
        profile=profile,
        monthly_income=monthly_income,
        total_expenses=total_expenses,
        total_income=analysis['total_income'],
        category_spending=category_spending,
        avg_daily=avg_daily,
        budget=budget,
        budget_amount=budget_amount,
        savings_target=savings_target,
        predicted_spending=predicted_spending,
        days_remaining=days_remaining,
        budget_summary=budget_summary,
        risks=risks,
        goals=goals,
        total_saved=total_saved,
        recent_transactions=recent_transactions,
        month_name=month_name,
        year=year,
        month=month,
        analysis=analysis
    )
