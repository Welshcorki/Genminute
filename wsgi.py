"""
WSGI 진입점 (Gunicorn 프로덕션 서버용)

실행 예시:
    gunicorn -c gunicorn_config.py wsgi:app
"""
from app import app
