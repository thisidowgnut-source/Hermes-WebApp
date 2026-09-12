#!/usr/bin/env python3
"""
Hermes WebApp - Encrypted Configuration Manager
================================================
Uses 'age' (modern encryption) to encrypt/decrypt .env file.
Install age: https://github.com/FiloSottile/age

Usage:
    python scripts/encrypt_config.py encrypt   # Encrypt .env -> .env.age
    python scripts/encrypt_config.py decrypt   # Decrypt .env.age -> .env
    python scripts/encrypt_config.py generate  # Generate new age key pair
"""

import os
import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
ENV_FILE = BASE_DIR / ".env"
ENV_ENCRYPTED = BASE_DIR / ".env.age"
AGE_KEY_FILE = BASE_DIR / ".age_key"
AGE_PUBKEY_FILE = BASE_DIR / ".age_pubkey"


def check_age_installed():
    """Check if age is installed."""
    try:
        subprocess.run(["age", "--version"], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def install_age():
    """Provide installation instructions for age."""
    print("❌ 'age' encryption tool not found!")
    print("\nInstall options:")
    print("  Windows: scoop install age")
    print("  Windows: choco install age")
    print("  Linux:   apt install age / brew install age")
    print("  Manual:  https://github.com/FiloSottile/age/releases")
    return False


def generate_keys():
    """Generate new age key pair."""
    print("🔐 Generating new age key pair...")
    
    # Generate private key
    result = subprocess.run(["age-keygen"], capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error generating key: {result.stderr}")
        return False
    
    lines = result.stdout.strip().split('\n')
    private_key = lines[0] if lines else ""
    public_key = lines[1] if len(lines) > 1 else ""
    
    # Save keys
    AGE_KEY_FILE.write_text(private_key + "\n")
    AGE_PUBKEY_FILE.write_text(public_key + "\n")
    
    # Set restrictive permissions
    os.chmod(AGE_KEY_FILE, 0o600)
    
    print(f"✅ Private key saved to: {AGE_KEY_FILE}")
    print(f"✅ Public key saved to:  {AGE_PUBKEY_FILE}")
    print(f"\n🔑 PUBLIC KEY (share this for encryption):")
    print(f"   {public_key}")
    print(f"\n⚠️  KEEP PRIVATE KEY SECRET! Add .age_key to .gitignore")
    return True


def encrypt_env():
    """Encrypt .env file using age."""
    if not ENV_FILE.exists():
        print(f"❌ .env file not found at {ENV_FILE}")
        return False
    
    if not AGE_PUBKEY_FILE.exists():
        print(f"❌ Public key not found. Run 'generate' first.")
        return False
    
    public_key = AGE_PUBKEY_FILE.read_text().strip()
    
    print(f"🔒 Encrypting {ENV_FILE} -> {ENV_ENCRYPTED}...")
    
    try:
        # Encrypt using age
        result = subprocess.run(
            ["age", "-r", public_key, "-o", str(ENV_ENCRYPTED), str(ENV_FILE)],
            capture_output=True, text=True
        )
        
        if result.returncode != 0:
            print(f"❌ Encryption failed: {result.stderr}")
            return False
        
        print(f"✅ Encrypted config saved to {ENV_ENCRYPTED}")
        print(f"   Safe to commit to git!")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def decrypt_env():
    """Decrypt .env.age file to .env."""
    if not ENV_ENCRYPTED.exists():
        print(f"❌ Encrypted file not found at {ENV_ENCRYPTED}")
        return False
    
    if not AGE_KEY_FILE.exists():
        print(f"❌ Private key not found at {AGE_KEY_FILE}")
        return False
    
    print(f"🔓 Decrypting {ENV_ENCRYPTED} -> {ENV_FILE}...")
    
    try:
        result = subprocess.run(
            ["age", "-d", "-i", str(AGE_KEY_FILE), "-o", str(ENV_FILE), str(ENV_ENCRYPTED)],
            capture_output=True, text=True
        )
        
        if result.returncode != 0:
            print(f"❌ Decryption failed: {result.stderr}")
            return False
        
        # Set restrictive permissions on decrypted file
        os.chmod(ENV_FILE, 0o600)
        
        print(f"✅ Decrypted config saved to {ENV_FILE}")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def main():
    if not check_age_installed():
        install_age()
        sys.exit(1)
    
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == "generate":
        generate_keys()
    elif command == "encrypt":
        encrypt_env()
    elif command == "decrypt":
        decrypt_env()
    else:
        print(f"Unknown command: {command}")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()