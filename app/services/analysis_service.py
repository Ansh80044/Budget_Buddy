import pandas as pd
import math


def _clean_value(val):
    """Convert NaN/NaT to None for safe JSON serialization."""
    try:
        if val is None:
            return None
        if isinstance(val, float) and math.isnan(val):
            return None
        return val
    except Exception:
        return None


def analyze_spending(transactions: list, year: int = None, month: int = None) -> dict:
    """
    Perform comprehensive spending analysis on transactions.
    Returns a dict of statistics.
    """
    if not transactions:
        return _empty_analysis()

    df = pd.DataFrame(transactions)
    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    df['amount'] = pd.to_numeric(df['amount'], errors='coerce').fillna(0)

    # Filter by month/year if given
    if year and month:
        df = df[(df['date'].dt.year == year) & (df['date'].dt.month == month)]

    expenses = df[df['type'] == 'expense'].copy()
    income_rows = df[df['type'] == 'income'].copy()

    total_expenses = float(expenses['amount'].sum())
    total_income = float(income_rows['amount'].sum())

    # Category-wise spending (exclude NaN categories)
    if not expenses.empty and 'category' in expenses.columns:
        cat_spending = (
            expenses.dropna(subset=['category'])
            .groupby('category', dropna=True)['amount']
            .sum()
            .to_dict()
        )
        cat_spending = {k: float(v) for k, v in cat_spending.items() if k and isinstance(k, str)}
    else:
        cat_spending = {}

    # Daily spending
    if not expenses.empty:
        daily = expenses.groupby(expenses['date'].dt.date)['amount'].sum()
        avg_daily = float(daily.mean()) if not daily.empty else 0.0

        # Get largest expenses — clean up NaN fields
        largest_cols = ['description', 'amount', 'date']
        if 'category' in expenses.columns:
            largest_cols.append('category')

        largest_df = expenses.nlargest(5, 'amount')[largest_cols]
        largest_expenses = []
        for _, row in largest_df.iterrows():
            exp = {
                'description': str(row.get('description', '')),
                'amount': float(row.get('amount', 0)),
                'date': str(row['date'].date()) if pd.notna(row['date']) else '',
                'category': str(row['category']) if 'category' in row.index and pd.notna(row['category']) else '',
            }
            largest_expenses.append(exp)
    else:
        avg_daily = 0.0
        largest_expenses = []

    # Weekly spending
    weekly = {}
    if not expenses.empty:
        expenses_copy = expenses.copy()
        expenses_copy['week'] = expenses_copy['date'].dt.isocalendar().week.astype(int)
        weekly_grp = expenses_copy.groupby('week')['amount'].sum()
        weekly = {int(k): float(v) for k, v in weekly_grp.items()}

    # Monthly trend (uses all passed transactions regardless of year/month filter)
    monthly_trend = {}
    try:
        all_exp_df = pd.DataFrame(transactions)
        all_exp_df['date'] = pd.to_datetime(all_exp_df['date'], errors='coerce')
        all_exp_df['amount'] = pd.to_numeric(all_exp_df['amount'], errors='coerce').fillna(0)
        all_expenses_only = all_exp_df[all_exp_df['type'] == 'expense'].copy()
        if not all_expenses_only.empty:
            all_expenses_only['month_key'] = all_expenses_only['date'].dt.to_period('M')
            monthly_grp = all_expenses_only.groupby('month_key')['amount'].sum()
            for period, amt in monthly_grp.items():
                monthly_trend[str(period)] = float(amt)
    except Exception:
        monthly_trend = {}

    return {
        'total_expenses': total_expenses,
        'total_income': total_income,
        'category_spending': cat_spending,
        'avg_daily_spending': avg_daily,
        'largest_expenses': largest_expenses,
        'weekly_spending': weekly,
        'monthly_trend': monthly_trend,
        'transaction_count': int(len(expenses))
    }


def _empty_analysis() -> dict:
    return {
        'total_expenses': 0.0,
        'total_income': 0.0,
        'category_spending': {},
        'avg_daily_spending': 0.0,
        'largest_expenses': [],
        'weekly_spending': {},
        'monthly_trend': {},
        'transaction_count': 0
    }
