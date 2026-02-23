import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Settings:
    # ==============================
    # Database
    # ==============================
    DATABASE_URL: str = os.getenv("DATABASE_URL")

    # ==============================
    # Security
    # ==============================
    SECRET_KEY: str = os.getenv("SECRET_KEY")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(
        os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 60)
    )

    # ==============================
    # Environment
    # ==============================
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")

    # ==============================
    # Validation
    # ==============================
    def validate(self):
        if not self.DATABASE_URL:
            raise ValueError("DATABASE_URL is not set in environment variables")

        if not self.SECRET_KEY:
            raise ValueError("SECRET_KEY is not set in environment variables")


# Create settings instance
settings = Settings()

# Validate on startup
settings.validate()
