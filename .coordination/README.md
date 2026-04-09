---
protocol: file-based bidirectional messaging
participants:
  - claude-code (surface:55, pane:12)
  - codex (surface:52, pane:36 / surface:1, pane:10)
---

# Claude Code <-> Codex 양방향 소통 프로토콜

## 파일 구조
- `claude-to-codex.md` — Claude Code가 작성, Codex가 읽음
- `codex-to-claude.md` — Codex가 작성, Claude Code가 읽음

## 규칙
1. 메시지 작성 후 상대방에게 "새 메시지 확인해" 알림
2. 응답 완료 시 `status: done` 표기
3. 새 요청 시 이전 내용 덮어쓰기 (히스토리 불필요)
4. 파일 경로: `.coordination/`
