import asyncio
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker

load_dotenv()

DATABASE_URL = os.environ.get("DATABASE_URL", "")
if DATABASE_URL:
    SYNC_DATABASE_URL = DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://").split('?')[0]
else:
    print("❌ DATABASE_URL not found")
    exit(1)

engine = create_engine(SYNC_DATABASE_URL)
Session = sessionmaker(bind=engine)

def main():
    print("=" * 70)
    print("🔍 EAGLECODE DATABASE INSPECTOR")
    print("=" * 70)
    
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    
    print(f"\n📚 TABLES ({len(tables)} tables):")
    for table in tables:
        print(f"  - {table}")
    
    with Session() as session:
        # Check users
        print("\n" + "=" * 50)
        print("👤 USERS")
        print("=" * 50)
        result = session.execute(text("SELECT id, email, username, avatar_url, created_at FROM users"))
        for row in result:
            print(f"  ID: {row[0]}")
            print(f"  Email: {row[1]}")
            print(f"  Username: {row[2]}")
            print(f"  Avatar: {row[3]}")
            print(f"  Created: {row[4]}")
            print()
        
        # Check user_credits
        print("\n" + "=" * 50)
        print("💰 USER CREDITS")
        print("=" * 50)
        result = session.execute(text("SELECT user_id, plan, daily_credits_used, monthly_credits_used, daily_reset_date, monthly_reset_date FROM user_credits"))
        for row in result:
            print(f"  User ID: {row[0]}")
            print(f"  Plan: {row[1]}")
            print(f"  Daily Used: {row[2]}")
            print(f"  Monthly Used: {row[3]}")
            print(f"  Daily Reset: {row[4]}")
            print(f"  Monthly Reset: {row[5]}")
            print()
        
        # Check projects
        print("\n" + "=" * 50)
        print("📁 PROJECTS")
        print("=" * 50)
        result = session.execute(text("SELECT id, name, user_id, project_type, file_count, timestamp FROM projects ORDER BY timestamp DESC"))
        for row in result:
            print(f"  ID: {row[0]}")
            print(f"  Name: {row[1]}")
            print(f"  User ID: {row[2]}")
            print(f"  Type: {row[3]}")
            print(f"  Files: {row[4]}")
            print(f"  Created: {row[5]}")
            print()
        
        # Count projects per user
        print("\n" + "=" * 50)
        print("📊 PROJECT COUNT BY USER")
        print("=" * 50)
        result = session.execute(text("SELECT user_id, COUNT(*) as project_count FROM projects GROUP BY user_id"))
        for row in result:
            print(f"  User {row[0]}: {row[1]} projects")

if __name__ == "__main__":
    main()