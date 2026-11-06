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

    # 썸네일 디자이너(Thumbnail_Designer_Pro.exe) 최신 소스 반영 빌드
    thumbnail_dir = project_root / "Thumbnail_Designer-Program"
    thumbnail_spec = thumbnail_dir / "Thumbnail_Designer_Pro.spec"
    thumbnail_exe = thumbnail_dir / "dist" / "Thumbnail_Designer_Pro.exe"

    if thumbnail_spec.exists():
        print("[1.5/3] Thumbnail_Designer_Pro.exe 빌드 및 최신화 중...")
        try:
            subprocess.check_call(
                [sys.executable, "-m", "PyInstaller", "Thumbnail_Designer_Pro.spec", "--noconfirm", "--clean"],
                cwd=thumbnail_dir
            )
            # 썸네일 디자이너 빌드 디렉토리 내 불필요한 폴더/로그 정리
            for unwanted in ["exports", "projects", "uploads"]:
                u_path = thumbnail_dir / "dist" / unwanted
                if u_path.exists() and u_path.is_dir() and not any(u_path.iterdir()):
                    try:
                        u_path.rmdir()
                    except Exception:
                        pass
            u_log = thumbnail_dir / "dist" / "thumbnail_designer.log"
            if u_log.exists():
                try:
                    u_log.unlink()
                except Exception:
                    pass
        except Exception as e:
            print(f"  [WARN] Thumbnail_Designer_Pro 빌드 경고 (기존 바이너리 사용): {e}")

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
    out_exe = dist_dir / 'AIDomusMusicStudio.exe'
    print(f"[3/3] 빌드 완료! 실행 파일 위치: {out_exe}")
    
    # 바탕화면 Team-FiinalProject 배포 폴더 자동 업데이트
    deploy_dir = Path.home() / "Desktop" / "Team-FiinalProject"
    if deploy_dir.exists() and out_exe.exists():
        import shutil
        target_exe = deploy_dir / "AIDomusMusicStudio.exe"
        try:
            shutil.copy2(out_exe, target_exe)
            print(f"  [OK] Deploy to: {target_exe}")

            # 배포 폴더 내 불필요한 폴더들(exports, projects, uploads) 및 로그 파일 자동 정리
            for unwanted_folder in ["exports", "projects", "uploads"]:
                uf_path = deploy_dir / unwanted_folder
                if uf_path.exists() and uf_path.is_dir() and not any(uf_path.iterdir()):
                    try:
                        uf_path.rmdir()
                        print(f"  [CLEANUP] 배포 폴더의 빈 폴더 제거 완료: {unwanted_folder}")
                    except Exception:
                        pass
            unwanted_log = deploy_dir / "thumbnail_designer.log"
            if unwanted_log.exists():
                try:
                    unwanted_log.unlink()
                    print("  [CLEANUP] 배포 폴더의 thumbnail_designer.log 파일 제거 완료")
                except Exception:
                    pass
        except Exception as e:
            print(f"  [ERROR] Deploy failed: {e}")
    print("==================================================")

if __name__ == "__main__":
    build()
