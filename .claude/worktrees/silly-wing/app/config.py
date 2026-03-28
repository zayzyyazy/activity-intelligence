import os
from dotenv import load_dotenv

# Load variables from .env into the environment
load_dotenv()

# OpenAI API key — set in .env or as a real environment variable
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


def check_config() -> None:
    """Print whether each required config value is loaded."""
    print(f"OPENAI_API_KEY loaded: {bool(OPENAI_API_KEY)}")


if __name__ == "__main__":
    check_config()
