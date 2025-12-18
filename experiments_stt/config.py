"""
애플리케이션 설정 관리
환경 변수와 상수를 중앙화하여 관리합니다.
"""
import os
import logging
from pathlib import Path
from typing import Set, Optional
from dotenv import load_dotenv

# .env 파일 로드
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)

# 로거 설정 (나중에 로깅이 필요할 경우를 대비)
logger = logging.getLogger(__name__)


class Config:
    """애플리케이션 설정 클래스"""

    # ==================== 기본 경로 ====================
    BASE_DIR = Path(__file__).parent.absolute()
    UPLOAD_FOLDER = BASE_DIR / "uploads"
    DATABASE_FOLDER = BASE_DIR / "database"
    DATABASE_PATH = DATABASE_FOLDER / "minute_ai.db"

    # ==================== Flask 설정 ====================
    SECRET_KEY: str = os.getenv('FLASK_SECRET_KEY', '')
    DEBUG: bool = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    PORT: int = int(os.getenv('FLASK_PORT', '5050'))

    # ==================== Firebase 설정 ====================
    FIREBASE_API_KEY: str = os.getenv('FIREBASE_API_KEY', '')
    FIREBASE_AUTH_DOMAIN: str = os.getenv('FIREBASE_AUTH_DOMAIN', '')
    FIREBASE_PROJECT_ID: str = os.getenv('FIREBASE_PROJECT_ID', '')
    FIREBASE_STORAGE_BUCKET: str = os.getenv('FIREBASE_STORAGE_BUCKET', '')
    FIREBASE_MESSAGING_SENDER_ID: str = os.getenv('FIREBASE_MESSAGING_SENDER_ID', '')
    FIREBASE_APP_ID: str = os.getenv('FIREBASE_APP_ID', '')
    FIREBASE_MEASUREMENT_ID: str = os.getenv('FIREBASE_MEASUREMENT_ID', '')

    # ==================== API 키 ====================
    OPENAI_API_KEY: str = os.getenv('OPENAI_API_KEY', '')
    GOOGLE_API_KEY: str = os.getenv('GOOGLE_API_KEY', '')
    HF_TOKEN: str = os.getenv('HUGGINGFACEHUB_API_TOKEN', '') or os.getenv('HF_TOKEN', '')
    GOOGLE_CLIENT_ID: str = os.getenv('GOOGLE_CLIENT_ID', '')
    GOOGLE_CLIENT_SECRET: str = os.getenv('GOOGLE_CLIENT_SECRET', '')

    # ==================== 파일 업로드 설정 ====================
    ALLOWED_EXTENSIONS: Set[str] = {"wav", "mp3", "m4a", "flac", "mp4", "webm"}
    MAX_FILE_SIZE_MB: int = 500
    UPLOAD_TIMEOUT_SECONDS: int = 1200  # 20분

    # ==================== STT 설정 ====================
    DEFAULT_TIME_INCREMENT_SECONDS: float = 5.0

    # ==================== 청킹(Chunking) 설정 ====================
    CHUNK_SIZE: int = 1000  # 텍스트 청크 최대 크기
    CHUNK_OVERLAP: int = 200  # 청크 중복 크기
    TIME_GAP_THRESHOLD_SECONDS: int = 60  # 화자 변경 인식 기준 (초)

    # ==================== 검색 설정 ====================
    SEARCH_RESULTS_PER_COLLECTION: int = 3  # 컬렉션당 검색 결과 수
    SEARCH_MULTIPLIER: int = 10  # 검색 결과 배수

    # ==================== 관리자 설정 ====================
    ADMIN_EMAILS: list = os.getenv('ADMIN_EMAILS', '').split(',') if os.getenv('ADMIN_EMAILS') else []

    # ==================== 로깅 설정 ====================
    LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FORMAT: str = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

    @classmethod
    def get_firebase_config(cls) -> dict:
        """Firebase 클라이언트 설정 반환 (템플릿용)"""
        return {
            'apiKey': cls.FIREBASE_API_KEY,
            'authDomain': cls.FIREBASE_AUTH_DOMAIN,
            'projectId': cls.FIREBASE_PROJECT_ID,
            'storageBucket': cls.FIREBASE_STORAGE_BUCKET,
            'messagingSenderId': cls.FIREBASE_MESSAGING_SENDER_ID,
            'appId': cls.FIREBASE_APP_ID,
            'measurementId': cls.FIREBASE_MEASUREMENT_ID
        }

    @classmethod
    def validate(cls) -> tuple[bool, list[str]]:
        """
        필수 환경 변수 검증

        Returns:
            (is_valid, missing_vars): 검증 결과와 누락된 변수 목록
        """
        required_vars = [
            ('FLASK_SECRET_KEY', cls.SECRET_KEY),
            ('FIREBASE_API_KEY', cls.FIREBASE_API_KEY),
            ('OPENAI_API_KEY', cls.OPENAI_API_KEY),
            ('GOOGLE_API_KEY', cls.GOOGLE_API_KEY),
            ('GOOGLE_CLIENT_ID', cls.GOOGLE_CLIENT_ID),
            ('GOOGLE_CLIENT_SECRET', cls.GOOGLE_CLIENT_SECRET),
        ]

        missing = [name for name, value in required_vars if not value]

        return (len(missing) == 0, missing)

    @classmethod
    def ensure_directories(cls):
        """필요한 디렉토리 생성"""
        cls.UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
        cls.DATABASE_FOLDER.mkdir(parents=True, exist_ok=True)

    @classmethod
    def print_config_status(cls, show_secrets: bool = False):
        """
        설정 로드 상태 출력

        Args:
            show_secrets: True일 경우 API 키 일부 노출 (개발 환경 전용)
        """
        print("=" * 70)
        print("📋 애플리케이션 설정 로드 상태")
        print("=" * 70)

        # 환경 파일 확인
        print(f"📂 .env 파일: {env_path}")
        print(f"   존재 여부: {'✅ 있음' if env_path.exists() else '❌ 없음'}")
        print()

        # 필수 설정 확인
        is_valid, missing = cls.validate()

        if is_valid:
            print("✅ 모든 필수 환경 변수가 로드되었습니다.")
        else:
            print("❌ 누락된 환경 변수:")
            for var in missing:
                print(f"   - {var}")

        print()

        # API 키 상태 (보안)
        def mask_key(key: str, show: bool = False) -> str:
            if not key:
                return "❌ 미설정"
            if show:
                return f"✅ 설정됨 ({key[:10]}...)"
            return "✅ 설정됨"

        print("🔑 API 키 상태:")
        print(f"   Flask Secret Key: {mask_key(cls.SECRET_KEY, show_secrets)}")
        print(f"   Firebase API Key: {mask_key(cls.FIREBASE_API_KEY, show_secrets)}")
        print(f"   OpenAI API Key:   {mask_key(cls.OPENAI_API_KEY, show_secrets)}")
        print(f"   Google API Key:   {mask_key(cls.GOOGLE_API_KEY, show_secrets)}")
        print()

        # 관리자 설정
        admin_count = len([e for e in cls.ADMIN_EMAILS if e.strip()])
        print(f"👑 관리자 이메일: {admin_count}개 설정됨")
        print()

        print("=" * 70)


# 설정 인스턴스 (싱글톤)
config = Config()

# 초기화 시 검증
is_valid, missing_vars = config.validate()
if not is_valid:
    print("⚠️  경고: 필수 환경 변수가 누락되었습니다!")
    print(f"누락된 변수: {', '.join(missing_vars)}")
    print("애플리케이션이 정상적으로 작동하지 않을 수 있습니다.")
    print()

# 필요한 디렉토리 생성
config.ensure_directories()

