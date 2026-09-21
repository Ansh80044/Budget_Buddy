from flask import Blueprint, render_template, request, session, jsonify
from app.utils.helpers import login_required, get_current_month_year, days_remaining_this_month
from app.services import supabase_service as db
from app.services import analysis_service, prediction_service, budget_service
from app.services.ai_service import get_financial_coach_response

ai_bp = Blueprint('ai', __name__)


@ai_bp.route('/coach')
@login_required
def coach():
    return render_template('coach.html')


@ai_bp.route('/api/coach/ask', methods=['POST'])
@login_required
def ask_coach():
    user_id = session['user_id']
    data = request.get_json()
    question = data.get('question', '').strip()

    if not question:
        return jsonify({'error': 'Please ask a question.'}), 400

    # Build financial context
    year, month = get_current_month_year()
    profile = db.get_profile(user_id)
    monthly_income = float(profile.get('monthly_income', 0)) if profile else 0.0

    month_tx = db.get_transactions_by_month(user_id, year, month)
    all_tx = db.get_transactions(user_id, limit=500)

    analysis = analysis_service.analyze_spending(month_tx, year, month)
    all_analysis = analysis_service.analyze_spending(all_tx)

    budget = db.get_budget(user_id, year, month)
    budget_amount = float(budget['amount']) if budget else 0.0
    savings_target = float(budget['savings_target']) if budget else 0.0
    budget_categories = budget.get('budget_categories', []) if budget else []

    days_remaining = days_remaining_this_month()
    import calendar as cal
    days_in_month = cal.monthrange(year, month)[1]
    days_elapsed = days_in_month - days_remaining

    prediction = prediction_service.try_ml_prediction(
        all_analysis['monthly_trend'],
        analysis['total_expenses'],
        analysis['avg_daily_spending'],
        year, month
    )

    budget_summary = budget_service.get_budget_summary(analysis['total_expenses'], budget_amount, monthly_income)
    risks = budget_service.detect_budget_risks(
        analysis['total_expenses'], budget_amount, prediction['predicted_spending'],
        savings_target, monthly_income, days_elapsed, days_in_month,
        analysis['category_spending'], budget_categories
    )

    goals = db.get_goals(user_id)

    financial_context = {
        'monthly_income': monthly_income,
        'total_expenses': analysis['total_expenses'],
        'remaining_budget': budget_summary['remaining_budget'],
        'budget_amount': budget_amount,
        'savings_target': savings_target,
        'predicted_spending': prediction['predicted_spending'],
        'budget_usage_pct': budget_summary['usage_pct'],
        'days_remaining': days_remaining,
        'avg_daily_spending': analysis['avg_daily_spending'],
        'category_spending': analysis['category_spending'],
        'goals': goals,
        'risks': risks
    }

    response = get_financial_coach_response(question, financial_context)
    return jsonify({'response': response})
