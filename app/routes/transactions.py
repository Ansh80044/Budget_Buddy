from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from app.utils.helpers import login_required, safe_float, success_response, error_response
from app.services import supabase_service as db
from app.services.ai_service import categorize_expense, EXPENSE_CATEGORIES
from datetime import date

transactions_bp = Blueprint('transactions', __name__)


@transactions_bp.route('/transactions')
@login_required
def transactions():
    user_id = session['user_id']
    all_tx = db.get_transactions(user_id, limit=500)
    return render_template('transactions.html',
        transactions=all_tx,
        categories=EXPENSE_CATEGORIES,
        today=str(date.today())
    )


@transactions_bp.route('/transactions/add', methods=['POST'])
@login_required
def add_transaction():
    user_id = session['user_id']
    tx_type = request.form.get('type', 'expense')
    amount = safe_float(request.form.get('amount'))
    description = request.form.get('description', '').strip()
    tx_date = request.form.get('date', str(date.today()))
    category = request.form.get('category', '').strip()
    source = request.form.get('source', 'manual')

    if not description or amount <= 0:
        flash('Please provide a valid description and amount.', 'error')
        return redirect(url_for('transactions.transactions'))

    # Auto-categorize if no category provided and it's an expense
    if tx_type == 'expense' and not category:
        category = categorize_expense(description, amount)

    data = {
        'user_id': user_id,
        'type': tx_type,
        'amount': amount,
        'description': description,
        'date': tx_date,
        'category': category if tx_type == 'expense' else None,
        'source': source,
    }
    if tx_type == 'income':
        data['source_label'] = request.form.get('source_label', 'Income')

    try:
        db.create_transaction(data)
        flash('Transaction added successfully!', 'success')
    except Exception as e:
        flash(f'Error adding transaction: {str(e)}', 'error')

    return redirect(url_for('transactions.transactions'))


@transactions_bp.route('/transactions/<transaction_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_transaction(transaction_id):
    user_id = session['user_id']
    tx = db.get_transaction(transaction_id, user_id)

    if not tx:
        flash('Transaction not found.', 'error')
        return redirect(url_for('transactions.transactions'))

    if request.method == 'POST':
        amount = safe_float(request.form.get('amount'))
        description = request.form.get('description', '').strip()
        tx_date = request.form.get('date', str(date.today()))
        category = request.form.get('category', '').strip()

        update_data = {
            'amount': amount,
            'description': description,
            'date': tx_date,
            'category': category if tx['type'] == 'expense' else None,
        }
        try:
            db.update_transaction(transaction_id, user_id, update_data)
            flash('Transaction updated!', 'success')
        except Exception as e:
            flash(f'Error: {str(e)}', 'error')
        return redirect(url_for('transactions.transactions'))

    return render_template('transactions.html',
        edit_tx=tx,
        transactions=db.get_transactions(user_id, limit=500),
        categories=EXPENSE_CATEGORIES,
        today=str(date.today())
    )


@transactions_bp.route('/transactions/<transaction_id>/delete', methods=['POST'])
@login_required
def delete_transaction(transaction_id):
    user_id = session['user_id']
    try:
        db.delete_transaction(transaction_id, user_id)
        flash('Transaction deleted.', 'success')
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
    return redirect(url_for('transactions.transactions'))


@transactions_bp.route('/api/categorize', methods=['POST'])
@login_required
def api_categorize():
    data = request.get_json()
    description = data.get('description', '')
    amount = safe_float(data.get('amount', 0))
    category = categorize_expense(description, amount)
    return success_response({'category': category})


@transactions_bp.route('/api/transactions', methods=['GET'])
@login_required
def api_get_transactions():
    user_id = session['user_id']
    transactions = db.get_transactions(user_id, limit=500)
    return jsonify({'transactions': transactions})
