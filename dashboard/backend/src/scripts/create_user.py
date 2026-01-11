#!/usr/bin/env python3
"""
User creation script.

Creates a dashboard user with specified credentials and role.
"""
import sys
import os
import argparse
from pathlib import Path
import re

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy.orm import Session
import uuid

from src.database import SessionLocal
from src.models.user import User
from src.services.auth_service import get_password_hash


def validate_email(email: str) -> bool:
    """Validate email format."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def validate_password(password: str) -> bool:
    """Validate password meets minimum requirements."""
    if len(password) < 8:
        print("❌ Password must be at least 8 characters long")
        return False
    return True


def create_user(
    email: str,
    password: str,
    role: str,
    unit_id: str = None
) -> bool:
    """
    Create a new dashboard user.
    
    Args:
        email: User email address
        password: Plain text password (will be hashed)
        role: User role (org_admin, analyst, unit_manager, technician)
        unit_id: Unit UUID (required for unit_manager role)
        
    Returns:
        True if user created successfully, False otherwise
    """
    # Validate inputs
    if not validate_email(email):
        print(f"❌ Invalid email format: {email}")
        return False
    
    if not validate_password(password):
        return False
    
    valid_roles = ['org_admin', 'analyst', 'unit_manager', 'technician']
    if role not in valid_roles:
        print(f"❌ Invalid role: {role}")
        print(f"   Valid roles: {', '.join(valid_roles)}")
        return False
    
    # Validate unit_id for unit_manager
    if role == 'unit_manager':
        if not unit_id:
            print("❌ unit_id is required for unit_manager role")
            return False
        try:
            unit_uuid = uuid.UUID(unit_id)
        except ValueError:
            print(f"❌ Invalid UUID format for unit_id: {unit_id}")
            return False
    elif unit_id:
        print(f"⚠️  Warning: unit_id provided for non-unit_manager role, will be ignored")
        unit_id = None
    
    # Create user
    db: Session = SessionLocal()
    try:
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == email).first()
        if existing_user:
            print(f"❌ User with email {email} already exists")
            return False
        
        # Hash password
        password_hash = get_password_hash(password)
        
        # Create user record
        user = User(
            email=email,
            password_hash=password_hash,
            role=role,
            unit_id=uuid.UUID(unit_id) if unit_id else None
        )
        
        db.add(user)
        db.commit()
        db.refresh(user)
        
        print("\n✅ User created successfully!")
        print(f"   ID: {user.id}")
        print(f"   Email: {user.email}")
        print(f"   Role: {user.role}")
        if user.unit_id:
            print(f"   Unit ID: {user.unit_id}")
        print(f"   Created: {user.created_at}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating user: {e}")
        db.rollback()
        return False
    finally:
        db.close()


def main():
    """Main entry point with CLI argument parsing."""
    parser = argparse.ArgumentParser(
        description="Create a dashboard user",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Create an org admin
  python src/scripts/create_user.py --email admin@hospital.com --password MyPass123 --role org_admin
  
  # Create a unit manager
  python src/scripts/create_user.py --email manager@hospital.com --password MyPass123 --role unit_manager --unit-id <uuid>
  
  # Create an analyst
  python src/scripts/create_user.py --email analyst@hospital.com --password MyPass123 --role analyst
        """
    )
    
    parser.add_argument(
        '--email',
        required=True,
        help='User email address'
    )
    parser.add_argument(
        '--password',
        required=True,
        help='User password (min 8 characters)'
    )
    parser.add_argument(
        '--role',
        required=True,
        choices=['org_admin', 'analyst', 'unit_manager', 'technician'],
        help='User role'
    )
    parser.add_argument(
        '--unit-id',
        help='Unit UUID (required for unit_manager role)'
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("Hospital Dashboard - User Creation")
    print("=" * 60)
    
    success = create_user(
        email=args.email,
        password=args.password,
        role=args.role,
        unit_id=args.unit_id
    )
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
