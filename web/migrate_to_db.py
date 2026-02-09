#!/usr/bin/env python3
"""
Migration script to convert file-based storage to database
Migrates users.json and .owner files to SQLite database
"""

import json
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app import app, db, User, CVVariant, CVMaster
from werkzeug.security import generate_password_hash

def migrate_users():
    """Migrate users from users.json to database"""
    users_file = Path(__file__).parent / 'users.json'
    
    if not users_file.exists():
        print("❌ users.json not found, skipping user migration")
        return {}
    
    print("\n📥 Loading users from users.json...")
    with open(users_file, 'r') as f:
        users_data = json.load(f)
    
    user_id_mapping = {}  # old_id -> new_id
    
    print(f"Found {len(users_data)} users to migrate")
    
    for old_id, user_info in users_data.items():
        email = user_info['email']
        password_hash = user_info['password_hash']
        
        # Check if user already exists
        existing = User.query.filter_by(email=email).first()
        if existing:
            print(f"⚠️  User {email} already exists (ID: {existing.id})")
            user_id_mapping[old_id] = existing.id
            continue
        
        # Create new user
        user = User(email=email)
        user.password_hash = password_hash  # Use existing hash
        db.session.add(user)
        db.session.flush()  # Get the ID
        
        user_id_mapping[old_id] = user.id
        print(f"✅ Migrated user: {email} (old ID: {old_id} -> new ID: {user.id})")
    
    db.session.commit()
    print(f"\n✅ Migrated {len(user_id_mapping)} users")
    
    return user_id_mapping

def migrate_variants(user_id_mapping):
    """Migrate CV variants from .owner files to database"""
    v1_dir = Path(__file__).parent.parent / 'v1'
    
    if not v1_dir.exists():
        print("❌ v1 directory not found, skipping variants migration")
        return
    
    print("\n📥 Scanning for CV variants...")
    migrated_count = 0
    
    for item in v1_dir.iterdir():
        if not item.is_dir() or item.name in ['.git', '__pycache__', 'canva']:
            continue
        
        # Check for .owner file
        owner_file = item / '.owner'
        if not owner_file.exists():
            print(f"⚠️  No .owner file for {item.name}, skipping")
            continue
        
        # Read owner
        with open(owner_file, 'r') as f:
            old_user_id = f.read().strip()
        
        # Map to new user ID
        new_user_id = user_id_mapping.get(old_user_id)
        if not new_user_id:
            print(f"⚠️  Owner {old_user_id} not found for {item.name}, skipping")
            continue
        
        # Check if already exists
        existing = CVVariant.query.filter_by(folder_name=item.name).first()
        if existing:
            print(f"⚠️  Variant {item.name} already exists in database")
            continue
        
        # Read job_desc.md for company/role info
        job_desc_file = item / 'job_desc.md'
        company = None
        role = None
        job_description = None
        
        if job_desc_file.exists():
            with open(job_desc_file, 'r', encoding='utf-8') as f:
                content = f.read()
                job_description = content
                # Try to extract company name from first line
                lines = content.split('\n')
                if lines:
                    company = lines[0].replace('#', '').strip()
                # Try to extract role from second line
                if len(lines) > 1 and '**Role:**' in lines[1]:
                    role = lines[1].replace('**Role:**', '').strip()
        
        # Check file existence
        has_tex = (item / 'main.tex').exists()
        has_pdf = (item / 'main.pdf').exists()
        
        # Create variant record
        variant = CVVariant(
            user_id=new_user_id,
            folder_name=item.name,
            company=company,
            role=role,
            job_description=job_description,
            has_tex=has_tex,
            has_pdf=has_pdf
        )
        db.session.add(variant)
        migrated_count += 1
        
        print(f"✅ Migrated variant: {item.name} (user: {new_user_id})")
    
    db.session.commit()
    print(f"\n✅ Migrated {migrated_count} variants")

def migrate_cv_masters(user_id_mapping):
    """Migrate user master CV files to database"""
    v1_dir = Path(__file__).parent.parent / 'v1'
    
    if not v1_dir.exists():
        print("❌ v1 directory not found, skipping CV masters migration")
        return
    
    print("\n📥 Scanning for user master CVs...")
    migrated_count = 0
    
    for old_user_id, new_user_id in user_id_mapping.items():
        master_file = v1_dir / f"user_{old_user_id}_master.tex"
        
        if not master_file.exists():
            continue
        
        # Check if already exists
        existing = CVMaster.query.filter_by(user_id=new_user_id, is_active=True).first()
        if existing:
            print(f"⚠️  Master CV for user {new_user_id} already exists")
            continue
        
        # Read LaTeX content
        with open(master_file, 'r', encoding='utf-8') as f:
            latex_content = f.read()
        
        # Create master record
        cv_master = CVMaster(
            user_id=new_user_id,
            latex_content=latex_content,
            original_filename=f"user_{old_user_id}_master.tex",
            version=1,
            is_active=True
        )
        db.session.add(cv_master)
        migrated_count += 1
        
        print(f"✅ Migrated master CV: user_{old_user_id}_master.tex -> user {new_user_id}")
    
    db.session.commit()
    print(f"\n✅ Migrated {migrated_count} master CVs")

def main():
    """Run migration"""
    print("🚀 Starting migration to database...")
    print("=" * 60)
    
    with app.app_context():
        # Create tables if not exist
        db.create_all()
        print("✅ Database tables created")
        
        # Migrate users
        user_id_mapping = migrate_users()
        
        # Migrate variants
        if user_id_mapping:
            migrate_variants(user_id_mapping)
            migrate_cv_masters(user_id_mapping)
        
        print("\n" + "=" * 60)
        print("✅ Migration completed successfully!")
        print("\nDatabase summary:")
        print(f"  Users: {User.query.count()}")
        print(f"  CV Masters: {CVMaster.query.count()}")
        print(f"  CV Variants: {CVVariant.query.count()}")

if __name__ == '__main__':
    main()
