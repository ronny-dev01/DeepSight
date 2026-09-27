from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    project_name: str = "SIH2026_MarineMVP"
    environment: str = "development"

    database_url: str
    redis_url: str

    max_upload_bytes: int = 524288000
    max_files_per_job: int = 200
    max_image_width: int = 12000
    max_image_height: int = 12000
    max_concurrent_jobs: int = 1

    model_name: str = "gv-yolo12"
    model_version: str = "initial"
    model_path: str = "ml/models/gv-yolo12/weights.onnx"
    model_device: str = "cpu"
    model_confidence: float = 0.25
    model_iou: float = 0.45
    model_image_size: int = 640
    model_tiling_enabled: bool = False
    model_tile_size: int = 384
    model_tile_stride: int = 256
    model_tile_iou: float = 0.70
    model_tile_nms_iou: float = 0.50
    model_registry_path: str = "ml/models/model_registry.json"
    model_verify_hash: bool = True

    api_host: str = "127.0.0.1"
    api_port: int = 8000

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()
