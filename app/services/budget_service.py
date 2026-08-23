from datetime import date
import calendar


def generate_budget_recommendation(monthly_income: float, savings_target: float,
                                    category_spending: dict, prev_months_avg: float = None) -> dict:
    """
    Recommend a budget based on:
    - Monthly income
    - Savings target
    - Historical category spending
    """
    available = monthly_income - savings_target
    if available < 0:
        available = monthly_income * 0.8  # safety fallback

    total_cat_spending = sum(category_spending.values()) if category_spending else 0

    category_limits = {}
    if category_spending and total_cat_spending > 0:
        for cat, amount in category_spending.items():
            # Scale category limits proportionally to available budget
            proportion = amount / total_cat_spending
            recommended = round(proportion * available, 0)
            category_limits[cat] = recommended
    else:
        # Default distribution for college students (India)
        default_pct = {
            "Food & Dining": 0.30,
            "Groceries": 0.10,
            "Transportation": 0.15,
            "Entertainment": 0.10,
            "Education": 0.15,
            "Shopping": 0.10,
            "Utilities": 0.05,
            "Personal Care": 0.05,
        }
        for cat, pct in default_pct.items():
            category_limits[cat] = round(available * pct, 0)

    return {
        'recommended_budget': round(available, 2),
        'monthly_income': round(monthly_income, 2),
        'savings_target': round(savings_target, 2),
        'category_limits': category_limits,
        'notes': _generate_budget_notes(monthly_income, savings_target, available)
    }


def _generate_budget_notes(income: float, savings: float, available: float) -> list:
    notes = []
    savings_pct = (savings / income * 100) if income > 0 else 0
    if savings_pct >= 20:
        notes.append(f"Excellent! You're targeting {savings_pct:.0f}% savings — well above the recommended 20%.")
    elif savings_pct >= 10:
        notes.append(f"Good savings target of {savings_pct:.0f}%. Try to increase to 20% if possible.")
    else:
        notes.append(f"Your savings target is {savings_pct:.0f}%. Consider increasing it for financial security.")
    return notes


def detect_budget_risks(current_spending: float, budget_amount: float,
                         predicted_spending: float, savings_target: float,
                         monthly_income: float, days_elapsed: int,
                         days_in_month: int, category_spending: dict,
                         budget_categories: list) -> list:
    """
    Detect predefined budget risk conditions and return list of risk messages.
    """
    risks = []
    if budget_amount <= 0:
        return risks

    usage_pct = (current_spending / budget_amount * 100) if budget_amount > 0 else 0
    pct_month_elapsed = (days_elapsed / days_in_month * 100) if days_in_month > 0 else 0

    # Risk 1: Rapid budget usage
    if usage_pct >= 80 and pct_month_elapsed < 70:
        risks.append(f"⚡ Rapid spending: {usage_pct:.0f}% of budget used with {days_in_month - days_elapsed} days remaining.")

    # Risk 2: Predicted budget overflow
    if predicted_spending > budget_amount:
        overflow = predicted_spending - budget_amount
        risks.append(f"🔮 Prediction alert: Estimated to overspend by ₹{overflow:,.0f} this month.")

    # Risk 3: Savings target risk
    potential_savings = monthly_income - predicted_spending
    if potential_savings < savings_target and savings_target > 0:
        shortfall = savings_target - potential_savings
        risks.append(f"🎯 Savings risk: Predicted to fall ₹{shortfall:,.0f} short of your savings target.")

    # Risk 4: Category limit violations
    cat_limits = {bc['category']: bc['limit_amount'] for bc in (budget_categories or [])}
    for cat, spent in category_spending.items():
        limit = cat_limits.get(cat)
        if limit and spent > limit:
            over = spent - limit
            risks.append(f"📊 {cat} over limit: Spent ₹{spent:,.0f} vs limit ₹{limit:,.0f} (₹{over:,.0f} over).")

    # Risk 5: General overspending (> 100%)
    if usage_pct > 100:
        risks.append(f"🚨 Over budget: You've exceeded your monthly budget by ₹{current_spending - budget_amount:,.0f}.")

    return risks


def get_budget_summary(current_spending: float, budget_amount: float, monthly_income: float) -> dict:
    """Returns budget usage summary metrics."""
    remaining = budget_amount - current_spending
    usage_pct = (current_spending / budget_amount * 100) if budget_amount > 0 else 0
    return {
        'budget_amount': round(budget_amount, 2),
        'current_spending': round(current_spending, 2),
        'remaining_budget': round(remaining, 2),
        'usage_pct': round(usage_pct, 1),
        'is_over_budget': current_spending > budget_amount
    }
