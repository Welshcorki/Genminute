"""
인증 계층 단위 테스트 (Firebase ID 토큰 기반)

외부 호출(Firebase, DB) 없이 mock으로 검증합니다.
테스트 항목:
- firebase_service.verify_id_token: 성공/무효/만료/키 파일 없음
- routes/auth.py: /api/firebase-config, /api/login
- config.validate: DB_TYPE에 따른 Supabase 변수 필수 여부
"""
import importlib.util
import os
import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from flask import Flask

from config import Config

try:
    from firebase_admin import auth as firebase_auth
    from services import firebase_service
    FIREBASE_AVAILABLE = True
except ImportError:
    FIREBASE_AVAILABLE = False


def _load_auth_routes():
    """
    routes/auth.py만 단독 로드합니다.

    `import routes.auth`는 routes/__init__.py를 거쳐 모든 Blueprint(벡터 DB, STT 등)를
    함께 로드하므로, 테스트에서는 파일 경로로 직접 로드해 무거운 의존성을 피합니다.
    """
    spec = importlib.util.spec_from_file_location(
        "auth_routes_under_test", ROOT_DIR / "routes" / "auth.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@unittest.skipUnless(FIREBASE_AVAILABLE, "firebase-admin 미설치")
class TestVerifyIdToken(unittest.TestCase):
    """firebase_service.verify_id_token 검증"""

    def setUp(self):
        # 실제 서비스 계정 키 없이 테스트하기 위해 초기화를 건너뜀
        patcher = mock.patch.object(firebase_service, "initialize_firebase")
        self.mock_init = patcher.start()
        self.addCleanup(patcher.stop)

    def test_valid_token_returns_user_info(self):
        decoded = {
            "uid": "uid-123",
            "email": "user@example.com",
            "name": "홍길동",
            "picture": "https://example.com/p.png",
        }
        with mock.patch.object(firebase_auth, "verify_id_token", return_value=decoded):
            result = firebase_service.verify_id_token("token")

        self.assertEqual(result, {
            "uid": "uid-123",
            "email": "user@example.com",
            "name": "홍길동",
            "picture": "https://example.com/p.png",
        })

    def test_missing_optional_fields_become_none(self):
        with mock.patch.object(firebase_auth, "verify_id_token", return_value={"uid": "u1"}):
            result = firebase_service.verify_id_token("token")

        self.assertEqual(result, {"uid": "u1", "email": None, "name": None, "picture": None})

    def test_invalid_token_returns_none(self):
        error = firebase_auth.InvalidIdTokenError("invalid")
        with mock.patch.object(firebase_auth, "verify_id_token", side_effect=error):
            self.assertIsNone(firebase_service.verify_id_token("bad"))

    def test_expired_token_returns_none(self):
        error = firebase_auth.ExpiredIdTokenError("expired", cause=None)
        with mock.patch.object(firebase_auth, "verify_id_token", side_effect=error):
            self.assertIsNone(firebase_service.verify_id_token("old"))

    def test_unexpected_error_returns_none(self):
        with mock.patch.object(firebase_auth, "verify_id_token", side_effect=RuntimeError("boom")):
            self.assertIsNone(firebase_service.verify_id_token("token"))


@unittest.skipUnless(FIREBASE_AVAILABLE, "firebase-admin 미설치")
class TestFirebaseInitialization(unittest.TestCase):
    """서비스 계정 키 파일이 없을 때의 동작"""

    def test_missing_credentials_file_fails_closed(self):
        missing_path = ROOT_DIR / "tests" / "__no_such_firebase_key__.json"
        with mock.patch.object(firebase_service, "_firebase_initialized", False), \
                mock.patch.object(firebase_service.config, "FIREBASE_CREDENTIALS_PATH", missing_path), \
                mock.patch.object(firebase_auth, "verify_id_token") as mock_verify:
            with self.assertRaises(FileNotFoundError):
                firebase_service.initialize_firebase()

            # 키 파일이 없으면 토큰을 검증하지 않고 로그인 거부(None)
            self.assertIsNone(firebase_service.verify_id_token("token"))
            mock_verify.assert_not_called()


@unittest.skipUnless(FIREBASE_AVAILABLE, "firebase-admin 미설치")
class TestAuthRoutes(unittest.TestCase):
    """routes/auth.py 엔드포인트 검증"""

    def setUp(self):
        self.auth_routes = _load_auth_routes()
        app = Flask(__name__)
        app.secret_key = "test-secret"
        app.register_blueprint(self.auth_routes.auth_bp)
        self.client = app.test_client()

    def test_firebase_config_endpoint(self):
        res = self.client.get("/api/firebase-config")

        self.assertEqual(res.status_code, 200)
        body = res.get_json()
        self.assertTrue(body["success"])
        for key in ("apiKey", "authDomain", "projectId", "appId"):
            self.assertIn(key, body["config"])

    def test_login_without_token_returns_400(self):
        res = self.client.post("/api/login", json={})

        self.assertEqual(res.status_code, 400)
        self.assertFalse(res.get_json()["success"])

    def test_login_with_invalid_token_returns_401(self):
        with mock.patch.object(self.auth_routes, "verify_id_token", return_value=None), \
                mock.patch.object(self.auth_routes, "get_or_create_user") as mock_get_user:
            res = self.client.post("/api/login", json={"idToken": "bad"})

        self.assertEqual(res.status_code, 401)
        mock_get_user.assert_not_called()

    def test_login_success_creates_session(self):
        user_info = {"uid": "uid-123", "email": "user@example.com", "name": "홍길동", "picture": None}
        db_user = {"id": 7, "email": "user@example.com", "name": "홍길동", "role": "user"}

        with mock.patch.object(self.auth_routes, "verify_id_token", return_value=user_info) as mock_verify, \
                mock.patch.object(self.auth_routes, "get_or_create_user", return_value=db_user) as mock_get_user:
            res = self.client.post("/api/login", json={"idToken": "good"})

        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.get_json()["user"]["id"], 7)
        mock_verify.assert_called_once_with("good")
        mock_get_user.assert_called_once_with(
            google_id="uid-123", email="user@example.com", name="홍길동", profile_picture=None,
        )
        with self.client.session_transaction() as sess:
            self.assertEqual(sess["user_id"], 7)
            self.assertEqual(sess["email"], "user@example.com")


