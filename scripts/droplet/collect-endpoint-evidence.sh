#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${1:?Usage: collect-endpoint-evidence.sh <base-url> <model-name> [output-dir]}"
MODEL_NAME="${2:?Usage: collect-endpoint-evidence.sh <base-url> <model-name> [output-dir]}"
OUTPUT_DIR="${3:-/opt/nullstate/evidence}"
STAMP="$(date -u +%Y%m%d-%H%M%S)"
RUN_DIR="${OUTPUT_DIR}/endpoint-${MODEL_NAME}-${STAMP}"

mkdir -p "${RUN_DIR}"

curl -sS "${BASE_URL%/}/v1/models" | tee "${RUN_DIR}/models.json"
curl -sS "${BASE_URL%/}/metrics" | tee "${RUN_DIR}/metrics.prom" >/dev/null || true

curl -sS "${BASE_URL%/}/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -d "{
    \"model\": \"${MODEL_NAME}\",
    \"messages\": [
      {\"role\": \"system\", \"content\": \"You are a concise cloud security assistant.\"},
      {\"role\": \"user\", \"content\": \"Explain why public object storage is risky in one sentence.\"}
    ],
    \"max_tokens\": 80,
    \"temperature\": 0.2
  }" | tee "${RUN_DIR}/chat-completion.json"

{
  echo "=== date ==="
  date -Is
  echo
  echo "=== docker containers ==="
  docker ps --format "table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}"
  echo
  echo "=== amd-smi ==="
  amd-smi static --asic --vram --driver 2>/dev/null || amd-smi 2>/dev/null || true
  echo
  echo "=== rocm-smi ==="
  rocm-smi 2>/dev/null || true
} | tee "${RUN_DIR}/host-snapshot.txt"

echo "Wrote ${RUN_DIR}"
