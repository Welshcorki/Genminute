
import sqlite3
import uuid
import datetime
import logging

logger = logging.getLogger(__name__)


class DatabaseManager:
    """SQLite 데이터베이스 관리 (Singleton 패턴)"""
    _instance = None
    _initialized = False

    def __new__(cls, db_path=None):
        if cls._instance is None:
            cls._instance = super(DatabaseManager, cls).__new__(cls)
        return cls._instance

    def __init__(self, db_path=None):
        # 이미 초기화된 경우 건너뛰기 (Singleton)
        if self._initialized:
            return

        if db_path is None:
            raise ValueError("DatabaseManager 최초 생성 시 db_path가 필요합니다.")

        self.db_path = db_path
        self._initialized = True
        logger.info(f"✅ DatabaseManager 초기화: {db_path}")

        # 데이터베이스 테이블 자동 생성
        self._initialize_tables()

    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _initialize_tables(self):
        """
        데이터베이스 테이블을 자동으로 생성합니다.
        app.py 시작 시 자동으로 호출되어 필요한 모든 테이블을 생성합니다.
        """
        import os

        # database 폴더 생성
        db_dir = os.path.dirname(self.db_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)

        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            # 1. meeting_dialogues 테이블 (음성인식 결과)
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

            # 2. meeting_minutes 테이블 (회의록)
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

            # 3. meeting_mindmap 테이블 (마인드맵)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS meeting_mindmap (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    meeting_id TEXT UNIQUE NOT NULL,
                    mindmap_content TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # 4. users 테이블 (사용자 정보)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    google_id TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    name TEXT,
                    profile_picture TEXT,
                    role TEXT DEFAULT 'user',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # 5. meeting_shares 테이블 (공유 정보)
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

            # 6. meeting_action_items 테이블 (Action Item)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS meeting_action_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    meeting_id TEXT NOT NULL,
                    content TEXT NOT NULL,
                    due_date TEXT,
                    status TEXT DEFAULT 'pending',
                    tool_call_id TEXT,
                    calendar_event_id TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # 7. 인덱스 생성 (성능 최적화)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_meeting_id ON meeting_dialogues(meeting_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_owner_id ON meeting_dialogues(owner_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_shares_meeting ON meeting_shares(meeting_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_action_items_meeting ON meeting_action_items(meeting_id)")

            # 8. Admin 사용자 자동 생성
            from config import config
            admin_emails = config.ADMIN_EMAILS

            if admin_emails:
                for email in admin_emails:
                    if email.strip():  # 빈 문자열 제외
                        try:
                            cursor.execute("""
                                INSERT INTO users (google_id, email, name, role)
                                VALUES (?, ?, ?, 'admin')
                            """, (f"admin_{email}", email, "Admin User"))
                            logger.info(f"✅ Admin 사용자 생성: {email}")
                        except sqlite3.IntegrityError:
                            # 이미 존재하는 경우 (정상)
                            pass

            conn.commit()
            logger.info("✅ 데이터베이스 테이블 초기화 완료")

        except Exception as e:
            conn.rollback()
            logger.error(f"❌ 데이터베이스 테이블 초기화 실패: {e}")
            raise

        finally:
            conn.close()

    def save_stt_to_db(self, segments, audio_filename, title, meeting_date=None, owner_id=None):
        """
        음성 인식 결과를 데이터베이스에 저장합니다.

        Args:
            segments (list): 음성 인식 결과 세그먼트 리스트
            audio_filename (str): 오디오 파일명
            title (str): 회의 제목
            meeting_date (str, optional): 회의 일시 (형식: "YYYY-MM-DD HH:MM:SS")
                                          제공되지 않으면 현재 시간 사용
            owner_id (int, optional): 회의 소유자 ID

        Returns:
            str: 생성된 meeting_id
        """
        meeting_id = str(uuid.uuid4())

        # meeting_date가 제공되지 않으면 현재 시간 사용
        if meeting_date is None:
            meeting_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        conn = self._get_connection()
        cursor = conn.cursor()
        for segment in segments:
            cursor.execute("""
                INSERT INTO meeting_dialogues
                (meeting_id, meeting_date, speaker_label, start_time, segment, confidence, audio_file, title, owner_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                meeting_id, meeting_date, str(segment['speaker']), segment['start_time'],
                segment['text'], segment['confidence'], audio_filename, title, owner_id
            ))
        conn.commit()
        conn.close()
        logger.info(f"✅ DB 저장 완료: meeting_id={meeting_id}, owner_id={owner_id}, meeting_date={meeting_date}")
        return meeting_id

    def get_meeting_by_id(self, meeting_id):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM meeting_dialogues WHERE meeting_id = ? ORDER BY start_time ASC", (meeting_id,))
        rows = cursor.fetchall()
        conn.close()
        return rows

    def get_all_meetings(self):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT meeting_id, title, MAX(meeting_date) as date,
                   (SELECT audio_file FROM meeting_dialogues WHERE meeting_id = md.meeting_id LIMIT 1) as audio_file
            FROM meeting_dialogues md
            GROUP BY meeting_id
            ORDER BY date DESC
        """)
        meetings = cursor.fetchall()
        conn.close()
        return meetings

    def get_segments_by_meeting_id(self, meeting_id):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM meeting_dialogues WHERE meeting_id = ? ORDER BY start_time ASC", (meeting_id,))
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def save_minutes(self, meeting_id, title, meeting_date, minutes_content, owner_id=None):
        """
        생성된 회의록을 데이터베이스에 저장합니다.

        Args:
            meeting_id (str): 회의 ID
            title (str): 회의 제목
            meeting_date (str): 회의 일시
            minutes_content (str): 회의록 내용 (마크다운 형식)
            owner_id (int, optional): 회의 소유자 ID

        Returns:
            bool: 저장 성공 여부
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        # meeting_minutes 테이블이 없으면 생성
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

        created_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 기존 회의록이 있는지 확인
        cursor.execute("SELECT meeting_id FROM meeting_minutes WHERE meeting_id = ?", (meeting_id,))
        existing = cursor.fetchone()

        if existing:
            # 기존 회의록 업데이트
            cursor.execute("""
                UPDATE meeting_minutes
                SET title = ?, meeting_date = ?, minutes_content = ?, updated_at = ?, owner_id = ?
                WHERE meeting_id = ?
            """, (title, meeting_date, minutes_content, created_at, owner_id, meeting_id))
            logger.info(f"✅ 회의록 업데이트 완료: meeting_id={meeting_id}, owner_id={owner_id}")
        else:
            # 새 회의록 저장
            cursor.execute("""
                INSERT INTO meeting_minutes (meeting_id, title, meeting_date, minutes_content, created_at, updated_at, owner_id)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (meeting_id, title, meeting_date, minutes_content, created_at, created_at, owner_id))
            logger.info(f"✅ 회의록 저장 완료: meeting_id={meeting_id}, owner_id={owner_id}")

        conn.commit()
        conn.close()
        return True

    def get_minutes_by_meeting_id(self, meeting_id):
        """
        meeting_id로 저장된 회의록을 조회합니다.

        Args:
            meeting_id (str): 회의 ID

        Returns:
            dict or None: 회의록 정보 (meeting_id, title, meeting_date, minutes_content, created_at, updated_at)
                          없으면 None 반환
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        # meeting_minutes 테이블이 없으면 None 반환
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='meeting_minutes'")
        if not cursor.fetchone():
            conn.close()
            return None

        cursor.execute("""
            SELECT meeting_id, title, meeting_date, minutes_content, created_at, updated_at
            FROM meeting_minutes
            WHERE meeting_id = ?
        """, (meeting_id,))

        row = cursor.fetchone()
        conn.close()

        if row:
            return dict(row)
        return None

    def delete_meeting_data(self, meeting_id=None, audio_file=None, title=None):
        """
        지정된 조건에 따라 회의 데이터를 삭제합니다.
        경고: 아무 조건도 주어지지 않으면 테이블의 모든 데이터가 삭제됩니다.
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        query = "DELETE FROM meeting_dialogues"
        conditions = []
        params = []

        if meeting_id:
            conditions.append("meeting_id = ?")
            params.append(meeting_id)
        if audio_file:
            conditions.append("audio_file = ?")
            params.append(audio_file)
        if title:
            conditions.append("title = ?")
            params.append(title)

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        cursor.execute(query, tuple(params))
        deleted_rows = cursor.rowcount
        conn.commit()
        conn.close()

        logger.info(f"✅ DB 삭제 완료: {deleted_rows}개 행 삭제됨")
        return deleted_rows

    def delete_meeting_by_id(self, meeting_id):
        """
        meeting_id로 회의와 관련된 모든 데이터를 삭제합니다.
        - meeting_dialogues 테이블에서 세그먼트 삭제
        - meeting_minutes 테이블에서 회의록 삭제
        - meeting_shares 테이블에서 공유 관계 삭제

        Args:
            meeting_id (str): 삭제할 회의 ID

        Returns:
            dict: 삭제 전후 항목 수 정보
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        logger.info(f"\n📊 [SQLite DB 삭제 검증 시작] meeting_id = {meeting_id}")
        logger.info("=" * 70)

        # 1. meeting_dialogues 삭제 전 개수 확인
        cursor.execute("SELECT COUNT(*) as count FROM meeting_dialogues WHERE meeting_id = ?", (meeting_id,))
        before_dialogues = cursor.fetchone()['count']
        logger.info(f"[삭제 전] meeting_dialogues: {before_dialogues}개")

        # 2. meeting_minutes 삭제 전 개수 확인
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='meeting_minutes'")
        before_minutes = 0
        if cursor.fetchone():
            cursor.execute("SELECT COUNT(*) as count FROM meeting_minutes WHERE meeting_id = ?", (meeting_id,))
            before_minutes = cursor.fetchone()['count']
            logger.info(f"[삭제 전] meeting_minutes: {before_minutes}개")
        else:
            logger.info(f"[삭제 전] meeting_minutes: 테이블 없음")

        # 3. meeting_shares 삭제 전 개수 확인
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='meeting_shares'")
        before_shares = 0
        if cursor.fetchone():
            cursor.execute("SELECT COUNT(*) as count FROM meeting_shares WHERE meeting_id = ?", (meeting_id,))
            before_shares = cursor.fetchone()['count']
            logger.info(f"[삭제 전] meeting_shares: {before_shares}개")
        else:
            logger.info(f"[삭제 전] meeting_shares: 테이블 없음")

        # 4. meeting_mindmap 삭제 전 개수 확인
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='meeting_mindmap'")
        before_mindmap = 0
        if cursor.fetchone():
            cursor.execute("SELECT COUNT(*) as count FROM meeting_mindmap WHERE meeting_id = ?", (meeting_id,))
            before_mindmap = cursor.fetchone()['count']
            logger.info(f"[삭제 전] meeting_mindmap: {before_mindmap}개")
        else:
            logger.info(f"[삭제 전] meeting_mindmap: 테이블 없음")

        # 5. meeting_action_items 삭제 전 개수 확인
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='meeting_action_items'")
        before_action_items = 0
        if cursor.fetchone():
            cursor.execute("SELECT COUNT(*) as count FROM meeting_action_items WHERE meeting_id = ?", (meeting_id,))
            before_action_items = cursor.fetchone()['count']
            logger.info(f"[삭제 전] meeting_action_items: {before_action_items}개")
        else:
            logger.info(f"[삭제 전] meeting_action_items: 테이블 없음")

        logger.info("-" * 70)

        # 4. meeting_dialogues에서 삭제 수행
        cursor.execute("DELETE FROM meeting_dialogues WHERE meeting_id = ?", (meeting_id,))
        deleted_dialogues = cursor.rowcount

        # 5. meeting_minutes에서 삭제 수행
        deleted_minutes = 0
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='meeting_minutes'")
        if cursor.fetchone():
            cursor.execute("DELETE FROM meeting_minutes WHERE meeting_id = ?", (meeting_id,))
            deleted_minutes = cursor.rowcount

        # 6. meeting_shares에서 삭제 수행
        deleted_shares = 0
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='meeting_shares'")
        if cursor.fetchone():
            cursor.execute("DELETE FROM meeting_shares WHERE meeting_id = ?", (meeting_id,))
            deleted_shares = cursor.rowcount

        # 7. meeting_mindmap에서 삭제 수행
        deleted_mindmap = 0
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='meeting_mindmap'")
        if cursor.fetchone():
            cursor.execute("DELETE FROM meeting_mindmap WHERE meeting_id = ?", (meeting_id,))
            deleted_mindmap = cursor.rowcount

        # 8. meeting_action_items에서 삭제 수행
        deleted_action_items = 0
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='meeting_action_items'")
        if cursor.fetchone():
            cursor.execute("DELETE FROM meeting_action_items WHERE meeting_id = ?", (meeting_id,))
            deleted_action_items = cursor.rowcount

        conn.commit()

        logger.info(f"[삭제 수행] meeting_dialogues: {deleted_dialogues}개 삭제")
        logger.info(f"[삭제 수행] meeting_minutes: {deleted_minutes}개 삭제")
        logger.info(f"[삭제 수행] meeting_shares: {deleted_shares}개 삭제")
        logger.info(f"[삭제 수행] meeting_mindmap: {deleted_mindmap}개 삭제")
        logger.info(f"[삭제 수행] meeting_action_items: {deleted_action_items}개 삭제")

        logger.info("-" * 70)

        # 7. 삭제 후 검증
        cursor.execute("SELECT COUNT(*) as count FROM meeting_dialogues WHERE meeting_id = ?", (meeting_id,))
        after_dialogues = cursor.fetchone()['count']
        logger.info(f"[삭제 후] meeting_dialogues: {after_dialogues}개 남음")

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='meeting_minutes'")
        after_minutes = 0
        if cursor.fetchone():
            cursor.execute("SELECT COUNT(*) as count FROM meeting_minutes WHERE meeting_id = ?", (meeting_id,))
            after_minutes = cursor.fetchone()['count']
            logger.info(f"[삭제 후] meeting_minutes: {after_minutes}개 남음")

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='meeting_shares'")
        after_shares = 0
        if cursor.fetchone():
            cursor.execute("SELECT COUNT(*) as count FROM meeting_shares WHERE meeting_id = ?", (meeting_id,))
            after_shares = cursor.fetchone()['count']
            logger.info(f"[삭제 후] meeting_shares: {after_shares}개 남음")

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='meeting_mindmap'")
        after_mindmap = 0
        if cursor.fetchone():
            cursor.execute("SELECT COUNT(*) as count FROM meeting_mindmap WHERE meeting_id = ?", (meeting_id,))
            after_mindmap = cursor.fetchone()['count']
            logger.info(f"[삭제 후] meeting_mindmap: {after_mindmap}개 남음")

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='meeting_action_items'")
        after_action_items = 0
        if cursor.fetchone():
            cursor.execute("SELECT COUNT(*) as count FROM meeting_action_items WHERE meeting_id = ?", (meeting_id,))
            after_action_items = cursor.fetchone()['count']
            logger.info(f"[삭제 후] meeting_action_items: {after_action_items}개 남음")

        conn.close()

        # 검증 결과
        if after_dialogues == 0 and after_minutes == 0 and after_shares == 0 and after_mindmap == 0 and after_action_items == 0:
            logger.info(f"✅ SQLite DB 삭제 검증 성공: 모든 데이터가 삭제되었습니다.")
        else:
            logger.warning(f"⚠️ SQLite DB 삭제 검증 실패: 일부 데이터가 남아있습니다!")

        logger.info("=" * 70)

        return {
            "dialogues": deleted_dialogues,
            "minutes": deleted_minutes,
            "shares": deleted_shares,
            "mindmap": deleted_mindmap,
            "before": {"dialogues": before_dialogues, "minutes": before_minutes, "shares": before_shares, "mindmap": before_mindmap},
            "after": {"dialogues": after_dialogues, "minutes": after_minutes, "shares": after_shares, "mindmap": after_mindmap}
        }

    def get_audio_file_by_meeting_id(self, meeting_id):
        """
        meeting_id로 오디오 파일명을 조회합니다.

        Args:
            meeting_id (str): 회의 ID

        Returns:
            str or None: 오디오 파일명, 없으면 None
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT audio_file FROM meeting_dialogues WHERE meeting_id = ? LIMIT 1", (meeting_id,))
        row = cursor.fetchone()
        conn.close()

        if row:
            return row['audio_file']
        return None

    def update_meeting_title(self, meeting_id, new_title):
        """
        회의 제목을 업데이트합니다.
        - ChromaDB: meeting_chunk, meeting_subtopic 컬렉션 메타데이터 업데이트
        - meeting_dialogues: 해당 meeting_id의 모든 행 업데이트
        - meeting_minutes: 해당 meeting_id의 제목 업데이트

        Args:
            meeting_id (str): 회의 ID
            new_title (str): 새로운 제목

        Returns:
            dict: 업데이트 결과 {'success': bool, 'updated_dialogues': int, 'updated_minutes': int, 'updated_vector': dict}
        """
        # ChromaDB 업데이트 먼저 수행 (순환 참조 방지를 위한 lazy import)
        from database.vector_manager import vdb_manager

        # 1. ChromaDB 메타데이터 업데이트
        vector_result = vdb_manager.update_metadata_title(meeting_id, new_title)

        if not vector_result['success']:
            # ChromaDB 업데이트 실패 시 전체 실패 처리
            logger.warning(f"⚠️ ChromaDB 업데이트 실패로 인해 SQLite 업데이트를 건너뜁니다.")
            return {
                'success': False,
                'error': f"ChromaDB 업데이트 실패: {vector_result.get('error', '알 수 없는 오류')}",
                'updated_dialogues': 0,
                'updated_minutes': 0,
                'updated_vector': vector_result
            }

        # 2. SQLite 업데이트 (ChromaDB 성공 후)
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            # 2-1. meeting_dialogues 테이블 업데이트
            cursor.execute("""
                UPDATE meeting_dialogues
                SET title = ?
                WHERE meeting_id = ?
            """, (new_title, meeting_id))
            updated_dialogues = cursor.rowcount

            # 2-2. meeting_minutes 테이블 업데이트 (테이블이 존재하는 경우)
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='meeting_minutes'")
            updated_minutes = 0
            if cursor.fetchone():
                cursor.execute("""
                    UPDATE meeting_minutes
                    SET title = ?,
                        updated_at = ?
                    WHERE meeting_id = ?
                """, (new_title, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), meeting_id))
                updated_minutes = cursor.rowcount

            conn.commit()

            logger.info(f"✅ SQLite 제목 업데이트 완료: meeting_id={meeting_id}, dialogues={updated_dialogues}개, minutes={updated_minutes}개")

            return {
                'success': True,
                'updated_dialogues': updated_dialogues,
                'updated_minutes': updated_minutes,
                'updated_vector': vector_result
            }

        except Exception as e:
            conn.rollback()
            logger.error(f"❌ SQLite 제목 업데이트 실패: {e}")
            logger.warning(f"⚠️ ChromaDB는 이미 업데이트되었습니다. 데이터 불일치 발생!")
            return {
                'success': False,
                'error': str(e),
                'updated_dialogues': 0,
                'updated_minutes': 0,
                'updated_vector': vector_result
            }

        finally:
            conn.close()

    def update_meeting_date(self, meeting_id, new_date):
        """
        회의 날짜를 업데이트합니다.
        - ChromaDB: meeting_chunk, meeting_subtopic 컬렉션 메타데이터 업데이트
        - meeting_dialogues: 해당 meeting_id의 모든 행 업데이트
        - meeting_minutes: 해당 meeting_id의 날짜 업데이트

        Args:
            meeting_id (str): 회의 ID
            new_date (str): 새로운 날짜 (형식: "YYYY-MM-DD HH:MM:SS")

        Returns:
            dict: 업데이트 결과 {'success': bool, 'updated_dialogues': int, 'updated_minutes': int, 'updated_vector': dict}
        """
        # ChromaDB 업데이트 먼저 수행 (순환 참조 방지를 위한 lazy import)
        from database.vector_manager import vdb_manager

        # 1. ChromaDB 메타데이터 업데이트
        vector_result = vdb_manager.update_metadata_date(meeting_id, new_date)

        if not vector_result['success']:
            # ChromaDB 업데이트 실패 시 전체 실패 처리
            logger.warning(f"⚠️ ChromaDB 업데이트 실패로 인해 SQLite 업데이트를 건너뜁니다.")
            return {
                'success': False,
                'error': f"ChromaDB 업데이트 실패: {vector_result.get('error', '알 수 없는 오류')}",
                'updated_dialogues': 0,
                'updated_minutes': 0,
                'updated_vector': vector_result
            }

        # 2. SQLite 업데이트 (ChromaDB 성공 후)
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            # 2-1. meeting_dialogues 테이블 업데이트
            cursor.execute("""
                UPDATE meeting_dialogues
                SET meeting_date = ?
                WHERE meeting_id = ?
            """, (new_date, meeting_id))
            updated_dialogues = cursor.rowcount

            # 2-2. meeting_minutes 테이블 업데이트 (테이블이 존재하는 경우)
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='meeting_minutes'")
            updated_minutes = 0
            if cursor.fetchone():
                cursor.execute("""
                    UPDATE meeting_minutes
                    SET meeting_date = ?,
                        updated_at = ?
                    WHERE meeting_id = ?
                """, (new_date, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), meeting_id))
                updated_minutes = cursor.rowcount

            conn.commit()

            logger.info(f"✅ SQLite 날짜 업데이트 완료: meeting_id={meeting_id}, dialogues={updated_dialogues}개, minutes={updated_minutes}개")

            return {
                'success': True,
                'updated_dialogues': updated_dialogues,
                'updated_minutes': updated_minutes,
                'updated_vector': vector_result
            }

        except Exception as e:
            conn.rollback()
            logger.error(f"❌ SQLite 날짜 업데이트 실패: {e}")
            logger.warning(f"⚠️ ChromaDB는 이미 업데이트되었습니다. 데이터 불일치 발생!")
            return {
                'success': False,
                'error': str(e),
                'updated_dialogues': 0,
                'updated_minutes': 0,
                'updated_vector': vector_result
            }

        finally:
            conn.close()

    def save_mindmap(self, meeting_id, mindmap_content):
        """
        생성된 마인드맵 키워드를 데이터베이스에 저장합니다.

        Args:
            meeting_id (str): 회의 ID
            mindmap_content (str): 마인드맵 마크다운 내용

        Returns:
            bool: 저장 성공 여부
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        # meeting_mindmap 테이블이 없으면 생성
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS meeting_mindmap (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                meeting_id TEXT UNIQUE NOT NULL,
                mindmap_content TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        created_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 기존 마인드맵이 있는지 확인
        cursor.execute("SELECT meeting_id FROM meeting_mindmap WHERE meeting_id = ?", (meeting_id,))
        existing = cursor.fetchone()

        if existing:
            # 기존 마인드맵 업데이트
            cursor.execute("""
                UPDATE meeting_mindmap
                SET mindmap_content = ?, created_at = ?
                WHERE meeting_id = ?
            """, (mindmap_content, created_at, meeting_id))
            logger.info(f"✅ 마인드맵 업데이트 완료: meeting_id={meeting_id}")
        else:
            # 새 마인드맵 저장
            cursor.execute("""
                INSERT INTO meeting_mindmap (meeting_id, mindmap_content, created_at)
                VALUES (?, ?, ?)
            """, (meeting_id, mindmap_content, created_at))
            logger.info(f"✅ 마인드맵 저장 완료: meeting_id={meeting_id}")

        conn.commit()
        conn.close()
        return True

    def get_mindmap_by_meeting_id(self, meeting_id):
        """
        meeting_id로 저장된 마인드맵을 조회합니다.

        Args:
            meeting_id (str): 회의 ID

        Returns:
            str: 마인드맵 마크다운 내용, 없으면 None
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        # 테이블 존재 여부 확인
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='meeting_mindmap'")
        if not cursor.fetchone():
            conn.close()
            return None

        cursor.execute("SELECT mindmap_content FROM meeting_mindmap WHERE meeting_id = ?", (meeting_id,))
        row = cursor.fetchone()
        conn.close()

        if row:
            return row['mindmap_content']
        return None

    def delete_mindmap_by_meeting_id(self, meeting_id):
        """
        meeting_id로 마인드맵 데이터를 삭제합니다.

        Args:
            meeting_id (str): 회의 ID

        Returns:
            int: 삭제된 행 수
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        # 테이블 존재 여부 확인
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='meeting_mindmap'")
        if not cursor.fetchone():
            conn.close()
            return 0

        cursor.execute("DELETE FROM meeting_mindmap WHERE meeting_id = ?", (meeting_id,))
        deleted_count = cursor.rowcount
        conn.commit()
        conn.close()

        return deleted_count

    def update_user_google_credentials(self, user_id: int, credentials_json: str):
        """
        사용자의 Google OAuth 2.0 인증 정보를 DB에 저장(업데이트)합니다.

        Args:
            user_id (int): 사용자 ID
            credentials_json (str): 직렬화된 인증 정보 (JSON 문자열)
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            # users 테이블에 google_auth_credentials_json 컬럼이 없으면 추가
            cursor.execute("PRAGMA table_info(users)")
            columns = [col[1] for col in cursor.fetchall()]
            if 'google_auth_credentials_json' not in columns:
                cursor.execute("ALTER TABLE users ADD COLUMN google_auth_credentials_json TEXT")
                logger.info("✅ 'users' 테이블에 'google_auth_credentials_json' 컬럼 추가 완료")

            cursor.execute("""
                UPDATE users
                SET google_auth_credentials_json = ?
                WHERE id = ?
            """, (credentials_json, user_id))
            conn.commit()
            logger.info(f"✅ 사용자 {user_id}의 Google 인증 정보 업데이트 완료")
        except Exception as e:
            conn.rollback()
            logger.error(f"❌ 사용자 {user_id}의 Google 인증 정보 업데이트 실패: {e}")
        finally:
            conn.close()

    def get_user_google_credentials(self, user_id: int) -> str or None:
        """
        사용자의 Google OAuth 2.0 인증 정보를 DB에서 조회합니다.

        Args:
            user_id (int): 사용자 ID

        Returns:
            str or None: 직렬화된 인증 정보 (JSON 문자열), 없으면 None
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT google_auth_credentials_json FROM users WHERE id = ?", (user_id,))
            row = cursor.fetchone()
            if row and row['google_auth_credentials_json']:
                return row['google_auth_credentials_json']
            return None
        except Exception as e:
            logger.error(f"❌ 사용자 {user_id}의 Google 인증 정보 조회 실패: {e}")
            return None
        finally:
            conn.close()

    # ========== Action Items 관련 메서드 ==========

    def save_action_items(self, meeting_id: str, items: list):
        """
        Action Item 목록을 데이터베이스에 저장합니다.

        Args:
            meeting_id (str): 회의 ID
            items (list): Action Item 딕셔너리 리스트
                각 항목은 다음 키를 포함해야 함:
                - content (str): Action Item 내용
                - due_date (str, optional): 마감 기한 (ISO 8601 형식)
                - tool_call_id (str, optional): 도구 호출 ID
                - calendar_event_id (str, optional): 캘린더 이벤트 ID
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            for item in items:
                cursor.execute("""
                    INSERT INTO meeting_action_items 
                    (meeting_id, content, due_date, tool_call_id, calendar_event_id, status)
                    VALUES (?, ?, ?, ?, ?, 'pending')
                """, (
                    meeting_id,
                    item.get('content') or item.get('summary', ''),
                    item.get('due_date') or item.get('start_time'),
                    item.get('tool_call_id'),
                    item.get('calendar_event_id')
                ))
            
            conn.commit()
            logger.info(f"✅ Action Items 저장 완료: meeting_id={meeting_id}, {len(items)}개 항목")
        except Exception as e:
            conn.rollback()
            logger.error(f"❌ Action Items 저장 실패: {e}", exc_info=True)
            raise
        finally:
            conn.close()

    def get_action_items_by_meeting_id(self, meeting_id: str):
        """
        회의 ID로 Action Item 목록을 조회합니다.

        Args:
            meeting_id (str): 회의 ID

        Returns:
            list: Action Item 딕셔너리 리스트
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            # 테이블 존재 여부 확인
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='meeting_action_items'")
            if not cursor.fetchone():
                return []

            cursor.execute("""
                SELECT id, meeting_id, content, due_date, status, tool_call_id, calendar_event_id, 
                       created_at, updated_at
                FROM meeting_action_items
                WHERE meeting_id = ?
                ORDER BY created_at ASC
            """, (meeting_id,))

            items = []
            for row in cursor.fetchall():
                items.append({
                    'id': row['id'],
                    'meeting_id': row['meeting_id'],
                    'content': row['content'],
                    'due_date': row['due_date'],
                    'status': row['status'],
                    'tool_call_id': row['tool_call_id'],
                    'calendar_event_id': row['calendar_event_id'],
                    'created_at': row['created_at'],
                    'updated_at': row['updated_at']
                })

            return items
        except Exception as e:
            logger.error(f"❌ Action Items 조회 실패: {e}", exc_info=True)
            return []
        finally:
            conn.close()

    def update_action_item_status(self, item_id: int, status: str):
        """
        Action Item의 상태를 업데이트합니다.

        Args:
            item_id (int): Action Item ID
            status (str): 새 상태 ('pending' 또는 'done')

        Returns:
            bool: 성공 여부
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            if status not in ['pending', 'done']:
                raise ValueError(f"잘못된 상태 값: {status}")

            updated_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute("""
                UPDATE meeting_action_items
                SET status = ?, updated_at = ?
                WHERE id = ?
            """, (status, updated_at, item_id))

            conn.commit()
            logger.info(f"✅ Action Item 상태 업데이트 완료: id={item_id}, status={status}")
            return cursor.rowcount > 0
        except Exception as e:
            conn.rollback()
            logger.error(f"❌ Action Item 상태 업데이트 실패: {e}", exc_info=True)
            return False
        finally:
            conn.close()

    def get_action_item_meeting_id(self, item_id: int):
        """
        Action Item ID로 회의 ID를 조회합니다.

        Args:
            item_id (int): Action Item ID

        Returns:
            str or None: 회의 ID, 없으면 None
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("SELECT meeting_id FROM meeting_action_items WHERE id = ?", (item_id,))
            row = cursor.fetchone()
            if row:
                return row['meeting_id']
            return None
        except Exception as e:
            logger.error(f"❌ Action Item 회의 ID 조회 실패: {e}", exc_info=True)
            return None
        finally:
            conn.close()

    def delete_action_items_by_meeting_id(self, meeting_id: str):
        """
        회의 ID로 관련된 모든 Action Item을 삭제합니다.

        Args:
            meeting_id (str): 회의 ID

        Returns:
            int: 삭제된 행 수
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("DELETE FROM meeting_action_items WHERE meeting_id = ?", (meeting_id,))
            deleted_count = cursor.rowcount
            conn.commit()
            logger.info(f"✅ Action Items 삭제 완료: meeting_id={meeting_id}, {deleted_count}개 삭제")
            return deleted_count
        except Exception as e:
            conn.rollback()
            logger.error(f"❌ Action Items 삭제 실패: {e}", exc_info=True)
            return 0
        finally:
            conn.close()
