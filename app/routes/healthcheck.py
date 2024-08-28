# app/routes/healthcheck.py

from flask import jsonify
from . import bp

@bp.route('/healthcheck')
def healthcheck():
    return jsonify({'status': 'ok'}), 200
