"""Ollama / LM Studio LLM API 클라이언트"""
import json
import requests
from typing import Optional, Callable


# LLM API 요청 타임아웃 (초)
REQUEST_TIMEOUT = 300


class LLMClient:
    """로컬 LLM(Ollama / LM Studio) API 클라이언트"""

    def __init__(self, endpoint: str, model: str, temperature: float = 0.8, max_tokens: int = 4096):
        self.endpoint = endpoint.rstrip("/")
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens

    # ──────────────────────────────────────────
    # Ollama 전용 API
    # ──────────────────────────────────────────

    def _ollama_generate(
        self,
        prompt: str,
        system: str = "",
        stream: bool = True,
        on_token: Optional[Callable[[str], None]] = None,
    ) -> str:
        """Ollama /api/generate 호출"""
        url = f"{self.endpoint}/api/generate"
        payload = {
            "model": self.model,
            "prompt": prompt,
            "system": system,
            "stream": stream,
            "options": {
                "temperature": self.temperature,
                "num_predict": self.max_tokens,
            },
        }
        full_text = ""
        with requests.post(url, json=payload, stream=stream, timeout=REQUEST_TIMEOUT) as resp:
            resp.raise_for_status()
            if stream:
                for line in resp.iter_lines():
                    if line:
                        data = json.loads(line)
                        token = data.get("response", "")
                        full_text += token
                        if on_token:
                            on_token(token)
                        if data.get("done"):
                            break
            else:
                data = resp.json()
                full_text = data.get("response", "")
        return full_text

    # ──────────────────────────────────────────
    # OpenAI 호환 API (LM Studio)
    # ──────────────────────────────────────────

    def _openai_chat(
        self,
        system: str,
        user_message: str,
        stream: bool = True,
        on_token: Optional[Callable[[str], None]] = None,
    ) -> str:
        """OpenAI 호환 /v1/chat/completions 호출 (LM Studio 등)"""
        url = f"{self.endpoint}/v1/chat/completions"
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user_message},
            ],
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "stream": stream,
        }
        full_text = ""
        with requests.post(url, json=payload, stream=stream, timeout=REQUEST_TIMEOUT) as resp:
            resp.raise_for_status()
            if stream:
                for line in resp.iter_lines():
                    if line:
                        raw = line.decode("utf-8") if isinstance(line, bytes) else line
                        if raw.startswith("data: "):
                            raw = raw[6:]
                        if raw.strip() == "[DONE]":
                            break
                        try:
                            data = json.loads(raw)
                            delta = data["choices"][0].get("delta", {})
                            token = delta.get("content", "")
                            full_text += token
                            if on_token and token:
                                on_token(token)
                        except (json.JSONDecodeError, KeyError):
                            continue
            else:
                data = resp.json()
                full_text = data["choices"][0]["message"]["content"]
        return full_text

    # ──────────────────────────────────────────
    # 공개 인터페이스
    # ──────────────────────────────────────────

    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        stream: bool = True,
        on_token: Optional[Callable[[str], None]] = None,
    ) -> str:
        """LLM 텍스트 생성 (Ollama 우선 시도, 실패 시 OpenAI 호환 API)"""
        try:
            return self._ollama_generate(
                prompt=user_prompt,
                system=system_prompt,
                stream=stream,
                on_token=on_token,
            )
        except requests.exceptions.ConnectionError:
            raise
        except requests.exceptions.HTTPError as e:
            # Ollama 엔드포인트가 없으면 OpenAI 호환 시도
            if e.response is not None and e.response.status_code == 404:
                return self._openai_chat(
                    system=system_prompt,
                    user_message=user_prompt,
                    stream=stream,
                    on_token=on_token,
                )
            raise

    def list_models(self) -> list:
        """사용 가능한 모델 목록 조회 (Ollama)"""
        try:
            url = f"{self.endpoint}/api/tags"
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            return [m["name"] for m in data.get("models", [])]
        except Exception:
            return []

    def is_reachable(self) -> bool:
        """LLM 서버 연결 가능 여부 확인"""
        try:
            requests.get(self.endpoint, timeout=5)
            return True
        except Exception:
            return False
