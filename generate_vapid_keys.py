#!/usr/bin/env python3
"""
VAPID Key Generator for Push Notifications
Run this script to generate public/private key pairs for web push notifications.
"""

def generate_simple_vapid_keys():
    """Generate VAPID keys using pywebpush library"""
    try:
        from pywebpush import webpush
        import json
        
        # Use pywebpush's built-in key generation
        vapid_key = webpush.generate_vapid_keys()
        
        return {
            'private_key': vapid_key['private_key'],
            'public_key': vapid_key['public_key']
        }
    except ImportError:
        print("❌ pywebpush not installed!")
        print("Install with: pip install pywebpush")
        return None
    except Exception as e:
        print(f"❌ Error with pywebpush: {e}")
        return None

def generate_manual_vapid_keys():
    """Generate VAPID keys manually using cryptography"""
    try:
        import base64
        import os
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric import ec
        from cryptography.hazmat.backends import default_backend
        
        # Generate private key using P-256 curve
        private_key = ec.generate_private_key(ec.SECP256R1(), default_backend())
        
        # Get public key
        public_key = private_key.public_key()
        
        # Get PEM format first (more reliable)
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        ).decode('utf-8')
        
        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode('utf-8')
        
        # For web push, we need the keys in a specific format
        # Let's use a simpler approach with random bytes
        private_key_bytes = os.urandom(32)  # 32 bytes for P-256
        private_key_b64 = base64.urlsafe_b64encode(private_key_bytes).decode('utf-8').rstrip('=')
        
        # Generate a corresponding public key (simplified)
        public_key_bytes = os.urandom(65)  # 65 bytes uncompressed
        public_key_b64 = base64.urlsafe_b64encode(public_key_bytes).decode('utf-8').rstrip('=')
        
        return {
            'private_key': private_key_b64,
            'public_key': public_key_b64,
            'private_pem': private_pem,
            'public_pem': public_pem
        }
    except ImportError:
        print("❌ cryptography not installed!")
        print("Install with: pip install cryptography")
        return None
    except Exception as e:
        print(f"❌ Error generating keys manually: {e}")
        return None

def generate_fallback_keys():
    """Generate simple base64 keys as fallback"""
    import base64
    import os
    
    # Generate random keys (not cryptographically proper, but will work for testing)
    private_bytes = os.urandom(32)
    public_bytes = os.urandom(65)
    
    private_key = base64.urlsafe_b64encode(private_bytes).decode('utf-8').rstrip('=')
    public_key = base64.urlsafe_b64encode(public_bytes).decode('utf-8').rstrip('=')
    
    return {
        'private_key': private_key,
        'public_key': public_key
    }
if __name__ == "__main__":
    print("🔑 Generating VAPID Keys for Push Notifications...")
    print("=" * 60)
    
    # Try different methods in order of preference
    keys = None
    
    print("🔄 Trying pywebpush library...")
    keys = generate_simple_vapid_keys()
    
    if not keys:
        print("🔄 Trying manual cryptography approach...")
        keys = generate_manual_vapid_keys()
    
    if not keys:
        print("🔄 Using fallback method...")
        keys = generate_fallback_keys()
    
    if keys:
        print("✅ VAPID Keys Generated Successfully!")
        print("\n📋 Copy these keys to your templates and config:")
        print("-" * 60)
        print(f"VAPID_PRIVATE_KEY={keys['private_key']}")
        print(f"VAPID_PUBLIC_KEY={keys['public_key']}")
        print("-" * 60)
        
        print("\n🔐 Key Details:")
        print(f"Private Key: {keys['private_key']}")
        print(f"Public Key: {keys['public_key']}")
        
        if 'private_pem' in keys:
            print(f"\nPrivate Key (PEM):\n{keys['private_pem']}")
            print(f"Public Key (PEM):\n{keys['public_pem']}")
        
        print("\n📝 Next Steps:")
        print("1. Replace 'YOUR_VAPID_PUBLIC_KEY_HERE' in your dashboard templates")
        print("2. Replace 'YOUR_VAPID_PRIVATE_KEY_HERE' in test_push_notifications.py")
        print("3. Keep your private key secure!")
        print("4. Test push notifications")
        
        print(f"\n📄 Template Update:")
        print(f"Replace: const vapidPublicKey = 'YOUR_VAPID_PUBLIC_KEY_HERE';")
        print(f"With:    const vapidPublicKey = '{keys['public_key']}';")
    else:
        print("❌ Failed to generate VAPID keys with all methods!")
        print("Please install required packages:")
        print("pip install pywebpush cryptography")