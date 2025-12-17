"""
Quick network check script to help you access the app from your phone
"""

import socket

def get_local_ip():
    """Get the local IP address of this computer"""
    try:
        # Create a socket connection to get local IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception as e:
        return None

def main():
    print("=" * 60)
    print("📱 PHONE ACCESS CHECKER")
    print("=" * 60)
    
    local_ip = get_local_ip()
    
    if local_ip:
        print(f"\n✅ Your computer's IP address: {local_ip}")
        print(f"\n📱 On your phone, open browser and go to:")
        print(f"   http://{local_ip}:5000")
        print(f"\n⚠️  IMPORTANT:")
        print(f"   1. Make sure your phone is on the SAME WiFi as this computer")
        print(f"   2. Make sure Flask server is running (python run.py)")
        print(f"   3. If using Windows, check firewall settings")
        print(f"\n🔒 For geolocation features on phone:")
        print(f"   - You need HTTPS (not HTTP)")
        print(f"   - Use ngrok: ngrok http 5000")
        print(f"   - Or deploy to a server with SSL certificate")
    else:
        print("\n❌ Could not detect IP address automatically")
        print("\n📋 Manual steps:")
        print("   Windows: Open cmd and type 'ipconfig'")
        print("   Mac/Linux: Open terminal and type 'ifconfig'")
        print("   Look for IPv4 Address (usually starts with 192.168 or 10.0)")
        print("\n   Then on your phone, go to: http://YOUR_IP:5000")
    
    print("\n" + "=" * 60)
    print("Need more help? Check PHONE_ACCESS_GUIDE.md")
    print("=" * 60)

if __name__ == '__main__':
    main()
