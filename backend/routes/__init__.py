from flask import Blueprint

def register_blueprints(app):
    from . import auth, lots, reservations

    app.register_blueprint(auth.bp, url_prefix="/api/auth")
    app.register_blueprint(lots.bp, url_prefix="/api/lots")
    app.register_blueprint(reservations.bp, url_prefix="/api/reservations")
