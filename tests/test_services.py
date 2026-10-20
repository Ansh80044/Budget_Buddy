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
    """Test rule-based expense categorization fallback and collision prevention."""
    from app.services.ai_service import _rule_based_categorize
    assert _rule_based_categorize("zomato dinner") == "Food & Dining"
    assert _rule_based_categorize("uber ride") == "Transportation"
    assert _rule_based_categorize("i travel by auto") == "Transportation"
    assert _rule_based_categorize("auto fare") == "Transportation"
    assert _rule_based_categorize("steam game") == "Entertainment"
    assert _rule_based_categorize("parents allowance") != "Rent & Housing"
    assert _rule_based_categorize("netflix subscription") == "Entertainment"


def test_categorize_expense_auto():
    """Test user's scenario: 'i travel by auto' correctly categorizes to Transportation."""
    from app.services.ai_service import categorize_expense
    assert categorize_expense("i travel by auto", 50) == "Transportation"
    assert categorize_expense("auto rickshaw fare", 30) == "Transportation"
    assert categorize_expense("dominos pizza", 350) == "Food & Dining"



def test_helpers_safe_float():
    """Test safe_float utility."""
    from app.utils.helpers import safe_float
    assert safe_float("100") == 100.0
    assert safe_float("invalid") == 0.0
    assert safe_float(None) == 0.0
    assert safe_float(45.5) == 45.5


def test_receipt_order_id_exclusion():
    """Ensure Order IDs, Barcodes, and phone numbers are not treated as expense amount."""
    from app.services.ai_service import _heuristic_receipt_parser, extract_receipt_data

    sample_ocr = """< Order Details Help
Order #OD338753515203686500
Placed on 28th Sep 2026
Order Delivered!
Cadbury Oreo Chocolate F... w54
6 x 41759 360
Cadbury Dairy Milk Crackl... R47
1 x 36 g
Rate your experience
Delivery details
Other HIFI MEN'S HOSTEL No.5/115
Arpit Kumar 9360054464
Lifetime Free Kotak Card"""

    # Test heuristic fallback
    h_result = _heuristic_receipt_parser(sample_ocr)
    assert h_result['amount'] < 10000, f"Order ID or Phone number extracted as amount: {h_result['amount']}"
    assert h_result['amount'] == 101.0 or h_result['amount'] in [54.0, 47.0], f"Unexpected amount: {h_result['amount']}"
    assert "338753515203686500" not in str(h_result['amount'])
    assert "9360054464" not in str(h_result['amount'])
    assert h_result['date'] == "2026-09-28"

    # Test main extract_receipt_data
    result = extract_receipt_data(sample_ocr)
    assert result['amount'] < 10000, f"Large ID extracted: {result['amount']}"
    assert "338753515203686500" not in str(result['amount'])


def test_delivery_receipt_amount_and_merchant():
    """Ensure food delivery order screenshots (like Domino's / Swiggy / Zomato) extract correct amount and merchant."""
    from app.services.ai_service import _heuristic_receipt_parser, extract_receipt_data, categorize_expense

    receipt_text = """Delivery DELIVERED
Order # 118
17 Oct 2026 19:24
(@) Capsicum & Red Paprika with Videshi Hot Sauce 5
(@) Paneer, Onion & Capsicum with Desi MakhaniS... 1
(@} Veg Parcel +2 Items 1
₹659.03 Reorder
Overall order rating How was your food?"""

    # Test heuristic fallback
    h_result = _heuristic_receipt_parser(receipt_text)
    assert h_result['amount'] == 659.03, f"Expected amount 659.03, got {h_result['amount']}"
    assert h_result['date'] == "2026-10-17"
    assert "Domino" in h_result['merchant'] or "Food Delivery" in h_result['merchant']

    # Test main extract_receipt_data
    result = extract_receipt_data(receipt_text)
    assert result['amount'] == 659.03, f"Expected amount 659.03, got {result['amount']}"
    assert result['date'] == "2026-10-17"

    # Test categorization
    category = categorize_expense(f"{result.get('merchant', '')} {result.get('description', '')}", result['amount'])
    assert category == "Food & Dining"


def test_ocr_receipt_image_if_available():
    """Test actual OCR processing on the uploaded receipt image if present."""
    from app.services.ocr_service import extract_text_from_file
    from app.services.ai_service import extract_receipt_data

    img_path = r"C:\Users\Utkarsh Singh\.gemini\antigravity-ide\brain\9e99919c-e843-4e7e-9be5-c31fc75c6c2a\.user_uploaded\media_1792518394444.jpg"
    if os.path.exists(img_path):
        ocr_text = extract_text_from_file(img_path)
        assert len(ocr_text) > 30, "OCR should extract readable text from receipt image"
        parsed = extract_receipt_data(ocr_text)
        assert parsed['amount'] == 659.03, f"OCR extraction failed to get 659.03, got {parsed['amount']}"
        assert parsed['date'] == "2026-10-17", f"Expected date 2026-10-17, got {parsed['date']}"


