# app/routes/index.py

from flask import jsonify
from flask import send_from_directory
import os
from . import bp

@bp.route('/')
def index():
    response = jsonify({'message': 'Welcome to the Pump Service'})
    return response

@bp.route('/favicon.ico')
def favicon():
    return send_from_directory('static', 'favicon.ico')
