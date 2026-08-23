from functools import wraps
from flask import session, redirect, url_for, jsonify, request
from datetime import date
import calendar


def login_required(f):
    """Decorator that ensures a user is logged in."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'access_token' not in session or 'user_id' not in session:
            if request.is_json or request.path.startswith('/api/'):
                return jsonify({'error': 'Authentication required'}), 401
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated


def get_current_month_year():
    today = date.today()
    return today.year, today.month


def days_in_month(year: int, month: int) -> int:
    return calendar.monthrange(year, month)[1]


def days_elapsed_this_month() -> int:
    return date.today().day


def days_remaining_this_month() -> int:
    today = date.today()
    last = calendar.monthrange(today.year, today.month)[1]
    return last - today.day


def format_currency(amount: float) -> str:
    return f"₹{amount:,.0f}"


def safe_float(value, default=0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def safe_int(value, default=0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def month_name(month: int) -> str:
    return calendar.month_name[month]


def success_response(data: dict = None, message: str = "Success"):
    resp = {'success': True, 'message': message}
    if data:
        resp.update(data)
    return jsonify(resp)


def error_response(message: str, status: int = 400):
    return jsonify({'success': False, 'error': message}), status
