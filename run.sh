#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Проверяем, нужен ли GPU
USE_GPU=false
if [[ "${1:-}" == "--gpu" ]]; then
    USE_GPU=true
    shift
fi

if $USE_GPU; then
    IMAGE="transcriber:gpu"
    DOCKERFILE="Dockerfile.gpu"
else
    IMAGE="transcriber:latest"
    DOCKERFILE="Dockerfile"
fi

# Собрать образ, если ещё нет
if ! docker image inspect "$IMAGE" &>/dev/null; then
    echo "🐳 Сборка Docker-образа ($DOCKERFILE)..."
    docker build -t "$IMAGE" -f "$SCRIPT_DIR/$DOCKERFILE" "$SCRIPT_DIR"
fi

# Разбираем аргументы: первый не-опциональный — это source
SOURCE=""
PASSTHROUGH=()
while [[ $# -gt 0 ]]; do
    if [[ "$1" != -* && -z "$SOURCE" ]]; then
        SOURCE="$1"
    else
        PASSTHROUGH+=("$1")
    fi
    shift
done

if [[ -z "$SOURCE" ]]; then
    echo "Использование: transcribe [--gpu] <файл|URL> [--model ...] [--timestamps] [--output-dir DIR] [--device ...]"
    exit 1
fi

# Монтирование
MOUNT_ARGS=()

if [[ "$SOURCE" =~ ^https?:// ]]; then
    # URL: результат сохранится в текущую директорию
    MOUNT_ARGS+=(-v "$(pwd):/out")
    PASSTHROUGH+=(--output-dir /out)
else
    # Локальный файл
    SOURCE_REAL="$(realpath "$SOURCE")"
    SOURCE_DIR="$(dirname "$SOURCE_REAL")"
    SOURCE_NAME="$(basename "$SOURCE_REAL")"
    MOUNT_ARGS+=(-v "$SOURCE_DIR:/data:ro")
    MOUNT_ARGS+=(-v "$(pwd):/out")
    SOURCE="/data/$SOURCE_NAME"
    PASSTHROUGH+=(--output-dir /out)
fi

# GPU-проброс
if $USE_GPU; then
    MOUNT_ARGS+=(--gpus all)
    # Если пользователь не указал явно --device, форсируем cuda
    if [[ ! " ${PASSTHROUGH[*]} " =~ " --device " ]]; then
        PASSTHROUGH+=(--device cuda)
    fi
fi

docker run --rm "${MOUNT_ARGS[@]}" "$IMAGE" "$SOURCE" "${PASSTHROUGH[@]}"
