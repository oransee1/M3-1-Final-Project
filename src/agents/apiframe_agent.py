import time
import requests
from pathlib import Path
from src.config import Config

class ApiframeClient:
    BASE_URL = "https://api.apiframe.ai/v2"

    def __init__(self, suno_key: str = None, nano_key: str = None):
        self.suno_key = suno_key or Config.get_suno_key()
        self.nano_key = nano_key or Config.get_nano_key()

    def create_music_task(self, prompt: str, style: str, title: str = "Healing BGM", instrumental: bool = True) -> str:
        """
        Suno 음악 생성을 요청하고 jobId를 반환합니다.
        """
        if not self.suno_key:
            raise ValueError("Apiframe Suno API 키가 설정되지 않았습니다.")

        url = f"{self.BASE_URL}/music/generate"
        headers = {
            "X-API-Key": self.suno_key,
            "Content-Type": "application/json"
        }
        payload = {
            "model": "suno",
            "prompt": prompt,
            "sunoParams": {
                "custom_mode": True,
                "model_version": "V5_5",
                "style": style,
                "title": title,
                "instrumental": instrumental
            }
        }

        resp = requests.post(url, json=payload, headers=headers, timeout=30)
        if resp.status_code not in (200, 201, 202):
            raise RuntimeError(f"Suno 작업 생성 실패 (HTTP {resp.status_code}): {resp.text}")

        data = resp.json()
        job_id = data.get("jobId") or data.get("id")
        if not job_id:
            raise RuntimeError(f"응답에서 jobId를 찾을 수 없습니다: {data}")
        return job_id

    def create_image_task(
        self,
        prompt: str,
        model: str = "nano-banana-2",
        aspect_ratio: str = "16:9",
        resolution: str = "4K"
    ) -> str:
        """
        Nano Banana 2 초고화질 4K 이미지 생성을 요청하고 jobId를 반환합니다.
        각 씬 16:9 비율 9장 및 전체 4K(3840x2160) 고해상도 생성을 위해 nanoBananaParams를 적용합니다.
        자막(텍스트), 프레임(테두리), 워터마크가 원천 배제되도록 네거티브 가드를 엄격히 보장합니다.
        """
        if not self.nano_key:
            raise ValueError("Apiframe Nano Banana API 키가 설정되지 않았습니다.")

        # 자막/텍스트/라벨/격자좌표(A1~C3)/숫자 및 프레임/테두리 원천 배제 강제 보장 가드
        neg_guard = (
            "borderless, full bleed, no text, no words, no letters, no numbers, no digits, "
            "no alphanumeric characters, no coordinates, no grid labels, no panel markers, "
            "no scene numbers, no A1, no A2, no A3, no B1, no B2, no B3, no C1, no C2, no C3, "
            "no overlay, no watermark, no logo, no subtitles, no captions, no typography, "
            "no title, no frame, no border, no white borders, no picture frame"
        )
        import re
        clean_prompt = re.sub(r"(?i)\b[A-Ca-c][1-9]\b[:\-\s]*", "", prompt)
        clean_prompt = re.sub(r"(?i)\bgrid storyboard\b", "grid layout of clean landscape scenes without any labels or numbers", clean_prompt)
        clean_prompt = re.sub(r"(?i)\bstoryboard\b", "sequential landscape scenes without any text or labels", clean_prompt)
        if "no coordinates" not in clean_prompt.lower() or "no a1" not in clean_prompt.lower():
            clean_prompt = f"{clean_prompt.rstrip(',. ')}, {neg_guard}"
        elif "no text" not in clean_prompt.lower():
            clean_prompt = f"{clean_prompt.rstrip(',. ')}, {neg_guard}"
        elif "no frame" not in clean_prompt.lower() and "no border" not in clean_prompt.lower():
            clean_prompt = f"{clean_prompt.rstrip(',. ')}, no frame, no border, no white borders, no picture frame"

        # Apiframe API 엄격 제약 조건: prompt <= 2000 characters (초과 시 HTTP 400 Validation Error)
        # 안전 여유폭(마진)을 두어 최대 1950자로 엄격히 제한하고 필수 가드 보존
        MAX_PROMPT_LEN = 1950
        if len(clean_prompt) > MAX_PROMPT_LEN:
            essential_guard = ", borderless full bleed, scenic nature only, no text, no labels, no coordinates, no frame, no borders, no watermark"
            allowed_base_len = MAX_PROMPT_LEN - len(essential_guard) - 5
            truncated = clean_prompt[:allowed_base_len]
            last_comma = truncated.rfind(",")
            if last_comma > allowed_base_len * 0.7:
                truncated = truncated[:last_comma]
            else:
                last_space = truncated.rfind(" ")
                if last_space > allowed_base_len * 0.7:
                    truncated = truncated[:last_space]
            clean_prompt = f"{truncated.rstrip(',. ')}{essential_guard}."

        url = f"{self.BASE_URL}/images/generate"
        headers = {
            "X-API-Key": self.nano_key,
            "Content-Type": "application/json"
        }
        payload = {
            "model": model,
            "prompt": clean_prompt,
            "nanoBananaParams": {
                "aspect_ratio": aspect_ratio,
                "resolution": resolution,
                "output_format": "png"
            }
        }

        resp = requests.post(url, json=payload, headers=headers, timeout=30)
        # 만약 nano-banana-2 모델 호출 시 에러가 발생할 경우 nano-banana-2-lite로 fallback 시도
        if resp.status_code not in (200, 201, 202) and model != "nano-banana-2-lite":
            fallback_payload = dict(payload)
            fallback_payload["model"] = "nano-banana-2-lite"
            resp = requests.post(url, json=fallback_payload, headers=headers, timeout=30)

        if resp.status_code not in (200, 201, 202):
            raise RuntimeError(f"이미지 작업 생성 실패 (HTTP {resp.status_code}): {resp.text}")

        data = resp.json()
        job_id = data.get("jobId") or data.get("id")
        if not job_id:
            raise RuntimeError(f"응답에서 jobId를 찾을 수 없습니다: {data}")
        return job_id

    def poll_job(self, job_id: str, api_key: str, max_wait_sec: int = 400, poll_interval: int = 5, callback=None) -> dict:
        """
        jobId의 완료 여부를 폴링하여 완료 시 결과 dict를 반환합니다.
        """
        url = f"{self.BASE_URL}/jobs/{job_id}"
        headers = {"X-API-Key": api_key}
        start_time = time.time()

        while time.time() - start_time < max_wait_sec:
            try:
                resp = requests.get(url, headers=headers, timeout=20)
                if resp.status_code == 200:
                    data = resp.json()
                    status = data.get("status", "").upper()
                    progress = data.get("progress", 0)

                    if callback:
                        callback(status, progress)

                    if status in ("COMPLETED", "SUCCESS"):
                        return data.get("result", {})
                    elif status in ("FAILED", "ERROR"):
                        error_msg = data.get("error") or "알 수 없는 오류"
                        raise RuntimeError(f"작업 실행 실패 ({job_id}): {error_msg}")
            except requests.RequestException as e:
                if callback:
                    callback(f"연결 재시도 중 ({e})", 0)

            time.sleep(poll_interval)

        raise TimeoutError(f"작업이 {max_wait_sec}초 내에 완료되지 않았습니다 (Job ID: {job_id})")

    @staticmethod
    def download_asset(url: str, save_path: Path, callback=None) -> Path:
        """
        원격 CDN URL로부터 파일을 스트리밍 다운로드합니다.
        """
        save_path.parent.mkdir(parents=True, exist_ok=True)
        with requests.get(url, stream=True, timeout=60) as r:
            r.raise_for_status()
            total_length = int(r.headers.get('content-length', 0))
            downloaded = 0
            with open(save_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if callback and total_length > 0:
                            callback(downloaded, total_length)

        if not save_path.exists() or save_path.stat().st_size == 0:
            raise IOError(f"다운로드된 파일이 비어 있습니다 (0바이트): {url}")

        return save_path
