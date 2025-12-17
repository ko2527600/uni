"""
Setup script to install pyOpenSSL for HTTPS support
"""

import subprocess
import sys

def install_pyopenssl():
    print("="*60)
    print("🔐 HTTPS Setup for UniPortal")
    print("="*60)
    print("\nThis will install pyOpenSSL to enable HTTPS mode.")
    print("HTTPS is required for geolocation to work on mobile phones.\n")
    
    response = input("Install pyOpenSSL? (y/n): ").lower()
    
    if response == 'y':
        print("\n📦 Installing pyOpenSSL...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "pyOpenSSL"])
            print("\n✅ Installation complete!")
            print("\n🚀 Now you can run:")
            print("   python run.py --https")
            print("\n📱 Then access from your phone:")
            print("   https://YOUR_IP:5000")
            print("   (Accept the security warning)")
        except subprocess.CalledProcessError:
            print("\n❌ Installation failed!")
            print("Try manually: pip install pyOpenSSL")
    else:
        print("\n❌ Installation cancelled.")
        print("\nAlternatives:")
        print("1. Test on computer: http://localhost:5000 (geolocation works)")
        print("2. Use HTTP on phone: http://YOUR_IP:5000 (no geolocation)")
        print("3. Install manually: pip install pyOpenSSL")
    
    print("\n" + "="*60)

if __name__ == '__main__':
    install_pyopenssl()
