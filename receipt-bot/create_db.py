import asyncio
import asyncpg

async def create_database():
    try:
        # Connect to the default 'postgres' database to issue the CREATE DATABASE command
        conn = await asyncpg.connect(
            user='postgres', 
            password='postgres', 
            database='postgres', 
            host='127.0.0.1', 
            port=5432
        )
        try:
            await conn.execute('CREATE DATABASE receipts')
            print("Successfully created the 'receipts' database!")
        except asyncpg.exceptions.DuplicateDatabaseError:
            print("Database 'receipts' already exists.")
        
        await conn.close()
    except Exception as e:
        print(f"Failed to connect to Local PostgreSQL: {e}")

if __name__ == "__main__":
    asyncio.run(create_database())
