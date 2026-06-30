"""
Gunicorn 프로덕션 서버 설정

실행 예시:
    gunicorn -c gunicorn_config.py wsgi:app
"""
import os
from pathlib import Path

# config에서 포트 가져오기 (환경 변수 우선)
_port = int(os.getenv("FLASK_PORT", "5000"))

# 바인드 주소 (0.0.0.0 = 모든 인터페이스)
bind = f"0.0.0.0:{_port}"

# 워커 프로세스 수 (CPU 코어 * 2 + 1 권장, 최소 1)
workers = int(os.getenv("GUNICORN_WORKERS", "4"))

# 요청 타임아웃 (초) - 업로드/STT 처리 시간 고려 (20분)
timeout = int(os.getenv("GUNICORN_TIMEOUT", "1200"))

# 워커 타입 (sync: 기본, gevent: 비동기 I/O)
worker_class = "sync"

# 로그 설정
_base_dir = Path(__file__).parent
_log_dir = _base_dir / "logs"
_log_dir.mkdir(exist_ok=True)
accesslog = str(_log_dir / "gunicorn_access.log")
errorlog = str(_log_dir / "gunicorn_error.log")
loglevel = os.getenv("LOG_LEVEL", "info").lower()

# 프로세스 이름
proc_name = "genminute"
