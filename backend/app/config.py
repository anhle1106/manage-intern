from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    mongodb_uri: str = "mongodb://localhost:27017/intern_management"
    jwt_secret: str = "change-this-secret"
    jwt_algorithm: str = "HS256"
    jwt_expire_hours: int = 24

    cloudinary_cloud_name: str = ""
    cloudinary_api_key: str = ""
    cloudinary_api_secret: str = ""

    gemini_api_key: str = ""

    max_upload_size_mb: int = 10

    class Config:
        env_file = [".env", "../.env"]
        case_sensitive = False
        extra = "ignore"


def get_settings() -> Settings:
    return Settings()
