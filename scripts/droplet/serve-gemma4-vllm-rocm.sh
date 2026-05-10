#!/usr/bin/env bash
set -euo pipefail

CONTAINER_NAME="${CONTAINER_NAME:-nullstate-blue-gemma4}"
IMAGE="${IMAGE:-vllm/vllm-openai-rocm:latest}"
MODEL_ID="${MODEL_ID:-google/gemma-4-E4B-it}"
SERVED_MODEL_NAME="${SERVED_MODEL_NAME:-nullstate-gemma4-e4b}"
HOST_PORT="${HOST_PORT:-8002}"
CONTAINER_PORT="${CONTAINER_PORT:-8000}"
MAX_MODEL_LEN="${MAX_MODEL_LEN:-32768}"
GPU_MEMORY_UTILIZATION="${GPU_MEMORY_UTILIZATION:-0.90}"

mkdir -p "${HOME}/.cache/huggingface"

docker rm -f "${CONTAINER_NAME}" >/dev/null 2>&1 || true
docker pull "${IMAGE}"

docker run -d \
  --name "${CONTAINER_NAME}" \
  --ipc=host \
  --privileged \
  --cap-add=CAP_SYS_ADMIN \
  --device=/dev/kfd \
  --device=/dev/dri \
  --group-add=video \
  --cap-add=SYS_PTRACE \
  --security-opt seccomp=unconfined \
  --shm-size 16G \
  -p "127.0.0.1:${HOST_PORT}:${CONTAINER_PORT}" \
  -e "HF_TOKEN=${HF_TOKEN:-}" \
  -e VLLM_ROCM_USE_AITER=1 \
  -v "${HOME}/.cache/huggingface:/root/.cache/huggingface" \
  "${IMAGE}" \
    --model "${MODEL_ID}" \
    --served-model-name "${SERVED_MODEL_NAME}" \
    --host 0.0.0.0 \
    --port "${CONTAINER_PORT}" \
    --dtype bfloat16 \
    --max-model-len "${MAX_MODEL_LEN}" \
    --gpu-memory-utilization "${GPU_MEMORY_UTILIZATION}" \
    --enable-force-include-usage \
    --enable-prompt-tokens-details \
    --limit-mm-per-prompt '{"image": 0, "audio": 0}'

echo "Started ${CONTAINER_NAME} on 127.0.0.1:${HOST_PORT}"
echo "Model: ${SERVED_MODEL_NAME} (${MODEL_ID})"
