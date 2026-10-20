import pytest
from app import create_app
from app.services import local_db


@pytest.fixture
def logged_in_client():
    app = create_app()
    app.config['TESTING'] = True
    client = app.test_client()
    
    conn = local_db.get_db()
    c = conn.cursor()
    row = c.execute("SELECT id, email, name FROM profiles LIMIT 1").fetchone()
    conn.close()
    
    user_id = row['id'] if row else "test-user-id"
    email = row['email'] if row else "test@college.edu"
    name = row['name'] if row else "Test Student"

    with client.session_transaction() as sess:
        sess['user_id'] = user_id
        sess['user_email'] = email
        sess['user_name'] = name
        sess['access_token'] = f"local-token-{user_id}"

    return client


def test_coach_page_loads(logged_in_client):
    res = logged_in_client.get('/coach')
    assert res.status_code == 200
    assert b"AI Financial Coach" in res.data


def test_coach_ask_api_success(logged_in_client):
    res = logged_in_client.post('/api/coach/ask', json={'question': 'Where am I spending the most?'})
    assert res.status_code == 200
    data = res.get_json()
    assert 'response' in data
    assert len(data['response']) > 10


def test_coach_ask_api_empty_validation(logged_in_client):
    res = logged_in_client.post('/api/coach/ask', json={'question': '   '})
    assert res.status_code == 400
    data = res.get_json()
    assert 'error' in data


def test_simulator_page_loads(logged_in_client):
    res = logged_in_client.get('/simulator')
    assert res.status_code == 200
    assert b"What-If Simulator" in res.data


def test_simulator_run_purchase(logged_in_client):
    res = logged_in_client.post('/api/simulator/run', json={
        'scenario': 'purchase',
        'amount': 500,
        'description': 'Textbook'
    })
    assert res.status_code == 200
    data = res.get_json()
    assert data['scenario'] == 'purchase'
    assert 'before' in data
    assert 'after' in data
    assert data['after']['expenses'] == data['before']['expenses'] + 500
    assert data['after']['predicted_spending'] == data['before']['predicted_spending'] + 500


def test_simulator_run_reduce_category(logged_in_client):
    res = logged_in_client.post('/api/simulator/run', json={
        'scenario': 'reduce_category',
        'category': 'Food & Dining',
        'reduce_by': 200
    })
    assert res.status_code == 200
    data = res.get_json()
    assert data['scenario'] == 'reduce_category'
    assert 'before' in data
    assert 'after' in data
    assert data['after']['expenses'] <= data['before']['expenses']


def test_simulator_run_increase_income(logged_in_client):
    res = logged_in_client.post('/api/simulator/run', json={
        'scenario': 'increase_income',
        'amount': 3000
    })
    assert res.status_code == 200
    data = res.get_json()
    assert data['after']['income'] == data['before']['income'] + 3000
    assert data['after']['balance'] == data['before']['balance'] + 3000


def test_simulator_run_savings_boost(logged_in_client):
    res = logged_in_client.post('/api/simulator/run', json={
        'scenario': 'savings_boost',
        'amount': 1000
    })
    assert res.status_code == 200
    data = res.get_json()
    assert data['scenario'] == 'savings_boost'
    assert 'has_savings_target' in data


def test_simulator_run_change_budget(logged_in_client):
    res = logged_in_client.post('/api/simulator/run', json={
        'scenario': 'change_budget',
        'amount': 2500
    })
    assert res.status_code == 200
    data = res.get_json()
    assert data['scenario'] == 'change_budget'
    assert data['after']['remaining_budget'] == 2500 - data['after']['expenses']


def test_api_categorize_auto_travel(logged_in_client):
    """Verify /api/categorize categorizes 'i travel by auto' as Transportation."""
    res = logged_in_client.post('/api/categorize', json={'description': 'i travel by auto', 'amount': 50})
    assert res.status_code == 200
    data = res.get_json()
    assert data['success'] is True
    assert data['category'] == 'Transportation'


def test_add_transaction_auto_categorizes_auto_travel(logged_in_client):
    """Verify submitting a transaction with no category auto-assigns Transportation."""
    res = logged_in_client.post('/transactions/add', data={
        'type': 'expense',
        'amount': '60',
        'description': 'i travel by auto to college',
        'category': '',
        'date': '2026-09-28'
    }, follow_redirects=True)
    assert res.status_code == 200
    assert b"Transaction added successfully!" in res.data
    # Clean up test transaction from local DB
    from app.services import local_db
    conn = local_db.get_db()
    c = conn.cursor()
    c.execute("DELETE FROM transactions WHERE description = 'i travel by auto to college'")
    conn.commit()
    conn.close()

