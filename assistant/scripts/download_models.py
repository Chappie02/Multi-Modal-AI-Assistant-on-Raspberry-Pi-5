import os
import pathlib
import sys
import urllib.request


ROOT = pathlib.Path(__file__).resolve().parents[1]
MODELS_DIR = ROOT / "models"
MODELS_DIR.mkdir(parents=True, exist_ok=True)


def download(url: str, dest: pathlib.Path) -> None:
    if dest.exists():
        print(f"[skip] {dest} already exists")
        return
    print(f"[download] {url} -> {dest}")
    dest.parent.mkdir(parents=True, exist_ok=True)
    try:
        urllib.request.urlretrieve(url, dest)
    except Exception as e:
        print(f"Failed to download {url}: {e}", file=sys.stderr)


def main() -> None:
    # LLM – tiny GGUF model suitable for Pi 5
    # You can replace this with any GGUF path you prefer.
    llm_url = (
        "https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF/"
        "resolve/main/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf"
    )
    download(llm_url, MODELS_DIR / "llm.gguf")

    # YOLOv8 nano → models/yolo.pt
    yolo_url = (
        "https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8n.pt"
    )
    download(yolo_url, MODELS_DIR / "yolo.pt")

    # Vosk STT small English model → models/vosk/
    # Official mirror from alphacephei.
    vosk_url = (
        "https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip"
    )
    vosk_zip = MODELS_DIR / "vosk-model-small-en-us-0.15.zip"
    download(vosk_url, vosk_zip)

    # Unpack Vosk if possible
    try:
        import zipfile

        if vosk_zip.exists():
            target_dir = MODELS_DIR / "vosk"
            if not target_dir.exists():
                print(f"[unzip] {vosk_zip} -> {target_dir}")
                with zipfile.ZipFile(vosk_zip, "r") as zf:
                    zf.extractall(MODELS_DIR)
                # Rename extracted folder to models/vosk
                for item in MODELS_DIR.iterdir():
                    if (
                        item.is_dir()
                        and item.name.startswith("vosk-model-")
                        and item.name != "vosk"
                    ):
                        item.rename(target_dir)
                        break
    except Exception as e:
        print(f"Failed to unpack Vosk model: {e}", file=sys.stderr)


if __name__ == "__main__":
    main()

