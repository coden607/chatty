#!/usr/bin/env python3
"""
SECURE API KEY BACKUP SYSTEM
Safely backs up and restores API keys with encryption
"""

import os
import json
import base64
from pathlib import Path
from datetime import datetime
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
from dotenv import load_dotenv

class SecureKeyBackup:
    """Secure backup system for API keys"""
    
    def __init__(self):
        self.secrets_file = Path.home() / ".config/chatty/secrets.env"
        self.backup_dir = Path.home() / ".config/chatty/backups"
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Key file for encryption
        self.key_file = Path.home() / ".config/chatty/.backup_key"
        
    def get_encryption_key(self):
        """Get or create encryption key"""
        if self.key_file.exists():
            with open(self.key_file, 'rb') as f:
                return f.read()
        else:
            # Generate new key
            key = Fernet.generate_key()
            self.key_file.write_bytes(key)
            # Make it read-only for owner
            os.chmod(self.key_file, 0o600)
            return key
    
    def backup_keys(self):
        """Create encrypted backup of API keys"""
        print("\n🔐 Creating secure backup of API keys...")
        
        if not self.secrets_file.exists():
            print("❌ No secrets file found to backup")
            return None
        
        # Read secrets
        with open(self.secrets_file, 'r') as f:
            secrets_content = f.read()
        
        # Get encryption key
        key = self.get_encryption_key()
        fernet = Fernet(key)
        
        # Encrypt
        encrypted = fernet.encrypt(secrets_content.encode())
        
        # Create backup file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = self.backup_dir / f"secrets_backup_{timestamp}.enc"
        
        backup_file.write_bytes(encrypted)
        os.chmod(backup_file, 0o600)  # Read-only for owner
        
        print(f"✅ Backup created: {backup_file}")
        print(f"   Encrypted with key: {self.key_file}")
        
        # Also create a metadata file
        metadata = {
            "timestamp": timestamp,
            "backup_file": str(backup_file),
            "original_file": str(self.secrets_file),
            "encrypted": True
        }
        
        metadata_file = self.backup_dir / f"backup_metadata_{timestamp}.json"
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        return backup_file
    
    def list_backups(self):
        """List all available backups"""
        print("\n📋 Available backups:")
        print("=" * 80)
        
        backups = sorted(self.backup_dir.glob("secrets_backup_*.enc"), reverse=True)
        
        if not backups:
            print("No backups found")
            return []
        
        for i, backup in enumerate(backups, 1):
            size_kb = backup.stat().st_size / 1024
            timestamp = backup.stem.replace("secrets_backup_", "")
            
            # Format timestamp
            dt = datetime.strptime(timestamp, "%Y%m%d_%H%M%S")
            formatted_date = dt.strftime("%Y-%m-%d %H:%M:%S")
            
            print(f"{i}. {formatted_date} - {size_kb:.1f} KB")
            print(f"   {backup}")
        
        print("=" * 80)
        return backups
    
    def restore_backup(self, backup_file=None):
        """Restore API keys from backup"""
        if backup_file is None:
            backups = self.list_backups()
            if not backups:
                return False
            
            choice = input("\nEnter backup number to restore (or 'q' to cancel): ").strip()
            if choice.lower() == 'q':
                return False
            
            try:
                backup_file = backups[int(choice) - 1]
            except (ValueError, IndexError):
                print("❌ Invalid choice")
                return False
        
        print(f"\n🔓 Restoring from: {backup_file}")
        
        # Get encryption key
        if not self.key_file.exists():
            print("❌ Encryption key not found!")
            return False
        
        key = self.get_encryption_key()
        fernet = Fernet(key)
        
        # Read and decrypt
        encrypted = Path(backup_file).read_bytes()
        
        try:
            decrypted = fernet.decrypt(encrypted)
            secrets_content = decrypted.decode()
        except Exception as e:
            print(f"❌ Failed to decrypt backup: {e}")
            return False
        
        # Backup current file first
        if self.secrets_file.exists():
            current_backup = self.secrets_file.parent / f"secrets.env.before_restore"
            self.secrets_file.rename(current_backup)
            print(f"   ℹ️  Current file backed up to: {current_backup}")
        
        # Write restored content
        self.secrets_file.write_text(secrets_content)
        os.chmod(self.secrets_file, 0o600)
        
        print(f"✅ Restored API keys to: {self.secrets_file}")
        return True
    
    def auto_backup_on_change(self):
        """Automatically backup when secrets file changes"""
        if not self.secrets_file.exists():
            return
        
        # Check if we need a backup (no backup in last hour)
        backups = sorted(self.backup_dir.glob("secrets_backup_*.enc"), reverse=True)
        
        if backups:
            latest = backups[0]
            age_hours = (datetime.now().timestamp() - latest.stat().st_mtime) / 3600
            
            if age_hours < 1:
                # Recent backup exists
                return
        
        # Create backup
        self.backup_keys()


def main():
    """Main execution"""
    import sys
    
    backup = SecureKeyBackup()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "backup":
            backup.backup_keys()
        elif command == "restore":
            backup.restore_backup()
        elif command == "list":
            backup.list_backups()
        elif command == "auto":
            backup.auto_backup_on_change()
        else:
            print(f"Unknown command: {command}")
            print("Usage: python3 secure_key_backup.py [backup|restore|list|auto]")
    else:
        # Interactive mode
        print("\n🔐 SECURE API KEY BACKUP SYSTEM")
        print("=" * 80)
        print("\nOptions:")
        print("1. Create backup")
        print("2. Restore from backup")
        print("3. List backups")
        print("4. Exit")
        
        choice = input("\nEnter choice (1-4): ").strip()
        
        if choice == "1":
            backup.backup_keys()
        elif choice == "2":
            backup.restore_backup()
        elif choice == "3":
            backup.list_backups()
        else:
            print("Exiting...")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Cancelled")
    except Exception as e:
        print(f"\n❌ Error: {e}")
