from datetime import date
import calendar


def predict_monthly_spending(avg_daily_spending: float, current_spending: float, year: int = None, month: int = None) -> dict:
    """
    Predict total monthly spending using:
    Predicted = Current Spending + (Avg Daily Spending × Remaining Days)
    """
    today = date.today()
    if year is None:
        year = today.year
    if month is None:
        month = today.month

    days_in_month = calendar.monthrange(year, month)[1]

    if year == today.year and month == today.month:
        days_elapsed = today.day
        days_remaining = days_in_month - today.day
    elif (year, month) < (today.year, today.month):
        # Past month — prediction is actual spending
        days_elapsed = days_in_month
        days_remaining = 0
    else:
        # Future month
        days_elapsed = 0
        days_remaining = days_in_month

    predicted = current_spending + (avg_daily_spending * days_remaining)

    return {
        'predicted_spending': round(predicted, 2),
        'current_spending': round(current_spending, 2),
        'avg_daily_spending': round(avg_daily_spending, 2),
        'days_remaining': days_remaining,
        'days_elapsed': days_elapsed,
        'days_in_month': days_in_month
    }


def try_ml_prediction(historical_monthly: dict, current_spending: float, avg_daily: float, year: int, month: int) -> dict:
    """
    Attempt ML-based prediction if enough historical data exists (6+ months).
    Falls back to simple prediction otherwise.
    """
    base = predict_monthly_spending(avg_daily, current_spending, year, month)

    if len(historical_monthly) < 6:
        base['method'] = 'simple'
        return base

    try:
        import numpy as np
        from sklearn.linear_model import LinearRegression

        # Prepare data: x = month index, y = spending
        sorted_months = sorted(historical_monthly.keys())
        amounts = [historical_monthly[m] for m in sorted_months]

        X = np.array(range(len(amounts))).reshape(-1, 1)
        y = np.array(amounts)

        model = LinearRegression()
        model.fit(X, y)

        next_idx = len(amounts)
        ml_prediction = float(model.predict([[next_idx]])[0])

        # Blend ML with simple prediction
        blended = (ml_prediction * 0.4 + base['predicted_spending'] * 0.6)
        base['predicted_spending'] = round(max(blended, current_spending), 2)
        base['method'] = 'ml_blended'
    except Exception as e:
        print(f"ML prediction failed, using simple: {e}")
        base['method'] = 'simple'

    return base
