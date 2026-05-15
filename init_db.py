import asyncio
import asyncpg
from app.core.config import settings

async def create_database():
    """
    Attempts to connect to the default 'postgres' database and 
    create the 'core_auth' database if it doesn't exist.
    """
    print("🚀 Initializing Database Setup...")
    
    # Parse connection string to get credentials
    # Expected: postgresql+asyncpg://user:pass@host:port/db
    conn_str = settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
    
    # We need to connect to the default 'postgres' db first to create the new one
    base_url, db_name = conn_str.rsplit('/', 1)
    postgres_url = f"{base_url}/postgres"

    try:
        # Connect to default postgres DB
        conn = await asyncpg.connect(postgres_url)
        
        # Check if core_auth exists
        exists = await conn.fetchval(f"SELECT 1 FROM pg_database WHERE datname = '{db_name}'")
        
        if not exists:
            # We must close connection and use another one to create DB (cannot create DB inside transaction)
            await conn.execute(f"CREATE DATABASE {db_name}")
            print(f"✅ Database '{db_name}' created successfully!")
        else:
            print(f"ℹ️ Database '{db_name}' already exists.")
            
        await conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\n💡 Troubleshooting Tips:")
        print("1. Ensure PostgreSQL is installed and running.")
        print("2. Check if your username/password in .env are correct.")
        print("3. Ensure your user has 'Createdb' privileges.")

if __name__ == "__main__":
    asyncio.run(create_database())
