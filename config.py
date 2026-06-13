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
    
    # 사용할 데이터베이스 타입: 'sqlite' 또는 'supabase' (기본값: supabase)
    DB_TYPE: str = os.getenv('DB_TYPE', 'supabase').lower()
    
    FRONTEND_BUILD_DIR = BASE_DIR / "frontend" / "dist"  # React 빌드 파일 경로

    # ==================== Flask 설정 ====================
    SECRET_KEY: str = os.getenv('FLASK_SECRET_KEY', '')
    DEBUG: bool = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    PORT: int = int(os.getenv('FLASK_PORT', '5000'))
    
    # CORS 허용 오리진 (쉼표로 구분, 기본값: 개발 환경)
    _allowed_origins_str = os.getenv('ALLOWED_ORIGINS', 'http://localhost:5173,http://127.0.0.1:5173')
    ALLOWED_ORIGINS: list[str] = [origin.strip() for origin in _allowed_origins_str.split(',') if origin.strip()]
    logger.debug(f"ALLOWED_ORIGINS initialized: {ALLOWED_ORIGINS} (count: {len(ALLOWED_ORIGINS)})")

    # 프론트엔드 베이스 URL (OAuth 콜백 후 리다이렉트 대상)
    # 미설정 시 첫 번째 허용 오리진으로 폴백 (개발 환경: http://localhost:5173)
    FRONTEND_URL: str = os.getenv('FRONTEND_URL', '') or (ALLOWED_ORIGINS[0] if ALLOWED_ORIGINS else 'http://localhost:5173')

    # ==================== Supabase 설정 ====================
    SUPABASE_URL: str = os.getenv('SUPABASE_URL', '')
    SUPABASE_ANON_KEY: str = os.getenv('SUPABASE_ANON_KEY', '')
    SUPABASE_SERVICE_ROLE_KEY: str = os.getenv('SUPABASE_SERVICE_ROLE_KEY', '')

    # ==================== API 키 ====================
    OPENAI_API_KEY: str = os.getenv('OPENAI_API_KEY', '')
    GOOGLE_API_KEY: str = os.getenv('GOOGLE_API_KEY', '')
    
    # [Merged] Hugging Face Token (Local STT)
    HF_TOKEN: str = os.getenv('HUGGINGFACEHUB_API_TOKEN', '') or os.getenv('HF_TOKEN', '')
    
    # ==================== Google Calendar 연동 ====================
    GOOGLE_CLIENT_ID: str = os.getenv('GOOGLE_CLIENT_ID', '')
    GOOGLE_CLIENT_SECRET: str = os.getenv('GOOGLE_CLIENT_SECRET', '')
    # Google Cloud Console 프로젝트 ID (캘린더 OAuth에 사용, 선택 필드)
    GOOGLE_PROJECT_ID: str = os.getenv('GOOGLE_PROJECT_ID', '')


    # ==================== 파일 업로드 설정 ====================
    ALLOWED_EXTENSIONS: Set[str] = {"wav", "mp3", "m4a", "flac", "mp4", "webm"}
    MAX_FILE_SIZE_MB: int = 500
    UPLOAD_TIMEOUT_SECONDS: int = 1200  # 20분

    # ==================== STT 엔진 설정 ====================
    # "local" : faster-whisper + pyannote (GPU 권장, 무료)
    # "gemini": Gemini API STT + 화자분리 (GPU 불필요, API 비용 발생)
    STT_ENGINE: str = os.getenv('STT_ENGINE', 'local')

    # Gemini 모델명 (요약, 회의록, 마인드맵, 챗봇 등에 공통 사용)
    GEMINI_MODEL: str = os.getenv('GEMINI_MODEL', 'gemini-3-flash')

    # ==================== 임베딩 모델 설정 ====================
    # 벡터 DB(ChromaDB) 임베딩에 사용하는 모델.
    # ⚠️ 기존 벡터와 차원이 호환되어야 하므로, 모델 교체 시 전체 재임베딩이 필요하다.
    # 기본값은 현재 코드가 의존하던 OpenAIEmbeddings 라이브러리 기본 모델과 동일하게 고정.
    EMBEDDING_MODEL: str = os.getenv('EMBEDDING_MODEL', 'text-embedding-ada-002')

    # ==================== STT 기타 설정 ====================
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
    def validate(cls) -> tuple[bool, list[str]]:
        """
        필수 환경 변수 검증

        필수: FLASK_SECRET_KEY, SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, OPENAI_API_KEY, GOOGLE_API_KEY
        조건부:
          - HF_TOKEN: STT_ENGINE=local 일 때만 필수
          - GOOGLE_CLIENT_ID/SECRET: 캘린더 연동 사용 시 필수

        Returns:
            (is_valid, missing_vars): 검증 결과와 누락된 변수 목록
        """
        # 항상 필수인 변수
        required_vars = [
            ('FLASK_SECRET_KEY', cls.SECRET_KEY),
            ('SUPABASE_URL', cls.SUPABASE_URL),
            ('SUPABASE_SERVICE_ROLE_KEY', cls.SUPABASE_SERVICE_ROLE_KEY),
            ('OPENAI_API_KEY', cls.OPENAI_API_KEY),
            ('GOOGLE_API_KEY', cls.GOOGLE_API_KEY),
        ]

        # 조건부 필수 변수 (STT_ENGINE=local 일 때)
        if cls.STT_ENGINE == 'local':
            required_vars.append(('HF_TOKEN', cls.HF_TOKEN))

        # 조건부 필수 변수 (캘린더 연동 사용 시)
        if cls.GOOGLE_CLIENT_ID or cls.GOOGLE_CLIENT_SECRET:
            required_vars += [
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
        print(f"   Flask Secret Key:       {mask_key(cls.SECRET_KEY, show_secrets)}")
        print(f"   Supabase URL:           {mask_key(cls.SUPABASE_URL, show_secrets)}")
        print(f"   Supabase Service Key:   {mask_key(cls.SUPABASE_SERVICE_ROLE_KEY, show_secrets)}")
        print(f"   OpenAI API Key:         {mask_key(cls.OPENAI_API_KEY, show_secrets)}")
        print(f"   Google API Key:         {mask_key(cls.GOOGLE_API_KEY, show_secrets)}")
        print(f"   Hugging Face:           {mask_key(cls.HF_TOKEN, show_secrets)}")
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
