# Cleanup 작업 핸드오프 (2026-07-01)

브랜치: `cleanup` (main에서 분기). main은 무수정.

## 지금까지 한 것

1. **이전 세션의 미커밋 작업 복구 + 검증.** 작업 시작 시 워킹트리에 커밋 안 된 변경
   110개 항목이 staged/unstaged로 쌓여 있었다. 정체: 이전 세션이 Repository 패턴 +
   DI + supabase 전환 + `markdown/`→`docs/` 재구성을 해놓고 커밋하지 않은 WIP.
2. **검증 결과 — 동작함:**
   - `python -m unittest tests.test_repositories` → 21개 통과.
   - DI Facade 실작동: `get_db_manager()`(sqlite)가 `SqliteMeetingRepository` 등
     6개 repo 구현체를 정상 노출.
   - `database/repositories/`에 sqlite + supabase 양쪽 구현체 실존.
   - 유일한 테스트 실패는 `test_diarization_service.py`의 `torch` 미설치(로컬 환경
     문제, AI 파이프라인 의존성) — 코드 결함 아님.
3. **복구 커밋 2개로 보존:**
   - `a81a544` staged 스냅샷(Repository/DI + docs 재구성)
   - `86b87de` unstaged 워킹트리 레이어(Firebase 제거/auth 정리 등 WIP)

## 정정된 그라운드 트루스 (원래 작업 지시서의 전제는 HEAD/구버전 기준이라 틀렸음)

| 지시서 주장 | 실제 (검증됨) |
|---|---|
| 백엔드 Flask | 맞음 |
| 프론트 `frontend/` 단일 React | 맞음 |
| 에이전트 = LangGraph 단일 노드(add_node 1개→END) | 맞음. AI 파이프라인이라 수정 금지 |
| `database/repositories/` 미존재/미구현 | **틀림** — 실존·동작, 21 테스트 통과 |
| 테스트 1개뿐 | **틀림** — `test_repositories.py`(21개) 존재 |
| DB는 SQLite 단일 | **틀림** — `config.DB_TYPE` 기본값 `supabase`, 교체형 |
| `markdown/`↔`docs/` 통합 필요 | **이미 완료** — `markdown/` 없음 |

## 확정된 방향 (사용자 결정)

- **문서:** "실제 구현대로 정확히 기술." 지시서 Phase 3의 'SQLite 단일/미구현' 서술은
  버린다 — 그대로 하면 정확한 문서를 거짓으로 만든다.
- **복구 코드:** 품질 검토 → 유지 → 정리 순서. AI 파이프라인은 그대로 둔다.

## 다음 세션 TODO

1. **품질 검토 (먼저):** 복구된 Repository/DI/supabase 코드가 완성도·일관성 면에서
   멀쩡한지 감사. 특히 86b87de의 unstaged WIP 레이어(Firebase 제거/auth 정리)가
   미완성일 수 있음 — 빌드/동작 확인.
2. **안전 철거:**
   - `genminute-dashboard/`: 코드 참조 0(docs에 디자인 영감 언급만) = 오펀. 삭제 후
     `cd frontend && npm run build` 통과 확인.
   - `experiments_stt/`: `archive/experiments-stt` 브랜치로 분리 후 cleanup에서 제거.
   - `templates/`·`static/js/`: **아직 죽지 않음**. `meetings.py`(index/notes/viewer),
     `auth.py`(login), `live_record.py`(recorder), `admin.py`(테스트 페이지)가
     `render_template` 사용 중. app.py catch-all(`/<path:path>`)과의 실제 도달성을
     앱 구동으로 검증한 뒤에만 삭제 판단.
3. **문서-코드 정합성:** dev_log/README를 실제 구현(supabase 기본·교체형 DB,
   Repository/DI/Facade 실존, 단일노드 LangGraph 에이전트, Flask)에 맞춰 정정.
   깨진 내부 링크 점검.

## 원칙 (유지)

- 파괴적 작업은 근거 확인 → 보고 → 승인 후 실행.
- AI 파이프라인(stt_service, diarization, agent_service, google_auth/calendar) 수정 금지.
- 커밋은 logical 단위 + conventional commits.
