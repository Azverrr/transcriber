#!/usr/bin/env python3

import argparse
import os
import sys
import tempfile
from pathlib import Path

from faster_whisper import WhisperModel


def is_url(text: str) -> bool:
    return text.startswith("http://") or text.startswith("https://")


def download_audio(url: str) -> Path:
    try:
        import yt_dlp
    except ImportError:
        print("Установите yt-dlp:")
        print("pip install yt-dlp")
        sys.exit(1)

    temp_dir = tempfile.mkdtemp(prefix="transcriber_")

    output_template = os.path.join(temp_dir, "%(title)s.%(ext)s")

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": output_template,
        "quiet": False,
        "noplaylist": True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = Path(ydl.prepare_filename(info))

    return filename


def transcribe(
    input_file: Path,
    output_file: Path,
    model_name: str,
    timestamps: bool,
    device: str,
    compute_type: str,
):
    print(f"Загрузка модели {model_name}...")
    print(f"Устройство: {device} ({compute_type})")

    model = WhisperModel(
        model_name,
        device=device,
        compute_type=compute_type,
    )

    print("Распознавание...\n")

    segments, info = model.transcribe(
        str(input_file),
        beam_size=5,
        vad_filter=True,
    )

    print(f"Язык: {info.language}")
    print()

    with output_file.open("w", encoding="utf-8") as f:
        for segment in segments:

            text = segment.text.strip()

            if timestamps:
                h = int(segment.start) // 3600
                m = (int(segment.start) % 3600) // 60
                s = int(segment.start) % 60

                line = f"[{h:02}:{m:02}:{s:02}] {text}"
            else:
                line = text

            print(line)
            f.write(line + "\n")

    print()
    print("Готово.")
    print(output_file.resolve())


def main():
    parser = argparse.ArgumentParser(
        description="Транскрибация видео и аудио через Faster-Whisper"
    )

    parser.add_argument(
        "source",
        help="Файл или YouTube URL",
    )

    parser.add_argument(
        "--model",
        default="medium",
        choices=["small", "medium", "large-v3"],
        help="Модель Whisper",
    )

    parser.add_argument(
        "--timestamps",
        action="store_true",
        help="Добавлять тайм-коды",
    )

    parser.add_argument(
        "--output-dir",
        default=None,
        help="Директория для сохранения результата (по умолчанию — рядом с исходным файлом или текущая)",
    )

    parser.add_argument(
        "--device",
        default="cpu",
        choices=["cpu", "cuda", "auto"],
        help="Устройство для вычислений: cpu, cuda или auto (по умолчанию cpu)",
    )

    parser.add_argument(
        "--compute-type",
        default=None,
        help="Тип вычислений: int8 (CPU), float16 (GPU), int8_float16 и др. (по умолчанию подбирается под устройство)",
    )

    args = parser.parse_args()

    # Автоопределение устройства
    device = args.device
    if device == "auto":
        try:
            import ctranslate2
            device = "cuda" if ctranslate2.get_cuda_device_count() > 0 else "cpu"
        except Exception:
            device = "cpu"

    # Автоопределение compute_type
    compute_type = args.compute_type
    if compute_type is None:
        compute_type = "float16" if device == "cuda" else "int8"

    if is_url(args.source):
        print("Скачивание аудио...")
        source = download_audio(args.source)
    else:
        source = Path(args.source)

    if not source.exists():
        print("Файл не найден.")
        sys.exit(1)

    # Определяем директорию для результата
    if args.output_dir:
        out_dir = Path(args.output_dir)
    elif is_url(args.source):
        out_dir = Path.cwd()
    else:
        out_dir = source.parent

    output = out_dir / (source.stem + ".txt")

    transcribe(
        source,
        output,
        args.model,
        args.timestamps,
        device,
        compute_type,
    )


if __name__ == "__main__":
    main()
