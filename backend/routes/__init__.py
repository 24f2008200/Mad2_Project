from flask import Blueprint

from . import auth_routes

# def register_blueprints(app):
#     from . import lots, reservations

#     app.register_blueprint(auth_routes.bp, url_prefix="/api/auth")
#     app.register_blueprint(lots.bp, url_prefix="/lots")
#     app.register_blueprint(reservations.bp, url_prefix="/reservations")
