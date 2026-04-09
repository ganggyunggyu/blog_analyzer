#!/bin/zsh
set -euo pipefail
OUT_DIR="/Users/ganggyunggyu/Programing/21lab/text-gen-hub/test-manuscripts/blog_filler_pet_claude_sonnet/20260331_181840"
SYSTEM_PROMPT=$(cat "$OUT_DIR/system_prompt.txt")
for i in {01..10}; do
  echo "[run] $i"
  cmux claude-teams -p --model claude-sonnet-4-6 --system-prompt "$SYSTEM_PROMPT" "$(cat "$OUT_DIR/input_${i}.txt")" > "$OUT_DIR/${i}_시바견.txt"
  echo "[done] $i"
done
