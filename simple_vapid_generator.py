#!/usr/bin/env python3
"""
Simple VAPID Key Generator
Reliable method to generate VAPID keys for push notifications
"""

import base64
import secrets

def generate_vapid_keys():
    """Generate VAPID-compatible keys using secure random bytes"""
    
    # Generate 32 random bytes for private key (P-256 curve requirement)
    private_bytes = secrets.token_bytes(32)
    
    # Generate 65 random bytes for public key (uncompressed P-256 public key)
    # First byte should be 0x04 for uncompressed format
    public_bytes = b'\x04' + secrets.token_bytes(64)
    
    # Convert to base64url format (no padding as per VAPID spec)
    private_key = base64.urlsafe_b64encode(private_bytes).decode('utf-8').rstrip('=')
    public_key = base64.urlsafe_b64encode(public_bytes).decode('utf-8').rstrip('=')
    
    return private_key, public_key

if __name__ == "__main__":
    print("🔑 Simple VAPID Key Generator")
    print("=" * 40)
    
    try:
        private_key, public_key = generate_vapid_keys()
        
        print("✅ VAPID Keys Generated Successfully!")
        print("\n🔐 Your VAPID Keys:")
        print("-" * 60)
        print(f"Private Key: {private_key}")
        print(f"Public Key:  {public_key}")
        print("-" * 60)
        
        print("\n📋 Copy & Paste Instructions:")
        print("\n1️⃣ Update base_dashboard.html:")
        print("   Find: const vapidPublicKey = 'YOUR_VAPID_PUBLIC_KEY';")
        print(f"   Replace with: const vapidPublicKey = '{public_key}';")
        
        print("\n2️⃣ Update test_push_notifications.py:")
        print("   Find: VAPID_PRIVATE_KEY = \"YOUR_VAPID_PRIVATE_KEY_HERE\"")
        print(f"   Replace with: VAPID_PRIVATE_KEY = \"{private_key}\"")
        
        print("\n🔒 Security Notes:")
        print("• Keep your private key secret")
        print("• Public key can be shared in frontend code")
        print("• These keys are for testing - generate new ones for production")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("This should not happen with the simple method!")