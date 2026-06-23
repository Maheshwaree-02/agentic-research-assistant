# test_db.py
from database.connection import init_db, get_db
from sqlalchemy import text

print("🔍 Testing PostgreSQL Connection...\n")

try:
    # Initialize tables
    init_db()
    print("✅ Database tables initialized/verified")
    
    # Test connection
    db = next(get_db())
    result = db.execute(text("SELECT version();"))
    version = result.scalar()
    
    print("✅ Successfully connected to PostgreSQL!")
    print(f"📊 PostgreSQL Version: {version}")
    
    # Count existing researches
    from database.schema import Research
    count = db.query(Research).count()
    print(f"📚 Total researches saved: {count}")
    
    db.close()
    
except Exception as e:
    print("❌ Connection Failed!")
    print(f"Error: {e}")
    print("\n💡 Check your DATABASE_URL in .env file")