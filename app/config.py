"""Application configuration loaded from environment variables."""

import os

from dotenv import load_dotenv

load_dotenv()


def _build_mysql_uri() -> str:
    """Build the SQLAlchemy URI from the discrete MYSQL_* variables."""
    user = os.getenv("MYSQL_USER", "ecommerce")
    password = os.getenv("MYSQL_PASSWORD", "ecommerce")
    host = os.getenv("MYSQL_HOST", "db")
    port = os.getenv("MYSQL_PORT", "3306")
    database = os.getenv("MYSQL_DATABASE", "ecommerce")
    return f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}?charset=utf8mb4"


class BaseConfig:
    """Settings shared by every environment."""

    SECRET_KEY = os.getenv("SECRET_KEY", "change-me-in-production")
    JSON_SORT_KEYS = False
    PROPAGATE_EXCEPTIONS = True

    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL") or _build_mysql_uri()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True, "pool_recycle": 280}

    # Pagination
    DEFAULT_PAGE_SIZE = int(os.getenv("DEFAULT_PAGE_SIZE", 20))
    MAX_PAGE_SIZE = int(os.getenv("MAX_PAGE_SIZE", 100))

    # flask-smorest / OpenAPI
    API_TITLE = "E-commerce API"
    API_VERSION = "1.0.0"
    OPENAPI_VERSION = "3.0.3"
    OPENAPI_URL_PREFIX = "/"
    OPENAPI_SWAGGER_UI_PATH = "/docs"
    OPENAPI_SWAGGER_UI_URL = "https://cdn.jsdelivr.net/npm/swagger-ui-dist/"
    OPENAPI_JSON_PATH = "openapi.json"
    API_SPEC_OPTIONS = {
        "info": {
            "description": (
                "RESTful API for a small e-commerce domain: categories, products "
                "and orders. Built with Flask, Flask-SQLAlchemy, Flask-Migrate, "
                "Marshmallow and MySQL."
            ),
        },
        "tags": [
            {"name": "Categories", "description": "Product categories (1:N with products)"},
            {"name": "Products", "description": "Catalog products"},
            {"name": "Orders", "description": "Customer orders (N:N with products)"},
        ],
    }


class DevelopmentConfig(BaseConfig):
    DEBUG = True


class TestingConfig(BaseConfig):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.getenv("TEST_DATABASE_URL", "sqlite:///:memory:")


class ProductionConfig(BaseConfig):
    DEBUG = False


CONFIG_MAP = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}


def get_config(name: str | None = None):
    """Return the config class for the given environment name."""
    env = (name or os.getenv("FLASK_ENV") or "development").lower()
    return CONFIG_MAP.get(env, DevelopmentConfig)
