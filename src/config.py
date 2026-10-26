import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import imageio_ffmpeg

# Project Root Directory & PyInstaller Runtime Directory
if getattr(sys, "frozen", False):
    BASE_DIR = Path(sys.executable).resolve().parent
    BUNDLE_DIR = Path(getattr(sys, "_MEIPASS", __file__)).resolve()
else:
    BASE_DIR = Path(__file__).resolve().parent.parent
    BUNDLE_DIR = BASE_DIR

# Desktop Directory Finder (Windows 바탕화면 경로 자동 탐색)
def get_desktop_dir() -> Path:
    desktop = Path.home() / "Desktop"
    if desktop.exists():
        return desktop
    onedrive_desktop = Path.home() / "OneDrive" / "Desktop"
    if onedrive_desktop.exists():
        return onedrive_desktop
    onedrive_kr = Path.home() / "OneDrive" / "바탕 화면"
    if onedrive_kr.exists():
        return onedrive_kr
    return desktop

# Output Directory (바탕화면 / Team-FiinalProject / output)
DESKTOP_DIR = get_desktop_dir()
OUTPUT_DIR = DESKTOP_DIR / "Team-FiinalProject" / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Application Icon
ICON_PATH = BUNDLE_DIR / "icon.png" if (BUNDLE_DIR / "icon.png").exists() else BASE_DIR / "icon.png"

# Thumbnail Designer Directory & Standalone Executable
THUMBNAIL_DESIGNER_DIR = BASE_DIR / "Thumbnail_Designer-Program"
if not THUMBNAIL_DESIGNER_DIR.exists() and (BUNDLE_DIR / "Thumbnail_Designer-Program").exists():
    THUMBNAIL_DESIGNER_DIR = BUNDLE_DIR / "Thumbnail_Designer-Program"
if not THUMBNAIL_DESIGNER_DIR.exists():
    _dev_fallback = Path(r"C:\Users\OWNER\PycharmProjects\01코디세이개발\Team-FiinalProject\M3-1_AI Domus\Thumbnail_Designer-Program")
    if _dev_fallback.exists():
        THUMBNAIL_DESIGNER_DIR = _dev_fallback

THUMBNAIL_DESIGNER_EXE = None
for cand_exe in [
    BUNDLE_DIR / "Thumbnail_Designer_Pro.exe",
    BASE_DIR / "Thumbnail_Designer_Pro.exe",
    THUMBNAIL_DESIGNER_DIR / "dist" / "Thumbnail_Designer_Pro.exe",
    THUMBNAIL_DESIGNER_DIR / "Thumbnail_Designer_Pro.exe",
]:
    if cand_exe.exists():
        THUMBNAIL_DESIGNER_EXE = cand_exe
        break

# Load environment variables (.env)
ENV_FILE = BASE_DIR / ".env"
if not ENV_FILE.exists() and (BUNDLE_DIR / ".env").exists():
    load_dotenv(BUNDLE_DIR / ".env")
load_dotenv(ENV_FILE, override=True)

class Config:
    @staticmethod
    def get_gemini_key() -> str:
        key = os.getenv("GEMINI_API_KEY", "").strip()
        if not key:
            key_file = THUMBNAIL_DESIGNER_DIR / "gemini_api_key.txt"
            if key_file.exists():
                try:
                    key = key_file.read_text(encoding="utf-8").strip()
                except Exception:
                    pass
        return key

    @staticmethod
    def get_chatbot_key() -> str:
        key = os.getenv("GEMINI_CHATBOT_API_KEY", "").strip()
        if not key:
            key_file = THUMBNAIL_DESIGNER_DIR / "gemini_api_key.txt"
            if key_file.exists():
                try:
                    key = key_file.read_text(encoding="utf-8").strip()
                except Exception:
                    pass
        if not key:
            key = Config.get_gemini_key()
        return key

    @staticmethod
    def get_suno_key() -> str:
        return os.getenv("APIFRAME_SUNO_KEY", "").strip()

    @staticmethod
    def get_nano_key() -> str:
        return os.getenv("APIFRAME_NANO_KEY", "").strip()

    @staticmethod
    def set_keys(gemini_key: str, suno_key: str, nano_key: str, chatbot_key: str = None):
        if chatbot_key is None:
            chatbot_key = Config.get_chatbot_key()
        with open(ENV_FILE, "w", encoding="utf-8") as f:
            f.write(f"GEMINI_API_KEY={gemini_key}\n")
            if chatbot_key:
                f.write(f"GEMINI_CHATBOT_API_KEY={chatbot_key}\n")
            f.write(f"APIFRAME_SUNO_KEY={suno_key}\n")
            f.write(f"APIFRAME_NANO_KEY={nano_key}\n")
        # Thumbnail_Designer-Program gemini_api_key.txt 동기화 (쳇봇용 키 우선 동기화)
        sync_key = chatbot_key or gemini_key
        if sync_key:
            try:
                THUMBNAIL_DESIGNER_DIR.mkdir(parents=True, exist_ok=True)
                (THUMBNAIL_DESIGNER_DIR / "gemini_api_key.txt").write_text(sync_key, encoding="utf-8")
            except Exception:
                pass
        # Reload
        load_dotenv(ENV_FILE, override=True)

    @staticmethod
    def get_ffmpeg_path() -> str:
        try:
            return imageio_ffmpeg.get_ffmpeg_exe()
        except Exception:
            return "ffmpeg"
