import os
import calendar
from app.services import local_db

_client = None


def is_supabase_configured() -> bool:
    url = os.environ.get('SUPABASE_URL', '').strip()
    key = os.environ.get('SUPABASE_KEY', '').strip()
    return bool(url and key and not url.startswith('https://your-project') and not url.startswith('your_supabase') and not 'dummy' in url)


def get_client():
    global _client
    if _client is None:
        if not is_supabase_configured():
            return None
        try:
            from supabase import create_client
            url = os.environ.get('SUPABASE_URL', '').strip()
            key = os.environ.get('SUPABASE_KEY', '').strip()
            _client = create_client(url, key)
        except Exception as e:
            print(f"Supabase client initialization notice: {e}. Operating in local SQLite mode.")
            _client = None
    return _client


# ──────────────────────────────────────────────
# Auth helpers
# ──────────────────────────────────────────────

class AuthResponse:
    def __init__(self, user_id, email, token):
        self.user = type('User', (), {'id': user_id, 'email': email})()
        self.session = type('Session', (), {'access_token': token})()


def sign_up(email: str, password: str, name: str):
    client = get_client()
    if client:
        try:
            resp = client.auth.sign_up({'email': email, 'password': password})
            if resp.user:
                try:
                    client.table('profiles').insert({
                        'id': resp.user.id,
                        'name': name,
                        'monthly_income': 15000.0
                    }).execute()
                except Exception:
                    pass
            return resp
        except Exception as e:
            print(f"Supabase sign_up error, falling back to local: {e}")
    # Local fallback
    data = local_db.local_sign_up(email, password, name)
    return AuthResponse(data['user']['id'], data['user']['email'], data['session']['access_token'])


def sign_in(email: str, password: str):
    client = get_client()
    if client:
        try:
            return client.auth.sign_in_with_password({'email': email, 'password': password})
        except Exception as e:
            print(f"Supabase sign_in error, checking local DB: {e}")
    # Local fallback
    data = local_db.local_sign_in(email, password)
    return AuthResponse(data['user']['id'], data['user']['email'], data['session']['access_token'])


def sign_out(access_token: str = None):
    client = get_client()
    if client:
        try:
            client.auth.sign_out()
        except Exception:
            pass


def get_user(access_token: str):
    client = get_client()
    if client:
        try:
            return client.auth.get_user(access_token)
        except Exception:
            pass
    return None


# ──────────────────────────────────────────────
# Profile
# ──────────────────────────────────────────────

def get_profile(user_id: str):
    client = get_client()
    if client:
        try:
            resp = client.table('profiles').select('*').eq('id', user_id).single().execute()
            if resp.data:
                return resp.data
        except Exception as e:
            pass
    return local_db.local_get_profile(user_id)


def update_profile(user_id: str, data: dict):
    client = get_client()
    if client:
        try:
            return client.table('profiles').update(data).eq('id', user_id).execute()
        except Exception as e:
            pass
    return local_db.local_update_profile(user_id, data)


# ──────────────────────────────────────────────
# Transactions
# ──────────────────────────────────────────────

def get_transactions(user_id: str, limit: int = 500):
    client = get_client()
    if client:
        try:
            resp = (
                client.table('transactions')
                .select('*')
                .eq('user_id', user_id)
                .order('date', desc=True)
                .limit(limit)
                .execute()
            )
            if resp.data is not None:
                return resp.data
        except Exception as e:
            pass
    return local_db.local_get_transactions(user_id, limit)


def get_transactions_by_month(user_id: str, year: int, month: int):
    client = get_client()
    if client:
        try:
            start = f"{year}-{month:02d}-01"
            last_day = calendar.monthrange(year, month)[1]
            end = f"{year}-{month:02d}-{last_day}"
            resp = (
                client.table('transactions')
                .select('*')
                .eq('user_id', user_id)
                .gte('date', start)
                .lte('date', end)
                .order('date', desc=True)
                .execute()
            )
            if resp.data is not None:
                return resp.data
        except Exception as e:
            pass
    return local_db.local_get_transactions_by_month(user_id, year, month)


def create_transaction(data: dict):
    client = get_client()
    if client:
        try:
            return client.table('transactions').insert(data).execute()
        except Exception as e:
            pass
    return local_db.local_create_transaction(data)


