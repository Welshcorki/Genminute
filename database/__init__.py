"""
데이터베이스 팩토리 모듈
config.DB_TYPE에 따라 적절한 DatabaseManager(SQLite 또는 Supabase)를 반환합니다.
"""
from typing import Any
import logging
from config import config

logger = logging.getLogger(__name__)

_db_manager_instance = None

def get_db_manager() -> Any:
    """
    설정된 DB_TYPE에 맞는 DatabaseManager 인스턴스를 반환합니다.
    """
    global _db_manager_instance
    
    if _db_manager_instance is not None:
        return _db_manager_instance
        
    db_type = config.DB_TYPE
    
    if db_type == 'supabase':
        logger.info("Initializing Supabase DatabaseManager...")
        from database.supabase_manager import SupabaseManager
        _db_manager_instance = SupabaseManager()
    else:
        logger.info(f"Initializing SQLite DatabaseManager (path: {config.DATABASE_PATH})...")
        from database.sqlite_manager import DatabaseManager
        _db_manager_instance = DatabaseManager(str(config.DATABASE_PATH))
        
    return _db_manager_instance
