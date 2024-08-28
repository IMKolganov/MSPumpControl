# app/routes/__init__.py

from flask import Blueprint

bp = Blueprint('routes', __name__)

from . import index, healthcheck