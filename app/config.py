
# App config. env_variables setup
import os


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-key") 
    DATABASE_PATH = os.getenv("DATABASE_PATH", "data/agenda.db")
    API_URL = os.getenv("API_URL", "http://localhost:5001/agendamentos") # Mock Port
    API_TIMEOUT = float(os.getenv("API_TIMEOUT", "5"))
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
