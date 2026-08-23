"""
Budget Buddy — Basic Tests
Run with: python -m pytest tests/
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


def test_analysis_service_empty():
    """Test analysis service with no transactions."""
    from app.services.analysis_service import analyze_spending
    result = analyze_spending([])
    assert result['total_expenses'] == 0.0
    assert result['total_income'] == 0.0
    assert result['category_spending'] == {}


def test_analysis_service_with_data():
    """Test analysis service with sample transactions."""
    from app.services.analysis_service import analyze_spending
    transactions = [
        {'type': 'income', 'amount': '10000', 'date': '2024-01-15', 'description': 'Salary', 'category': None},
        {'type': 'expense', 'amount': '450', 'date': '2024-01-20', 'description': "Domino's", 'category': 'Food & Dining'},
        {'type': 'expense', 'amount': '250', 'date': '2024-01-21', 'description': 'Uber', 'category': 'Transportation'},
    ]
    result = analyze_spending(transactions)
    assert result['total_income'] == 10000.0
    assert result['total_expenses'] == 700.0
    assert 'Food & Dining' in result['category_spending']


def test_prediction_service():
    """Test spending prediction calculation."""
    from app.services.prediction_service import predict_monthly_spending
    result = predict_monthly_spending(avg_daily_spending=200, current_spending=3000, year=2024, month=8)
    assert result['predicted_spending'] >= 3000
    assert 'days_remaining' in result
    assert 'method' not in result  # basic predict doesn't have method key


def test_budget_service_recommendation():
    """Test budget recommendation generation."""
    from app.services.budget_service import generate_budget_recommendation
    rec = generate_budget_recommendation(
        monthly_income=10000,
        savings_target=2000,
        category_spending={'Food & Dining': 2000, 'Transportation': 1000}
    )
    assert rec['recommended_budget'] == 8000.0
    assert 'category_limits' in rec
    assert len(rec['category_limits']) > 0


def test_budget_risk_detection_no_budget():
    """Test risk detection with no budget returns empty list."""
    from app.services.budget_service import detect_budget_risks
    risks = detect_budget_risks(0, 0, 0, 0, 0, 0, 30, {}, [])
    assert risks == []


def test_rule_based_categorization():
    """Test rule-based expense categorization fallback."""
    from app.services.ai_service import _rule_based_categorize
    assert _rule_based_categorize("zomato dinner") == "Food & Dining"
    assert _rule_based_categorize("uber ride") == "Transportation"
    assert _rule_based_categorize("netflix subscription") == "Entertainment"


def test_helpers_safe_float():
    """Test safe_float utility."""
    from app.utils.helpers import safe_float
    assert safe_float("100") == 100.0
    assert safe_float("invalid") == 0.0
    assert safe_float(None) == 0.0
    assert safe_float(45.5) == 45.5
