# check_db.py - Updated for your actual schema
import sqlite3
import json
from datetime import datetime

def check_database():
    """Simple database checker - matches your actual schema"""
    
    conn = sqlite3.connect('./eaglecode.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # First, get the actual schema
    cursor.execute("SELECT sql FROM sqlite_master WHERE type='table'")
    schemas = cursor.fetchall()
    
    print("\n" + "="*80)
    print("📊 EAGLECODE DATABASE - COMPLETE INSPECTION")
    print("="*80)
    
    # Database info
    import os
    db_size = os.path.getsize('./eaglecode.db') if os.path.exists('./eaglecode.db') else 0
    print(f"\n📁 Database: eaglecode.db")
    print(f"💾 Size: {db_size / 1024:.2f} KB ({db_size / 1024 / 1024:.2f} MB)")
    print(f"🕐 Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Show all tables
    print("\n" + "="*80)
    print("📋 DATABASE TABLES")
    print("="*80)
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = cursor.fetchall()
    for table in tables:
        print(f"  📌 {table['name']}")
    
    # ========== USERS ==========
    print("\n" + "="*80)
    print("👥 USERS TABLE")
    print("="*80)
    try:
        # First, check what columns exist
        cursor.execute("PRAGMA table_info(users)")
        columns = cursor.fetchall()
        column_names = [col['name'] for col in columns]
        print(f"Columns: {', '.join(column_names)}")
        
        # Build query dynamically
        select_cols = []
        for col in ['id', 'email', 'username', 'created_at']:
            if col in column_names:
                select_cols.append(col)
        
        # Add is_admin if it exists
        if 'is_admin' in column_names:
            select_cols.append('is_admin')
        
        query = f"SELECT {', '.join(select_cols)} FROM users ORDER BY created_at DESC"
        cursor.execute(query)
        users = cursor.fetchall()
        print(f"\nTotal users: {len(users)}\n")
        
        for user in users:
            print(f"  📧 Email: {user['email']}")
            print(f"     Username: {user['username']}")
            if 'is_admin' in user.keys():
                print(f"     Admin: {'✅ YES' if user['is_admin'] else '❌ NO'}")
            print(f"     User ID: {user['id']}")
            print(f"     Created: {user['created_at'][:19] if user['created_at'] else 'N/A'}")
            print()
    except Exception as e:
        print(f"  ⚠️ Could not read users table: {e}")
    
    # ========== PROJECTS ==========
    print("\n" + "="*80)
    print("📁 PROJECTS TABLE")
    print("="*80)
    try:
        cursor.execute("SELECT COUNT(*) FROM projects")
        total_projects = cursor.fetchone()[0]
        print(f"Total projects: {total_projects}\n")
        
        if total_projects > 0:
            # Get column info
            cursor.execute("PRAGMA table_info(projects)")
            columns = cursor.fetchall()
            column_names = [col['name'] for col in columns]
            
            # Build query
            select_cols = []
            for col in ['id', 'name', 'project_type', 'file_count', 'timestamp', 'user_id']:
                if col in column_names:
                    select_cols.append(col)
            
            query = f"SELECT {', '.join(select_cols)} FROM projects ORDER BY timestamp DESC LIMIT 20"
            cursor.execute(query)
            projects = cursor.fetchall()
            
            for proj in projects:
                print(f"  📄 Name: {proj['name']}")
                if 'project_type' in proj.keys():
                    print(f"     Type: {proj['project_type'] or 'general'}")
                if 'file_count' in proj.keys():
                    print(f"     Files: {proj['file_count']}")
                print(f"     Project ID: {proj['id']}")
                if 'user_id' in proj.keys():
                    print(f"     User ID: {proj['user_id']}")
                if 'timestamp' in proj.keys() and proj['timestamp']:
                    print(f"     Created: {proj['timestamp'][:19]}")
                print()
    except Exception as e:
        print(f"  ⚠️ Could not read projects table: {e}")
    
    # ========== PROJECT FILES ==========
    print("\n" + "="*80)
    print("📄 PROJECT FILES TABLE")
    print("="*80)
    try:
        cursor.execute("SELECT COUNT(*) FROM project_files")
        total_files = cursor.fetchone()[0]
        print(f"Total files: {total_files}\n")
        
        if total_files > 0:
            cursor.execute("""
                SELECT project_id, file_path, file_type, size_bytes 
                FROM project_files 
                LIMIT 10
            """)
            files = cursor.fetchall()
            for file in files:
                print(f"  📝 Path: {file['file_path']}")
                print(f"     Type: {file['file_type'] or 'unknown'}")
                print(f"     Size: {file['size_bytes']} bytes")
                print(f"     Project ID: {file['project_id']}")
                print()
            if total_files > 10:
                print(f"  ... and {total_files - 10} more files\n")
    except Exception as e:
        print(f"  ⚠️ Could not read project_files table: {e}")
    
    # ========== SESSIONS ==========
    print("\n" + "="*80)
    print("🔐 SESSIONS TABLE")
    print("="*80)
    try:
        cursor.execute("SELECT COUNT(*) FROM sessions")
        total_sessions = cursor.fetchone()[0]
        print(f"Total sessions: {total_sessions}\n")
        
        if total_sessions > 0:
            cursor.execute("""
                SELECT id, user_id, expires_at, created_at 
                FROM sessions 
                ORDER BY created_at DESC 
                LIMIT 10
            """)
            sessions = cursor.fetchall()
            for session in sessions:
                print(f"  🎫 Session ID: {session['id'][:16]}...")
                print(f"     User ID: {session['user_id'][:16]}...")
                if session['expires_at']:
                    print(f"     Expires: {session['expires_at'][:19]}")
                if session['created_at']:
                    print(f"     Created: {session['created_at'][:19]}")
                print()
    except Exception as e:
        print(f"  ⚠️ Could not read sessions table: {e}")
    
    # ========== USER CREDITS ==========
    print("\n" + "="*80)
    print("💰 USER CREDITS TABLE")
    print("="*80)
    try:
        cursor.execute("""
            SELECT c.user_id, c.plan, c.daily_credits_used, c.monthly_credits_used,
                   u.email
            FROM user_credits c 
            LEFT JOIN users u ON u.id = c.user_id
        """)
        credits = cursor.fetchall()
        print(f"Total credit records: {len(credits)}\n")
        
        for credit in credits:
            daily_limit = 5 if credit['plan'] == 'free' else (15 if credit['plan'] == 'pro' else 40)
            monthly_limit = 30 if credit['plan'] == 'free' else (120 if credit['plan'] == 'pro' else 350)
            print(f"  👤 User: {credit['email'] or credit['user_id'][:16]}")
            print(f"     Plan: {credit['plan'].upper()}")
            print(f"     Daily: {credit['daily_credits_used']} / {daily_limit}")
            print(f"     Monthly: {credit['monthly_credits_used']} / {monthly_limit}")
            print()
    except Exception as e:
        print(f"  ⚠️ Could not read user_credits table: {e}")
    
    # ========== API KEYS ==========
    print("\n" + "="*80)
    print("🔑 API KEYS TABLE")
    print("="*80)
    try:
        cursor.execute("SELECT COUNT(*) FROM api_keys")
        total_keys = cursor.fetchone()[0]
        print(f"Total API keys: {total_keys}\n")
        
        if total_keys > 0:
            cursor.execute("SELECT name, is_active, created_at, last_used_at FROM api_keys")
            api_keys = cursor.fetchall()
            for key in api_keys:
                print(f"  🔑 Name: {key['name']}")
                print(f"     Active: {'✅ YES' if key['is_active'] else '❌ NO'}")
                if key['created_at']:
                    print(f"     Created: {key['created_at'][:19]}")
                if key['last_used_at']:
                    print(f"     Last used: {key['last_used_at'][:19]}")
                print()
    except Exception as e:
        print(f"  ⚠️ Could not read api_keys table: {e}")
    
    # ========== TEMPLATES ==========
    print("\n" + "="*80)
    print("📋 TEMPLATES TABLE")
    print("="*80)
    try:
        cursor.execute("SELECT COUNT(*) FROM templates")
        total_templates = cursor.fetchone()[0]
        print(f"Total templates: {total_templates}\n")
        
        if total_templates > 0:
            cursor.execute("SELECT name, category, usage_count, created_at FROM templates ORDER BY usage_count DESC")
            templates = cursor.fetchall()
            for template in templates:
                print(f"  📋 Name: {template['name']}")
                print(f"     Category: {template['category']}")
                print(f"     Used: {template['usage_count']} times")
                if template['created_at']:
                    print(f"     Created: {template['created_at'][:19]}")
                print()
    except Exception as e:
        print(f"  ⚠️ Could not read templates table: {e}")
    
    # ========== UPGRADE REQUESTS ==========
    print("\n" + "="*80)
    print("📨 UPGRADE REQUESTS TABLE")
    print("="*80)
    try:
        cursor.execute("SELECT COUNT(*) FROM upgrade_requests")
        total_upgrades = cursor.fetchone()[0]
        print(f"Total upgrade requests: {total_upgrades}\n")
        
        if total_upgrades > 0:
            cursor.execute("""
                SELECT user_email, requested_plan, status, created_at 
                FROM upgrade_requests 
                ORDER BY created_at DESC
            """)
            upgrades = cursor.fetchall()
            for upgrade in upgrades:
                print(f"  📧 Email: {upgrade['user_email']}")
                print(f"     Requested: {upgrade['requested_plan']}")
                print(f"     Status: {upgrade['status']}")
                if upgrade['created_at']:
                    print(f"     Date: {upgrade['created_at'][:19]}")
                print()
    except Exception as e:
        print(f"  ⚠️ Could not read upgrade_requests table: {e}")
    
    # ========== FINAL SUMMARY ==========
    print("\n" + "="*80)
    print("📊 SUMMARY")
    print("="*80)
    print(f"  📋 Total Tables:        {len(tables)}")
    print(f"  👥 Users:              {len(users) if 'users' in locals() else 0}")
    print(f"  📁 Projects:           {total_projects if 'total_projects' in locals() else 0}")
    print(f"  📄 Files:              {total_files if 'total_files' in locals() else 0}")
    print(f"  🔐 Sessions:           {total_sessions if 'total_sessions' in locals() else 0}")
    print(f"  🔑 API Keys:           {total_keys if 'total_keys' in locals() else 0}")
    print(f"  📋 Templates:          {total_templates if 'total_templates' in locals() else 0}")
    print(f"  📨 Upgrade Requests:   {total_upgrades if 'total_upgrades' in locals() else 0}")
    print(f"  💾 Database Size:      {db_size / 1024:.2f} KB")
    print("="*80)
    print("✅ Inspection complete!")
    print("="*80 + "\n")
    
    conn.close()

if __name__ == "__main__":
    check_database()