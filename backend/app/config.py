from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql://feedback:feedback@localhost:5432/feedback_explorer"
    groq_api_key: str = ""
    groq_model: str = "openai/gpt-oss-20b"
    embedding_model: str = "paraphrase-multilingual-MiniLM-L12-v2"
    cluster_similarity_threshold: float = 0.45
    min_entries_for_new_theme: int = 4

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
