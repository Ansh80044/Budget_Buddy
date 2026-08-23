from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from app.services import supabase_service as db
from app.utils.helpers import safe_float

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard.dashboard'))
    return render_template('index.html')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('dashboard.dashboard'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        try:
            resp = db.sign_in(email, password)
            if resp.user and resp.session:
                session['user_id'] = resp.user.id
                session['access_token'] = resp.session.access_token
                session['user_email'] = resp.user.email
                profile = db.get_profile(resp.user.id)
                session['user_name'] = profile.get('name', email.split('@')[0]) if profile else email.split('@')[0]
                return redirect(url_for('dashboard.dashboard'))
            else:
                flash('Invalid email or password.', 'error')
        except Exception as e:
            flash(f'Login failed: {str(e)}', 'error')

    return render_template('login.html')


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for('dashboard.dashboard'))

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        monthly_income = safe_float(request.form.get('monthly_income', 0))

        if not name or not email or not password:
            flash('All fields are required.', 'error')
            return render_template('register.html')

        try:
            resp = db.sign_up(email, password, name)
            if resp.user:
                # Update monthly income in profile
                db.update_profile(resp.user.id, {'monthly_income': monthly_income, 'name': name})
                flash('Registration successful! Please log in.', 'success')
                return redirect(url_for('auth.login'))
            else:
                flash('Registration failed. Try a different email.', 'error')
        except Exception as e:
            flash(f'Registration error: {str(e)}', 'error')

    return render_template('register.html')


@auth_bp.route('/logout')
def logout():
    try:
        token = session.get('access_token')
        if token:
            db.sign_out(token)
    except Exception:
        pass
    session.clear()
    return redirect(url_for('auth.index'))
