# 환경 스냅샷

`genminute_stt` conda 환경에 실제로 설치된 패키지의 정확한 버전 목록(`pip freeze` 출력)입니다.
`requirements.txt`는 허용 **범위**만 적으므로, "그때 실제로 무엇이 깔려 있었는지"는 이 파일들로 확인합니다.

| 파일 | 시점 |
|---|---|
| `2026-11-16_before_upgrade.txt` | LangChain 계열 업데이트 직전 |
| `2026-11-16_after_upgrade.txt` | 업데이트 직후 (langgraph 1.2.22, langchain-classic 1.0.8, langchain 1.5.0 등) |

## 사용법

```bash
# 두 시점의 차이 보기
git diff --no-index docs/development/env_snapshots/2026-11-16_before_upgrade.txt docs/development/env_snapshots/2026-11-16_after_upgrade.txt

# 특정 시점으로 되돌리기 (환경을 그 목록과 똑같이 맞춤)
pip install -r docs/development/env_snapshots/2026-11-16_before_upgrade.txt

# 새 스냅샷 남기기 (패키지를 올리거나 내리기 전후에)
pip freeze > docs/development/env_snapshots/YYYY-MM-DD_설명.txt
```
