import os
import socket
from dotenv import load_dotenv

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(BASE_DIR, '.env'))

def is_port_open(host, port, timeout=0.8):
    """Check if PostgreSQL server port is actively listening."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, int(port)))
        sock.close()
        return result == 0
    except Exception:
        return False

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'traffic-violation-logger-secret-key-2026')

    # PostgreSQL connection parameters
    PG_USER = os.environ.get('POSTGRES_USER', os.environ.get('PGUSER', 'postgres'))
    PG_PASSWORD = os.environ.get('POSTGRES_PASSWORD', os.environ.get('PGPASSWORD', 'postgres'))
    PG_HOST = os.environ.get('POSTGRES_HOST', os.environ.get('PGHOST', 'localhost'))
    PG_PORT = os.environ.get('POSTGRES_PORT', os.environ.get('PGPORT', '5432'))
    PG_DB = os.environ.get('POSTGRES_DB', os.environ.get('PGDATABASE', 'traffic_logger'))

    POSTGRES_URI = f"postgresql+psycopg2://{PG_USER}:{PG_PASSWORD}@{PG_HOST}:{PG_PORT}/{PG_DB}"
    SQLITE_URI = f"sqlite:///{os.path.join(BASE_DIR, 'database.db')}"

    # Determine database connection
    custom_db_url = os.environ.get('DATABASE_URL')
    if custom_db_url:
        if custom_db_url.startswith('postgres://'):
            custom_db_url = custom_db_url.replace('postgres://', 'postgresql+psycopg2://', 1)
        elif custom_db_url.startswith('postgresql://') and not custom_db_url.startswith('postgresql+psycopg2://'):
            custom_db_url = custom_db_url.replace('postgresql://', 'postgresql+psycopg2://', 1)
        SQLALCHEMY_DATABASE_URI = custom_db_url
        DB_ENGINE = 'PostgreSQL (Explicit DATABASE_URL)'
    elif is_port_open(PG_HOST, PG_PORT):
        SQLALCHEMY_DATABASE_URI = POSTGRES_URI
        DB_ENGINE = f'PostgreSQL ({PG_HOST}:{PG_PORT}/{PG_DB})'
    else:
        # Seamless local development fallback if PostgreSQL service is not yet started
        SQLALCHEMY_DATABASE_URI = SQLITE_URI
        DB_ENGINE = 'SQLite (Local fallback - start PostgreSQL on port 5432 to auto-switch)'

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    QR_FOLDER = os.path.join(BASE_DIR, 'static', 'qr')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
