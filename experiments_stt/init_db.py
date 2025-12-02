#!/usr/bin/env python3
"""
데이터베이스 초기화 스크립트
프로젝트를 처음 시작하거나 DB를 재생성할 때 실행합니다.

실행 방법:
    python init_db.py
"""
import sqlite3
import os
import logging
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# 로깅 설정 (app.py와 동일한 방식)
from config import config
logging.basicConfig(level=config.LOG_LEVEL, format=config.LOG_FORMAT)
logger = logging.getLogger(__name__)

DB_PATH = "database/minute_ai.db"

def init_database():
    """데이터베이스 및 모든 테이블 초기화"""

    logger.info("=" * 70)
    logger.info("🔧 데이터베이스 초기화 시작")
    logger.info("=" * 70)

    # database 폴더 생성
    os.makedirs("database", exist_ok=True)
    logger.info("✅ database 폴더 생성/확인 완료")

    # DB 연결 (파일 없으면 자동 생성)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    logger.info(f"✅ DB 파일 생성/연결: {DB_PATH}")

    # 1. meeting_dialogues 테이블 (음성인식 결과)
    logger.info("1️⃣ meeting_dialogues 테이블 생성...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS meeting_dialogues (
            segment_id INTEGER PRIMARY KEY AUTOINCREMENT,
            meeting_id TEXT NOT NULL,
            meeting_date TEXT,
            speaker_label TEXT,
            start_time REAL,
            segment TEXT,
            confidence REAL,
            audio_file TEXT,
            title TEXT,
            owner_id INTEGER
        )
    """)
    conn.commit()
    logger.info("✅ meeting_dialogues 테이블 생성 완료")

    # 2. meeting_minutes 테이블 (회의록)
    logger.info("2️⃣ meeting_minutes 테이블 생성...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS meeting_minutes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            meeting_id TEXT UNIQUE NOT NULL,
            title TEXT,
            meeting_date TEXT,
            minutes_content TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            owner_id INTEGER
        )
    """)
    conn.commit()
    logger.info("✅ meeting_minutes 테이블 생성 완료")

    # 3. meeting_mindmap 테이블 (마인드맵)
    logger.info("3️⃣ meeting_mindmap 테이블 생성...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS meeting_mindmap (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            meeting_id TEXT UNIQUE NOT NULL,
            mindmap_content TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    logger.info("✅ meeting_mindmap 테이블 생성 완료")

    # 4. users 테이블 (사용자 정보)
    logger.info("4️⃣ users 테이블 생성...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            google_id TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            name TEXT,
            profile_picture TEXT,
            role TEXT DEFAULT 'user',
            google_auth_credentials_json TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    logger.info("✅ users 테이블 생성 완료")

    # 5. meeting_shares 테이블 (공유 정보)
    logger.info("5️⃣ meeting_shares 테이블 생성...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS meeting_shares (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            meeting_id TEXT NOT NULL,
            owner_id INTEGER NOT NULL,
            shared_with_user_id INTEGER NOT NULL,
            permission TEXT DEFAULT 'read',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (owner_id) REFERENCES users(id),
            FOREIGN KEY (shared_with_user_id) REFERENCES users(id),
            UNIQUE(meeting_id, shared_with_user_id)
        )
    """)
    conn.commit()
    logger.info("✅ meeting_shares 테이블 생성 완료")

    # 6. Admin 사용자 생성
    logger.info("6️⃣ Admin 사용자 생성...")
    admin_emails = os.getenv('ADMIN_EMAILS', '').split(',')
    admin_emails = [email.strip() for email in admin_emails if email.strip()]

    if admin_emails:
        for email in admin_emails:
            try:
                cursor.execute("""
                    INSERT INTO users (google_id, email, name, role)
                    VALUES (?, ?, ?, 'admin')
                """, (f"admin_{email}", email, "Admin User"))
                conn.commit()
                logger.info(f"✅ Admin 사용자 생성: {email}")
            except sqlite3.IntegrityError:
                logger.warning(f"⚠️ Admin 이미 존재: {email}")
    else:
        logger.warning("⚠️ ADMIN_EMAILS 환경변수가 설정되지 않았습니다")
        logger.warning("   .env 파일에 ADMIN_EMAILS=your@email.com 추가하세요")

    # 7. 인덱스 생성 (성능 최적화)
    logger.info("7️⃣ 인덱스 생성...")
    try:
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_meeting_id ON meeting_dialogues(meeting_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_owner_id ON meeting_dialogues(owner_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_shares_meeting ON meeting_shares(meeting_id)")
        conn.commit()
        logger.info("✅ 인덱스 생성 완료")
    except Exception as e:
        logger.warning(f"⚠️ 인덱스 생성 중 일부 에러: {e}")

    # 8. 최종 확인
    logger.info("=" * 70)
    logger.info("📊 생성된 테이블 확인:")
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
    tables = cursor.fetchall()
    for t in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {t[0]}")
        count = cursor.fetchone()[0]
        logger.info(f"  ✅ {t[0]:25} ({count}개 레코드)")

    logger.info("\n🎉 데이터베이스 초기화 완료!")
    logger.info(f"📁 DB 위치: {os.path.abspath(DB_PATH)}")
    logger.info("=" * 70)

    conn.close()

if __name__ == "__main__":
    # 기존 DB 있으면 경고
    if os.path.exists(DB_PATH):
        # 개발 중에는 확인 없이 바로 삭제하고 새로 생성하는 것이 편할 수 있음
        # 여기서는 안전을 위해 확인 절차 유지
        logger.warning(f"⚠️ 경고: {DB_PATH} 파일이 이미 존재합니다!")
        logger.warning("   기존 데이터는 유지되고, 없는 테이블만 생성됩니다.")
        try:
            response = input("    계속하시겠습니까? (y/n): ")
            if response.lower() != 'y':
                logger.info("취소되었습니다.")
                exit(0)
        except (EOFError, KeyboardInterrupt):
            # 비대화형 환경(예: CI/CD)에서 실행될 경우 input()에서 오류 발생 가능
            logger.info("\n비대화형 환경에서 실행되어 취소합니다.")
            exit(0)


    init_database()