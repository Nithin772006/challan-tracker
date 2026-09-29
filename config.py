import os
import socket
from dotenv import load_dotenv

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
# Load environment variables from .env
load_dotenv(os.path.join(BASE_DIR, '.env'))

def is_port_open(host, port, timeout=0.8):
    """Check if server port is actively listening."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, int(port)))
        sock.close()
        return result == 0
    except Exception:
        return False

def clean_database_url(url):
    """Format and optimize PostgreSQL / Supabase connection URLs."""
    if not url:
        return None
    url = url.strip().strip("'").strip('"')

    # Convert generic prefix to psycopg2 driver
    if url.startswith('postgres://'):
        url = url.replace('postgres://', 'postgresql+psycopg2://', 1)
    elif url.startswith('postgresql://') and not url.startswith('postgresql+psycopg2://'):
        url = url.replace('postgresql://', 'postgresql+psycopg2://', 1)

    # Supabase cloud requires SSL mode
    if ('supabase.co' in url or 'supabase.com' in url) and 'sslmode' not in url:
        separator = '&' if '?' in url else '?'
        url = f"{url}{separator}sslmode=require"

    return url

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'traffic-violation-logger-secret-key-2026')

    # Priority 1: Supabase / PostgreSQL full connection URL
    supabase_or_db_url = os.environ.get('SUPABASE_DB_URL') or os.environ.get('DATABASE_URL')
    
    # Priority 2: Individual PostgreSQL / Supabase credentials
    PG_USER = os.environ.get('POSTGRES_USER', os.environ.get('PGUSER', 'postgres'))
    PG_PASSWORD = os.environ.get('POSTGRES_PASSWORD', os.environ.get('PGPASSWORD', 'postgres'))
    PG_HOST = os.environ.get('POSTGRES_HOST', os.environ.get('PGHOST', 'localhost'))
    PG_PORT = os.environ.get('POSTGRES_PORT', os.environ.get('PGPORT', '5432'))
    PG_DB = os.environ.get('POSTGRES_DB', os.environ.get('PGDATABASE', 'postgres'))

    LOCAL_POSTGRES_URI = f"postgresql+psycopg2://{PG_USER}:{PG_PASSWORD}@{PG_HOST}:{PG_PORT}/{PG_DB}"
    SQLITE_URI = f"sqlite:///{os.path.join(BASE_DIR, 'database.db')}"

    # Determine active connection
    if supabase_or_db_url and supabase_or_db_url.strip():
        SQLALCHEMY_DATABASE_URI = clean_database_url(supabase_or_db_url)
        if 'supabase' in SQLALCHEMY_DATABASE_URI.lower():
            DB_ENGINE = 'Supabase (PostgreSQL Cloud Managed)'
        else:
            DB_ENGINE = 'PostgreSQL (Cloud / Remote DATABASE_URL)'
    elif is_port_open(PG_HOST, PG_PORT):
        SQLALCHEMY_DATABASE_URI = LOCAL_POSTGRES_URI
        DB_ENGINE = f'PostgreSQL ({PG_HOST}:{PG_PORT}/{PG_DB})'
    else:
        # Fallback to local SQLite when offline/unconfigured so app runs immediately
        SQLALCHEMY_DATABASE_URI = SQLITE_URI
        DB_ENGINE = 'SQLite (Local fallback - configure Supabase in .env to switch)'

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Engine options for Supabase cloud stability & connection pooling
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
    }

    QR_FOLDER = os.path.join(BASE_DIR, 'static', 'qr')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