class TestConfigValidate(unittest.TestCase):
    """config.validate의 조건부 필수 변수 검증"""

    BASE = {
        "SECRET_KEY": "s", "FIREBASE_API_KEY": "k", "FIREBASE_AUTH_DOMAIN": "d",
        "FIREBASE_PROJECT_ID": "p", "OPENAI_API_KEY": "o", "GOOGLE_API_KEY": "g",
        "STT_ENGINE": "gemini", "GOOGLE_CLIENT_ID": "", "GOOGLE_CLIENT_SECRET": "",
        "SUPABASE_URL": "", "SUPABASE_SERVICE_ROLE_KEY": "",
    }

    def test_sqlite_does_not_require_supabase(self):
        with mock.patch.multiple(Config, DB_TYPE="sqlite", **self.BASE):
            is_valid, missing = Config.validate()

        self.assertTrue(is_valid, missing)

    def test_supabase_requires_supabase_vars(self):
        with mock.patch.multiple(Config, DB_TYPE="supabase", **self.BASE):
            is_valid, missing = Config.validate()

        self.assertFalse(is_valid)
        self.assertEqual(set(missing), {"SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY"})

    def test_firebase_vars_are_required(self):
        overrides = {**self.BASE, "FIREBASE_API_KEY": "", "FIREBASE_PROJECT_ID": ""}
        with mock.patch.multiple(Config, DB_TYPE="sqlite", **overrides):
            is_valid, missing = Config.validate()

        self.assertFalse(is_valid)
        self.assertEqual(set(missing), {"FIREBASE_API_KEY", "FIREBASE_PROJECT_ID"})

    def test_default_db_type_is_sqlite(self):
        # DB_TYPE 환경 변수가 없을 때의 기본값 (.env의 영향을 받지 않도록 소스 기준 검증)
        source = (ROOT_DIR / "config.py").read_text(encoding="utf-8")
        self.assertIn("os.getenv('DB_TYPE', 'sqlite')", source)


if __name__ == "__main__":
    unittest.main()
