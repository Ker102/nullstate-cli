#!/usr/bin/env bash
set -euo pipefail

CONTAINER_NAME="${CONTAINER_NAME:-nullstate-red-qwen-vllm}"
IMAGE="${IMAGE:-vllm/vllm-openai-rocm:latest}"
MODEL_ID="${MODEL_ID:-Qwen/Qwen3-4B-Instruct-2507}"
SERVED_MODEL_NAME="${SERVED_MODEL_NAME:-nullstate-qwen3-4b}"
HOST_PORT="${HOST_PORT:-8001}"
CONTAINER_PORT="${CONTAINER_PORT:-8000}"
MAX_MODEL_LEN="${MAX_MODEL_LEN:-32768}"
GPU_MEMORY_UTILIZATION="${GPU_MEMORY_UTILIZATION:-0.40}"

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
    --enable-prompt-tokens-details

echo "Started ${CONTAINER_NAME} on 127.0.0.1:${HOST_PORT}"
echo "Model: ${SERVED_MODEL_NAME} (${MODEL_ID})"
