from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql://feedback:feedback@localhost:5432/feedback_explorer"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"
    embedding_model: str = "all-MiniLM-L6-v2"
    cluster_similarity_threshold: float = 0.62
    min_entries_for_new_theme: int = 4

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()