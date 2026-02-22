from flask import Blueprint
from app.routes.health_routes import health_bp
from app.routes.auth_routes import auth_bp
from app.routes.resume_routes import resume_bp

# Register all blueprints here
def register_blueprints(app):
    app.register_blueprint(health_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(resume_bp)