def update_transaction(transaction_id: str, user_id: str, data: dict):
    client = get_client()
    if client:
        try:
            return client.table('transactions').update(data).eq('id', transaction_id).eq('user_id', user_id).execute()
        except Exception as e:
            pass
    return local_db.local_update_transaction(transaction_id, user_id, data)


def delete_transaction(transaction_id: str, user_id: str):
    client = get_client()
    if client:
        try:
            return client.table('transactions').delete().eq('id', transaction_id).eq('user_id', user_id).execute()
        except Exception as e:
            pass
    return local_db.local_delete_transaction(transaction_id, user_id)


def get_transaction(transaction_id: str, user_id: str):
    client = get_client()
    if client:
        try:
            resp = (
                client.table('transactions')
                .select('*')
                .eq('id', transaction_id)
                .eq('user_id', user_id)
                .single()
                .execute()
            )
            if resp.data:
                return resp.data
        except Exception as e:
            pass
    return local_db.local_get_transaction(transaction_id, user_id)


# ──────────────────────────────────────────────
# Budgets
# ──────────────────────────────────────────────

def get_budget(user_id: str, year: int, month: int):
    client = get_client()
    if client:
        try:
            resp = (
                client.table('budgets')
                .select('*, budget_categories(*)')
                .eq('user_id', user_id)
                .eq('year', year)
                .eq('month', month)
                .execute()
            )
            if resp.data:
                return resp.data[0]
        except Exception as e:
            pass
    return local_db.local_get_budget(user_id, year, month)


def create_budget(data: dict):
    client = get_client()
    if client:
        try:
            return client.table('budgets').insert(data).execute()
        except Exception as e:
            pass
    return local_db.local_create_budget(data)


def update_budget(budget_id: str, user_id: str, data: dict):
    client = get_client()
    if client:
        try:
            return client.table('budgets').update(data).eq('id', budget_id).eq('user_id', user_id).execute()
        except Exception as e:
            pass
    return local_db.local_update_budget(budget_id, user_id, data)


def upsert_budget_category(budget_id: str, category: str, limit_amount: float):
    client = get_client()
    if client:
        try:
            existing = (
                client.table('budget_categories')
                .select('id')
                .eq('budget_id', budget_id)
                .eq('category', category)
                .execute()
            )
            if existing.data:
                return client.table('budget_categories').update({'limit_amount': limit_amount}).eq('id', existing.data[0]['id']).execute()
            else:
                return client.table('budget_categories').insert({'budget_id': budget_id, 'category': category, 'limit_amount': limit_amount}).execute()
        except Exception as e:
            pass
    return local_db.local_upsert_budget_category(budget_id, category, limit_amount)


def delete_budget_category(category_id: str):
    client = get_client()
    if client:
        try:
            return client.table('budget_categories').delete().eq('id', category_id).execute()
        except Exception as e:
            pass


# ──────────────────────────────────────────────
# Savings Goals
# ──────────────────────────────────────────────

def get_goals(user_id: str):
    client = get_client()
    if client:
        try:
            resp = client.table('savings_goals').select('*').eq('user_id', user_id).execute()
            if resp.data is not None:
                return resp.data
        except Exception as e:
            pass
    return local_db.local_get_goals(user_id)


def get_goal(goal_id: str, user_id: str):
    client = get_client()
    if client:
        try:
            resp = client.table('savings_goals').select('*').eq('id', goal_id).eq('user_id', user_id).single().execute()
            if resp.data:
                return resp.data
        except Exception as e:
            pass
    return local_db.local_get_goal(goal_id, user_id)


def create_goal(data: dict):
    client = get_client()
    if client:
        try:
            return client.table('savings_goals').insert(data).execute()
        except Exception as e:
            pass
    return local_db.local_create_goal(data)


def update_goal(goal_id: str, user_id: str, data: dict):
    client = get_client()
    if client:
        try:
            return client.table('savings_goals').update(data).eq('id', goal_id).eq('user_id', user_id).execute()
        except Exception as e:
            pass
    return local_db.local_update_goal(goal_id, user_id, data)


def delete_goal(goal_id: str, user_id: str):
    client = get_client()
    if client:
        try:
            return client.table('savings_goals').delete().eq('id', goal_id).eq('user_id', user_id).execute()
        except Exception as e:
            pass
    return local_db.local_delete_goal(goal_id, user_id)
