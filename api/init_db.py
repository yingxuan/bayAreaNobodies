#!/usr/bin/env python3
"""
Initialize database: run migrations and seed data
"""
import os
import sys
from alembic.config import Config
from alembic import command
from app.database import engine, Base
from app.models import *  # noqa
from seed import seed_queries

def init_db():
    """Initialize database with migrations and seed data"""
    print("Running database migrations...")
    
    # Get database URL
    alembic_cfg = Config("alembic.ini")
    alembic_cfg.set_main_option("sqlalchemy.url", os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/llm4luck"))
    
    # Run migrations
    try:
        command.upgrade(alembic_cfg, "head")
        print("✓ Migrations completed")
    except Exception as e:
        print(f"✗ Migration error: {e}")
        sys.exit(1)
    
    # Seed data
    print("Seeding default data...")
    try:
        seed_queries()
        print("✓ Seeding completed")
    except Exception as e:
        print(f"✗ Seeding error: {e}")
        sys.exit(1)
    
    print("Database initialization complete!")

if __name__ == "__main__":
    init_db()

