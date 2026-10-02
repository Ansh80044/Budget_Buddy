from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from app.utils.helpers import login_required, safe_float
from app.services.ocr_service import extract_text_from_image
from app.services.ai_service import extract_receipt_data, categorize_expense, EXPENSE_CATEGORIES
from app.services import supabase_service as db
from datetime import date
import random

receipt_bp = Blueprint('receipt', __name__)


@receipt_bp.route('/receipt')
@login_required
def receipt():
    return render_template('receipt.html', categories=EXPENSE_CATEGORIES, today=str(date.today()))


@receipt_bp.route('/receipt/scan', methods=['POST'])
@login_required
def scan_receipt():
    if 'receipt_image' not in request.files:
        return jsonify({'error': 'No image uploaded'}), 400

    file = request.files['receipt_image']
    if not file or file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    # Read image bytes
    image_bytes = file.read()

    # OCR
    ocr_text = extract_text_from_image(image_bytes)

    # Check if OCR could extract text
    if not ocr_text:
        return jsonify({
            'error': 'Could not extract readable text from the receipt image. Please ensure the receipt is well-lit and clearly focused, or add the transaction manually.'
        }), 400

    # AI parse with Groq / fallback
    extracted = extract_receipt_data(ocr_text)
    merchant = extracted.get('merchant', '')
    amount = safe_float(extracted.get('amount', 0))
    # Safeguard against product IDs or tracking numbers slipping through
    if amount > 200000:
        amount = 0.0
    receipt_date = extracted.get('date', str(date.today()))
    description = extracted.get('description', merchant)
    category = categorize_expense(f"{merchant} {description}", amount)

    return jsonify({
        'ocr_text': ocr_text,
        'merchant': merchant,
        'amount': amount,
        'date': receipt_date,
        'description': description or merchant,
        'category': category,
        'categories': EXPENSE_CATEGORIES
    })


@receipt_bp.route('/receipt/save', methods=['POST'])
@login_required
def save_receipt_expense():
    user_id = session['user_id']
    description = request.form.get('description', '').strip()
    amount = safe_float(request.form.get('amount', 0))
    tx_date = request.form.get('date', str(date.today()))
    category = request.form.get('category', 'Other')

    if not description or amount <= 0:
        flash('Invalid expense data. Please enter a valid description and amount.', 'error')
        return redirect(url_for('receipt.receipt'))

    if amount > 500000:
        flash('Expense amount is unusually high (> ₹5,00,000). Please verify the actual price before saving.', 'error')
        return redirect(url_for('receipt.receipt'))

    data = {
        'user_id': user_id,
        'type': 'expense',
        'amount': amount,
        'description': description,
        'date': tx_date,
        'category': category,
        'source': 'receipt'
    }
    try:
        db.create_transaction(data)
        flash('Receipt expense saved successfully to transactions!', 'success')
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')

    return redirect(url_for('transactions.transactions'))
