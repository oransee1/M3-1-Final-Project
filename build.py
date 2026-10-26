import os
import sys
import subprocess
from pathlib import Path

def build():
    print("==================================================")
    print("  AI Domus Music Studio - Standalone .exe Builder")
    print("==================================================")

    # 1. PyInstaller 확인 및 설치
    try:
        import PyInstaller
        print("[1/3] PyInstaller 감지됨.")
    except ImportError:
        print("[1/3] PyInstaller 설치 중...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])

    # 2. 빌드 옵션 구성
    project_root = Path(__file__).resolve().parent
    main_script = project_root / "main.py"
    dist_dir = project_root / "dist"
    build_dir = project_root / "build"

    thumbnail_exe = project_root / "Thumbnail_Designer-Program" / "dist" / "Thumbnail_Designer_Pro.exe"

    cmd = [
        sys.executable,
        "-m", "PyInstaller",
        "--name=AIDomusMusicStudio",
        "--onefile",
        "--windowed",
        "--noconfirm",
        "--clean",
        f"--paths={project_root}",
        "--icon=icon.ico",
        "--add-data=.env;.",
        "--add-data=icon.png;.",
        "--add-data=icon.ico;.",
    ]

    if thumbnail_exe.exists():
        cmd.append(f"--add-binary={thumbnail_exe};.")

    cmd.extend([
        "--collect-all=imageio_ffmpeg",
        "--collect-all=google.genai",
        "--hidden-import=PyQt5",
        "--hidden-import=PyQt5.QtCore",
        "--hidden-import=PyQt5.QtGui",
        "--hidden-import=PyQt5.QtWidgets",
        "--hidden-import=dotenv",
        "--hidden-import=PIL",
        "--hidden-import=numpy",
        str(main_script)
    ])

    print("[2/3] PyInstaller 빌드 실행 중 (수 분 소요)...")
    print(f"명령어: {' '.join(cmd)}")
    subprocess.check_call(cmd, cwd=project_root)

    print("==================================================")
    print(f"[3/3] 빌드 완료! 실행 파일 위치: {dist_dir / 'AIDomusMusicStudio.exe'}")
    print("==================================================")

if __name__ == "__main__":
    build()
