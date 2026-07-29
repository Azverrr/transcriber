# Transcriber

Транскрибация аудио и видео в текст через [Faster-Whisper](https://github.com/SYSTRAN/faster-whisper) в Docker-контейнере. Поддерживает CPU и GPU (**только NVIDIA**).

## Требования

- Docker
- Для GPU: видеокарта **NVIDIA** + [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html)

### AMD Radeon / Intel GPU

GPU-образ (`Dockerfile.gpu`) работает **только с NVIDIA** (CUDA). Для AMD и Intel — используй CPU-образ:

```bash
transcribe video.mp4 --model medium
```

## Быстрый старт

```bash
# CPU
docker build -t transcriber:latest .

# GPU (только NVIDIA)
docker build -t transcriber:gpu -f Dockerfile.gpu .

# Или используй обёртку — соберёт автоматически при первом запуске
```

Для удобства добавь `run.sh` в PATH:

```bash
ln -s "$(pwd)/run.sh" ~/.local/bin/transcribe
```

## Использование

```bash
transcribe [--gpu] <файл или URL> [опции]
```

### Примеры

```bash
# CPU (по умолчанию)
transcribe lecture.mp4 --timestamps

# Быстро, моделью small
transcribe podcast.mp3 --model small

# GPU (NVIDIA)
transcribe --gpu interview.mp4 --model large-v3 --timestamps

# YouTube
transcribe "https://www.youtube.com/watch?v=..." --timestamps

# YouTube на GPU (NVIDIA)
transcribe --gpu "https://www.youtube.com/watch?v=..." --model medium
```

### Опции обёртки

| Опция | Описание |
|---|---|
| `--gpu` | Использовать GPU-образ (`transcriber:gpu`) с `--gpus all` (NVIDIA) |

### Опции скрипта

| Опция | Значения | По умолчанию | Описание |
|---|---|---|---|
| `--model` | `small`, `medium`, `large-v3` | `medium` | Размер модели |
| `--timestamps` | флаг | выкл | Добавлять тайм-коды `[чч:мм:сс]` |
| `--output-dir` | путь | рядом с файлом | Куда сохранить `.txt` |
| `--device` | `cpu`, `cuda`, `auto` | `cpu` | Устройство вычислений |
| `--compute-type` | `int8`, `float16`, `int8_float16` | авто | Тип вычислений (int8 для CPU, float16 для GPU) |

При `--gpu` обёртка автоматически добавляет `--device cuda`, если не указано иное.

### Результат

Скрипт создаёт `.txt` с тем же именем, что у исходного файла:

```
lecture.mp4  →  lecture.txt
```

## Модели

| Модель | Скорость (CPU) | Скорость (GPU) | Точность | ОЗУ |
|---|---|---|---|---|
| `small` | Быстро | Очень быстро | Хорошая | ~2 ГБ |
| `medium` | Умеренно | Быстро | Отличная | ~5 ГБ |
| `large-v3` | Медленно | Умеренно | Максимальная | ~10 ГБ |

## Сборка образов

```bash
# CPU
docker build -t transcriber:latest .

# GPU (NVIDIA)
docker build -t transcriber:gpu -f Dockerfile.gpu .
```

## Ручной запуск без обёртки

```bash
# CPU: локальный файл
docker run --rm \
  -v "$(dirname "$(realpath video.mp4)"):/data:ro" \
  -v "$(pwd):/out" \
  transcriber:latest \
  /data/video.mp4 --output-dir /out --timestamps

# GPU (NVIDIA): YouTube
docker run --rm --gpus all \
  -v "$(pwd):/out" \
  transcriber:gpu \
  "https://youtube.com/..." --output-dir /out --device cuda
```
