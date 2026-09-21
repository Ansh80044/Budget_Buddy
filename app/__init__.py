from flask import Flask
from dotenv import load_dotenv
import os

load_dotenv()


def create_app():
    app = Flask(__name__)
    app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'dev-secret-key-change-in-production')

    # Register blueprints
    from app.routes.auth import auth_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.transactions import transactions_bp
    from app.routes.budget import budget_bp
    from app.routes.reports import reports_bp
    from app.routes.goals import goals_bp
    from app.routes.receipt import receipt_bp
    from app.routes.ai import ai_bp
    from app.routes.simulator import simulator_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(transactions_bp)
    app.register_blueprint(budget_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(goals_bp)
    app.register_blueprint(receipt_bp)
    app.register_blueprint(ai_bp)
    app.register_blueprint(simulator_bp)

    return app
