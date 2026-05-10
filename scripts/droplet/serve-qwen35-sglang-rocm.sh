#!/usr/bin/env bash
set -euo pipefail

CONTAINER_NAME="${CONTAINER_NAME:-nullstate-red-qwen35}"
IMAGE="${IMAGE:-lmsysorg/sglang:v0.5.9-rocm720-mi30x}"
MODEL_ID="${MODEL_ID:-Qwen/Qwen3.5-9B}"
SERVED_MODEL_NAME="${SERVED_MODEL_NAME:-nullstate-qwen35-9b}"
HOST_PORT="${HOST_PORT:-8001}"
CONTAINER_PORT="${CONTAINER_PORT:-30000}"
MEM_FRACTION_STATIC="${MEM_FRACTION_STATIC:-0.8}"
SGLANG_USE_AITER="${SGLANG_USE_AITER:-0}"

mkdir -p "${HOME}/.cache/huggingface"

docker rm -f "${CONTAINER_NAME}" >/dev/null 2>&1 || true
docker pull "${IMAGE}"

docker run -d \
  --name "${CONTAINER_NAME}" \
  --ipc=host \
  --privileged \
  --device=/dev/kfd \
  --device=/dev/dri \
  --group-add=video \
  --cap-add=SYS_PTRACE \
  --security-opt seccomp=unconfined \
  --shm-size 16G \
  -p "127.0.0.1:${HOST_PORT}:${CONTAINER_PORT}" \
  -e "HF_TOKEN=${HF_TOKEN:-}" \
  -e "SGLANG_USE_AITER=${SGLANG_USE_AITER}" \
  -v "${HOME}/.cache/huggingface:/root/.cache/huggingface" \
  "${IMAGE}" \
  python3 -m sglang.launch_server \
    --model-path "${MODEL_ID}" \
    --served-model-name "${SERVED_MODEL_NAME}" \
    --host 0.0.0.0 \
    --port "${CONTAINER_PORT}" \
    --tp-size 1 \
    --attention-backend triton \
    --reasoning-parser qwen3 \
    --tool-call-parser qwen3_coder \
    --mem-fraction-static "${MEM_FRACTION_STATIC}" \
    --trust-remote-code

echo "Started ${CONTAINER_NAME} on 127.0.0.1:${HOST_PORT}"
echo "Model: ${SERVED_MODEL_NAME} (${MODEL_ID})"
