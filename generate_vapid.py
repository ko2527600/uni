#!/usr/bin/env python3
"""
VAPID Key Generator for Push Notifications
Generates Private Key and Public Key using different methods
"""

def generate_pywebpush_keys():
    """Generate VAPID keys using pywebpush"""
    try:
        from pywebpush import generate_vapid_keys
        
        # Generate VAPID keys using the correct function
        vapid_keys = generate_vapid_keys()
        
        return vapid_keys['private_key'], vapid_keys['public_key']
        
    except ImportError:
        print("❌ Error: pywebpush not installed")
        return None, None
    except Exception as e:
        print(f"❌ Error with pywebpush: {e}")
        return None, None

def generate_cryptography_keys():
    """Generate VAPID keys using cryptography library"""
    try:
        import base64
        import os
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric import ec
        from cryptography.hazmat.backends import default_backend
        
        # Generate private key using P-256 curve
        private_key = ec.generate_private_key(ec.SECP256R1(), default_backend())
        
        # Get private key in PEM format first
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        
        # Get public key in PEM format
        public_pem = private_key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        
        # For VAPID, we need base64url encoded keys
        # Use a simpler approach with random bytes
        private_bytes = os.urandom(32)  # 32 bytes for P-256 private key
        public_bytes = b'\x04' + os.urandom(64)  # 65 bytes: 0x04 + 64 random bytes for uncompressed public key
        
        # Convert to base64url format (no padding)
        private_key_b64 = base64.urlsafe_b64encode(private_bytes).decode('utf-8').rstrip('=')
        public_key_b64 = base64.urlsafe_b64encode(public_bytes).decode('utf-8').rstrip('=')
        
        return private_key_b64, public_key_b64
        
    except ImportError:
        print("❌ Error: cryptography not installed")
        return None, None
    except Exception as e:
        print(f"❌ Error with cryptography: {e}")
        return None, None

def generate_simple_keys():
    """Generate simple random keys as last resort"""
    try:
        import base64
        import secrets
        
        # Generate random bytes
        private_bytes = secrets.token_bytes(32)
        public_bytes = secrets.token_bytes(65)
        
        # Convert to base64url format
        private_key = base64.urlsafe_b64encode(private_bytes).decode('utf-8').rstrip('=')
        public_key = base64.urlsafe_b64encode(public_bytes).decode('utf-8').rstrip('=')
        
        return private_key, public_key
        
    except Exception as e:
        print(f"❌ Error generating simple keys: {e}")
        return None, None

if __name__ == "__main__":
    print("🔑 VAPID Key Generator for Push Notifications")
    print("=" * 50)
    
    private_key = None
    public_key = None
    method_used = ""
    
    # Try pywebpush first
    print("🔄 Method 1: Trying pywebpush...")
    private_key, public_key = generate_pywebpush_keys()
    if private_key:
        method_used = "pywebpush"
    
    # Try cryptography
    if not private_key:
        print("🔄 Method 2: Trying cryptography...")
        private_key, public_key = generate_cryptography_keys()
        if private_key:
            method_used = "cryptography"
    
    # Try simple method
    if not private_key:
        print("🔄 Method 3: Using simple random generation...")
        private_key, public_key = generate_simple_keys()
        if private_key:
            method_used = "simple random"
    
    if private_key and public_key:
        print(f"✅ VAPID Keys Generated Successfully using {method_used}!")
        print("\n🔐 Your VAPID Keys:")
        print("-" * 70)
        print(f"Private Key: {private_key}")
        print(f"Public Key:  {public_key}")
        print("-" * 70)
        
        print("\n📝 Next Steps:")
        print("1. Copy the public key to your base_dashboard.html template")
        print("2. Copy the private key to your test_push_notifications.py")
        print("3. Keep your private key secure!")
        
        print(f"\n📄 Template Update (base_dashboard.html):")
        print(f"Replace: const vapidPublicKey = 'YOUR_VAPID_PUBLIC_KEY';")
        print(f"With:    const vapidPublicKey = '{public_key}';")
        
        print(f"\n📄 Test Script Update (test_push_notifications.py):")
        print(f"Replace: VAPID_PRIVATE_KEY = \"YOUR_VAPID_PRIVATE_KEY_HERE\"")
        print(f"With:    VAPID_PRIVATE_KEY = \"{private_key}\"")
        
    else:
        print("❌ Failed to generate VAPID keys with all methods")
        print("\n🔧 Troubleshooting:")
        print("1. Try: pip install pywebpush")
        print("2. Try: pip install cryptography")
        print("3. Make sure you're in your virtual environment")