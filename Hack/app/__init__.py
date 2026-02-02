from flask import Flask
import os
from . import db as dbmod


def create_app() -> Flask:

	app = Flask(__name__)
	app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024  # 5 MB upload limit
	app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-change-me")
	app.config["DATABASE"] = os.environ.get("DATABASE", os.path.join(os.getcwd(), "resume_analyzer.db"))

	from .routes import bp as main_bp
	app.register_blueprint(main_bp)

	# Initialize database
	with app.app_context():
		dbmod.initialize_database(app.config["DATABASE"])

	return app


