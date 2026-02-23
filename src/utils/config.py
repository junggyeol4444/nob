"""설정 관리 모듈"""
import json
import os
from typing import Any


# 기본 설정값
DEFAULT_CONFIG = {
    "llm_endpoint": "http://localhost:11434",
    "llm_model": "mistral",
    "temperature": 0.8,
    "max_tokens": 4096,
    "auto_save_interval": 30,
    "default_word_count": 2000,
    "db_path": "",  # 비어있으면 기본 경로 사용
}


def get_config_path() -> str:
    """설정 파일 경로 반환"""
    config_dir = os.path.join(os.path.expanduser("~"), ".novelwriter_local")
    os.makedirs(config_dir, exist_ok=True)
    return os.path.join(config_dir, "config.json")


def get_default_db_path() -> str:
    """기본 데이터베이스 파일 경로 반환"""
    data_dir = os.path.join(os.path.expanduser("~"), ".novelwriter_local")
    os.makedirs(data_dir, exist_ok=True)
    return os.path.join(data_dir, "novelwriter.db")


def load_config() -> dict:
    """설정 파일 로드 (없으면 기본값 반환)"""
    config_path = get_config_path()
    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            # 누락된 기본값 보충
            for key, val in DEFAULT_CONFIG.items():
                data.setdefault(key, val)
            return data
        except (json.JSONDecodeError, OSError):
            pass
    config = dict(DEFAULT_CONFIG)
    config["db_path"] = get_default_db_path()
    return config


def save_config(config: dict):
    """설정 파일 저장"""
    config_path = get_config_path()
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)


def get(key: str, default: Any = None) -> Any:
    """단일 설정값 조회"""
    config = load_config()
    return config.get(key, default)


def set_value(key: str, value: Any):
    """단일 설정값 저장"""
    config = load_config()
    config[key] = value
    save_config(config)
