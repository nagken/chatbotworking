#!/usr/bin/env python3
"""
Bulk User Creation Script for CA Rebates Tool
Creates multiple users from CSV file with proper validation and error handling
"""
import asyncio
import sys
import os
import csv
import argparse
from typing import List, Dict, Tuple
from pathlib import Path

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from app.database.connection import init_database, get_db_session
from app.auth.user_repository import UserRepository
from app.models.schemas import UserCreate
from app.auth.password_utils import validate_password_strength
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BulkUserCreator:
    """Handles bulk creation of users from CSV files"""
    
    def __init__(self):
        self.required_fields = ['email', 'username', 'password']
        self.optional_fields = ['is_active']
        self.stats = {
            'total': 0,
            'created': 0,
            'skipped': 0,
            'errors': 0
        }
    
    def validate_csv_headers(self, headers: List[str]) -> Tuple[bool, List[str]]:
        """Validate CSV headers contain required fields"""
        missing_fields = []
        for field in self.required_fields:
            if field not in headers:
                missing_fields.append(field)
        
        return len(missing_fields) == 0, missing_fields
    
    def validate_user_data(self, row: Dict[str, str], row_number: int) -> Tuple[bool, List[str]]:
        """Validate individual user data"""
        errors = []
        
        # Check required fields are not empty
        for field in self.required_fields:
            if not row.get(field, '').strip():
                errors.append(f"Field '{field}' is required but empty")
        
        # Validate email format (basic)
        email = row.get('email', '').strip()
        if email and '@' not in email:
            errors.append(f"Invalid email format: {email}")
        
        # Validate password strength
        password = row.get('password', '').strip()
        if password:
            is_strong, password_errors = validate_password_strength(password)
            if not is_strong:
                errors.extend([f"Password: {error}" for error in password_errors])
        
        # Validate username length
        username = row.get('username', '').strip()
        if username and len(username) < 2:
            errors.append("Username must be at least 2 characters long")
        elif username and len(username) > 100:
            errors.append("Username must be no more than 100 characters long")
        
        # Validate is_active field
        is_active = row.get('is_active', '').strip().lower()
        if is_active and is_active not in ['true', 'false', '1', '0', 'yes', 'no']:
            errors.append(f"Invalid is_active value: {is_active}. Use: true/false, 1/0, yes/no")
        
        return len(errors) == 0, errors
    
    def parse_boolean(self, value: str) -> bool:
        """Parse boolean value from string"""
        value = value.strip().lower()
        return value in ['true', '1', 'yes']
    
    def read_csv(self, file_path: str) -> Tuple[bool, List[Dict[str, str]], List[str]]:
        """Read and validate CSV file"""
        try:
            users_data = []
            errors = []
            
            with open(file_path, 'r', encoding='utf-8') as file:
                # Detect delimiter
                sample = file.read(1024)
                file.seek(0)
                sniffer = csv.Sniffer()
                delimiter = sniffer.sniff(sample).delimiter
                
                reader = csv.DictReader(file, delimiter=delimiter)
                headers = reader.fieldnames
                
                if not headers:
                    return False, [], ["CSV file appears to be empty or invalid"]
                
                # Validate headers
                headers_valid, missing_fields = self.validate_csv_headers(headers)
                if not headers_valid:
                    return False, [], [f"Missing required CSV columns: {', '.join(missing_fields)}"]
                
                # Read and validate data
                for row_number, row in enumerate(reader, start=2):  # Start at 2 (header is row 1)
                    # Clean whitespace from all values
                    cleaned_row = {k: v.strip() if v else '' for k, v in row.items()}
                    
                    # Skip empty rows
                    if not any(cleaned_row.values()):
                        continue
                    
                    # Validate row data
                    is_valid, row_errors = self.validate_user_data(cleaned_row, row_number)
                    if not is_valid:
                        errors.extend([f"Row {row_number}: {error}" for error in row_errors])
                        continue
                    
                    users_data.append(cleaned_row)
                
                self.stats['total'] = len(users_data)
                return True, users_data, errors
                
        except FileNotFoundError:
            return False, [], [f"CSV file not found: {file_path}"]
        except csv.Error as e:
            return False, [], [f"CSV parsing error: {e}"]
        except Exception as e:
            return False, [], [f"Error reading CSV file: {e}"]
    
    async def create_users(self, users_data: List[Dict[str, str]]) -> bool:
        """Create users in database"""
        try:
            # Initialize database
            await init_database()
            print("✅ Database connection initialized")
            
            async with get_db_session() as db:
                user_repo = UserRepository(db)
                
                for i, user_data in enumerate(users_data, 1):
                    try:
                        email = user_data['email']
                        username = user_data['username']
                        password = user_data['password']
                        is_active = self.parse_boolean(user_data.get('is_active', 'true'))
                        
                        print(f"\n👤 Processing user {i}/{len(users_data)}: {email}")
                        
                        # Check if user already exists
                        existing_user = await user_repo.get_user_by_email(email)
                        if existing_user:
                            print(f"   ⏭️  User already exists, skipping...")
                            self.stats['skipped'] += 1
                            continue
                        
                        # Create user data object
                        user_create = UserCreate(
                            email=email,
                            username=username,
                            password=password  # Will be hashed by UserRepository
                        )
                        
                        # Create user in database
                        new_user = await user_repo.create_user(user_create)
                        
                        # Update is_active if specified as false
                        if not is_active:
                            from app.models.schemas import UserUpdate
                            await user_repo.update_user(new_user.id, UserUpdate(is_active=False))
                            print(f"   ℹ️  User set as inactive")
                        
                        print(f"   ✅ User created successfully")
                        print(f"      - ID: {new_user.id}")
                        print(f"      - Email: {new_user.email}")
                        print(f"      - Username: {new_user.username}")
                        print(f"      - Active: {is_active}")
                        
                        self.stats['created'] += 1
                        
                    except Exception as e:
                        print(f"   ❌ Failed to create user {email}: {e}")
                        self.stats['errors'] += 1
                        continue
                
                # Commit all changes
                await db.commit()
                print(f"\n💾 All changes committed to database")
            
            return self.stats['errors'] == 0
            
        except Exception as e:
            print(f"❌ Database operation failed: {e}")
            logger.error(f"Bulk creation error: {e}")
            return False
    
    def print_summary(self):
        """Print creation summary"""
        print("\n" + "="*50)
        print("🎯 BULK USER CREATION SUMMARY")
        print("="*50)
        print(f"📊 Total users processed: {self.stats['total']}")
        print(f"✅ Successfully created: {self.stats['created']}")
        print(f"⏭️  Skipped (already exist): {self.stats['skipped']}")
        print(f"❌ Failed: {self.stats['errors']}")
        
        if self.stats['created'] > 0:
            print(f"\n🎉 {self.stats['created']} users created successfully!")
        
        if self.stats['skipped'] > 0:
            print(f"ℹ️  {self.stats['skipped']} users were skipped (already exist)")
        
        if self.stats['errors'] > 0:
            print(f"⚠️  {self.stats['errors']} users failed to create")
        
        success_rate = (self.stats['created'] / self.stats['total'] * 100) if self.stats['total'] > 0 else 0
        print(f"📈 Success rate: {success_rate:.1f}%")

