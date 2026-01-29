from __future__ import annotations

from typing import Any, Dict, Optional

from google import genai
from google.genai import types

from config import GEMINI_API_KEY, GROK_API_KEY, RECRAFT_API_KEY
from utils.logger import console


def get_image_service_type(model_name: str) -> str:
    """이미지 생성 모델명으로 서비스 타입 결정"""
    if model_name.startswith("grok"):
        return "grok"
    elif model_name.startswith("imagen"):
        return "imagen"
    elif "flash" in model_name and "image" in model_name:
        return "gemini-flash"
    elif model_name.startswith("recraft"):
        return "recraft"
    else:
        raise ValueError(f"지원하지 않는 이미지 생성 모델: {model_name}")


def _generate_single_grok_image(
    client: Any,
    model_name: str,
    prompt: str,
    keyword: str,
    index: int,
) -> Optional[str]:
    import requests
    from utils.s3_uploader import upload_image_to_s3

    console.print(f"  [dim]#{index}[/dim] 생성 중...", end="\r")

    try:
        response = client.image.sample(
            model=model_name,
            prompt=prompt,
            image_format="url",
        )

        grok_url = getattr(response, "url", None)
        if not grok_url:
            console.print(f"  [yellow]#{index}[/yellow] URL 없음")
            return None

        img_response = requests.get(grok_url, timeout=30)
        if img_response.status_code != 200:
            console.print(f"  [yellow]#{index}[/yellow] 다운로드 실패")
            return None

        content_type = img_response.headers.get("Content-Type", "image/png")
        s3_url = upload_image_to_s3(
            image_bytes=img_response.content,
            keyword=keyword,
            content_type=content_type,
        )

        if s3_url:
            console.print(f"  [green]#{index}[/green] ✓ 완료           ")
        return s3_url

    except Exception as e:
        console.print(f"  [red]#{index}[/red] 실패: {e}")
        return None


def _generate_single_imagen_image(
    client: Any,
    model_name: str,
    prompt: str,
    keyword: str,
    index: int,
) -> Optional[str]:
    from io import BytesIO
    from utils.s3_uploader import upload_image_to_s3

    console.print(f"  [dim]#{index}[/dim] 생성 중...", end="\r")

    try:
        response = client.models.generate_images(
            model=model_name,
            prompt=prompt,
            config=types.GenerateImagesConfig(number_of_images=1),
        )

        if not response.generated_images:
            console.print(f"  [yellow]#{index}[/yellow] 생성 실패")
            return None

        img = response.generated_images[0].image

        if hasattr(img, "_pil_image") and img._pil_image:
            buffer = BytesIO()
            img._pil_image.save(buffer, format="PNG")
            image_bytes = buffer.getvalue()
        elif hasattr(img, "image_bytes"):
            image_bytes = img.image_bytes
        elif hasattr(img, "_image_bytes"):
            image_bytes = img._image_bytes
        elif hasattr(img, "data"):
            image_bytes = img.data
        else:
            image_bytes = bytes(img) if isinstance(img, (bytes, bytearray)) else None

        if not image_bytes:
            console.print(f"  [yellow]#{index}[/yellow] 바이트 추출 실패")
            return None

        s3_url = upload_image_to_s3(
            image_bytes=image_bytes,
            keyword=keyword,
            content_type="image/png",
        )

        if s3_url:
            console.print(f"  [green]#{index}[/green] ✓ 완료           ")
        return s3_url

    except Exception as e:
        console.print(f"  [red]#{index}[/red] 실패: {e}")
        return None


def _generate_single_gemini_flash_image(
    client: Any,
    model_name: str,
    prompt: str,
    keyword: str,
    index: int,
) -> Optional[str]:
    from io import BytesIO
    from utils.s3_uploader import upload_image_to_s3

    console.print(f"  [dim]#{index}[/dim] 생성 중...", end="\r")

    try:
        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE", "TEXT"],
            ),
        )

        parts = getattr(response, "parts", None)

        if not parts and hasattr(response, "candidates") and response.candidates:
            parts = response.candidates[0].content.parts

        if not parts:
            console.print(f"  [yellow]#{index}[/yellow] 응답에 parts 없음 (정책 거부 가능)")
            return None

        for part in parts:
            if hasattr(part, "inline_data") and part.inline_data is not None:
                image_bytes = None

                image_data = part.inline_data
                if hasattr(image_data, "data"):
                    image_bytes = image_data.data
                elif hasattr(image_data, "_pb") and hasattr(image_data._pb, "data"):
                    image_bytes = image_data._pb.data

                if not image_bytes and hasattr(part, "as_image"):
                    try:
                        from PIL import Image

                        image = part.as_image()
                        if isinstance(image, Image.Image):
                            buffer = BytesIO()
                            image.save(buffer, "PNG")
                            image_bytes = buffer.getvalue()
                    except Exception:
                        pass

                if not image_bytes:
                    continue

                s3_url = upload_image_to_s3(
                    image_bytes=image_bytes,
                    keyword=keyword,
                    content_type="image/png",
                )

                if s3_url:
                    console.print(f"  [green]#{index}[/green] ✓ 완료           ")
                    return s3_url

        console.print(f"  [yellow]#{index}[/yellow] 이미지 없음")
        return None

    except Exception as e:
        console.print(f"  [red]#{index}[/red] 실패: {e}")
        return None


