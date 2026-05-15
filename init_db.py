import asyncio

import asyncpg

from app.core.config import settings


async def create_database():
    print("🚀 Initializing Enterprise Database Setup...")

    # Extract info from settings
    url = settings.DATABASE_URL
    if "sqlite" in url:
        print("✅ Using SQLite. No manual database creation needed.")
        return

    try:
        # Clean the URL for asyncpg
        conn_str = url.replace("postgresql+asyncpg://", "postgresql://")
        base_url, db_name = conn_str.rsplit('/', 1)
        postgres_url = f"{base_url}/postgres"

        # Connect to master postgres DB
        conn = await asyncpg.connect(postgres_url)

        # Check if target db exists
        exists = await conn.fetchval(f"SELECT 1 FROM pg_database WHERE datname = '{db_name}'")

        if not exists:
            # We must close connection to create DB
            await conn.close()
            # Reconnect without transaction to run CREATE DATABASE
            conn = await asyncpg.connect(postgres_url)
            await conn.execute(f"CREATE DATABASE {db_name}")
            print(f"✅ Database '{db_name}' created successfully!")
        else:
            print(f"ℹ️ Database '{db_name}' already exists.")

        await conn.close()

    except Exception as e:
        print(f"❌ Connection Error: {e}")
        print("\n💡 Tip: Check your password in .env.")
        print("If you don't have Postgres, the app will use SQLite.")

if __name__ == "__main__":
    asyncio.run(create_database())