def create_sample_csv(file_path: str = "sample_users.csv"):
    """Create a sample CSV file template"""
    sample_data = [
        {
            'email': 'admin@company.com',
            'username': 'Admin User',
            'password': 'SecurePass123!',
            'is_active': 'true'
        },
        {
            'email': 'john.doe@company.com',
            'username': 'John Doe',
            'password': 'UserPass456!',
            'is_active': 'true'
        },
        {
            'email': 'jane.smith@company.com',
            'username': 'Jane Smith',
            'password': 'SmithPass789!',
            'is_active': 'false'
        }
    ]
    
    try:
        with open(file_path, 'w', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=['email', 'username', 'password', 'is_active'])
            writer.writeheader()
            writer.writerows(sample_data)
        
        print(f"✅ Sample CSV created: {file_path}")
        print("📝 Edit this file with your user data, then run:")
        print(f"   python scripts/bulk_create_users.py {file_path}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to create sample CSV: {e}")
        return False

async def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description="Bulk create users from CSV file",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
CSV Format:
  Required columns: email, username, password
  Optional columns: is_active (true/false, default: true)

Examples:
  python scripts/bulk_create_users.py users.csv
  python scripts/bulk_create_users.py --sample
  python scripts/bulk_create_users.py data/new_users.csv --dry-run
        """
    )
    
    parser.add_argument('csv_file', nargs='?', help='Path to CSV file containing user data')
    parser.add_argument('--sample', action='store_true', help='Create a sample CSV template')
    parser.add_argument('--dry-run', action='store_true', help='Validate CSV without creating users')
    parser.add_argument('--force', action='store_true', help='Skip confirmation prompt')
    
    args = parser.parse_args()
    
    print("🚀 CA REBATES TOOL - BULK USER CREATION")
    print("="*50)
    
    # Handle sample creation
    if args.sample:
        return create_sample_csv()
    
    # Validate arguments
    if not args.csv_file:
        print("❌ Error: CSV file path is required")
        parser.print_help()
        return False
    
    if not os.path.exists(args.csv_file):
        print(f"❌ Error: CSV file not found: {args.csv_file}")
        return False
    
    # Initialize bulk creator
    creator = BulkUserCreator()
    
    # Read and validate CSV
    print(f"📂 Reading CSV file: {args.csv_file}")
    success, users_data, errors = creator.read_csv(args.csv_file)
    
    if not success or errors:
        print("❌ CSV validation failed:")
        for error in errors:
            print(f"   - {error}")
        return False
    
    print(f"✅ CSV validated successfully")
    print(f"📊 Found {len(users_data)} valid users to create")
    
    # Show preview
    if users_data:
        print(f"\n📋 Preview of first few users:")
        for i, user in enumerate(users_data[:3], 1):
            active_status = "Active" if creator.parse_boolean(user.get('is_active', 'true')) else "Inactive"
            print(f"   {i}. {user['email']} ({user['username']}) - {active_status}")
        
        if len(users_data) > 3:
            print(f"   ... and {len(users_data) - 3} more users")
    
    # Dry run mode
    if args.dry_run:
        print(f"\n🔍 DRY RUN MODE - No users will be created")
        print(f"✅ CSV file is valid and ready for import")
        return True
    
    # Confirmation
    if not args.force:
        print(f"\n🤔 This will create {len(users_data)} new users in the database.")
        response = input("Do you want to proceed? (y/N): ")
        if response.lower() not in ['y', 'yes']:
            print("❌ Operation cancelled by user")
            return False
    
    # Create users
    print(f"\n🚀 Creating users...")
    success = await creator.create_users(users_data)
    
    # Print summary
    creator.print_summary()
    
    if success:
        print(f"\n✅ Bulk user creation completed successfully!")
        print(f"💡 Users can now log in with their credentials")
    else:
        print(f"\n⚠️  Bulk user creation completed with errors")
        print(f"💡 Check the error messages above")
    
    return success

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n❌ Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)