def _generate_single_recraft_image(
    api_key: str,
    model_name: str,
    prompt: str,
    keyword: str,
    index: int,
    style: str = "realistic_image",
    size: str = "1280x720",
) -> Optional[str]:
    import json
    import requests
    from utils.s3_uploader import upload_image_to_s3

    console.print(f"  [dim]#{index}[/dim] 생성 중...", end="\r")

    try:
        url = "https://external.api.recraft.ai/v1/images/generations"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        data = {
            "model": model_name,
            "prompt": prompt,
            "style": style,
            "size": size,
            "n": 1,
        }

        response = requests.post(url, headers=headers, data=json.dumps(data), timeout=60)

        if response.status_code != 200:
            console.print(f"  [red]#{index}[/red] API 오류: {response.status_code}")
            return None

        result = response.json()
        image_url = result.get("data", [{}])[0].get("url")

        if not image_url:
            console.print(f"  [yellow]#{index}[/yellow] 이미지 URL 없음")
            return None

        img_response = requests.get(image_url, timeout=30)
        if img_response.status_code != 200:
            console.print(f"  [red]#{index}[/red] 이미지 다운로드 실패")
            return None

        image_bytes = img_response.content

        s3_url = upload_image_to_s3(
            image_bytes=image_bytes,
            keyword=keyword,
            content_type="image/png",
        )

        if s3_url:
            console.print(f"  [green]#{index}[/green] ✓ 완료           ")
            return s3_url

        console.print(f"  [yellow]#{index}[/yellow] S3 업로드 실패")
        return None

    except Exception as e:
        console.print(f"  [red]#{index}[/red] 실패: {e}")
        return None


def call_image_ai(
    model_name: str,
    prompt: str,
    keyword: str = "generated",
) -> Optional[Dict[str, float | str]]:
    """
    단일 이미지 생성 AI 호출 함수

    Args:
        model_name: 모델 이름 (예: "grok-2-image", "imagen-4.0-generate-001")
        prompt: 이미지 생성 프롬프트
        keyword: S3 저장 폴더명

    Returns:
        {"url": "..."} 또는 None (실패 시)
    """
    service_type = get_image_service_type(model_name)

    if service_type == "grok":
        if not GROK_API_KEY:
            raise ValueError("GROK_API_KEY가 설정되어 있지 않습니다.")

        from xai_sdk import Client

        client = Client(api_key=GROK_API_KEY)

        s3_url = _generate_single_grok_image(client, model_name, prompt, keyword, 1)
        if s3_url:
            return {"url": s3_url, "cost": 0.07}
        return None

    elif service_type == "imagen":
        if not GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY가 설정되어 있지 않습니다.")

        client = genai.Client(api_key=GEMINI_API_KEY)

        s3_url = _generate_single_imagen_image(client, model_name, prompt, keyword, 1)
        if s3_url:
            return {"url": s3_url, "cost": 0.04}
        return None

    elif service_type == "gemini-flash":
        if not GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY가 설정되어 있지 않습니다.")

        client = genai.Client(api_key=GEMINI_API_KEY)

        s3_url = _generate_single_gemini_flash_image(client, model_name, prompt, keyword, 1)
        if s3_url:
            return {"url": s3_url, "cost": 0.039}
        return None

    elif service_type == "recraft":
        if not RECRAFT_API_KEY:
            raise ValueError("RECRAFT_API_KEY가 설정되어 있지 않습니다.")

        s3_url = _generate_single_recraft_image(RECRAFT_API_KEY, model_name, prompt, keyword, 1)
        if s3_url:
            return {"url": s3_url, "cost": 0.008}
        return None

    else:
        raise ValueError(f"지원하지 않는 이미지 서비스: {service_type}")


__all__ = [
    "call_image_ai",
    "get_image_service_type",
]
