#!/usr/bin/env python3
"""
Check if required dependencies for real-time chat are installed
"""

def check_dependencies():
    """Check if SocketIO dependencies are installed"""
    print("🔍 Checking Real-Time Chat Dependencies")
    print("=" * 50)
    
    required_packages = [
        'flask_socketio',
        'eventlet',
        'socketio'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package} - Installed")
        except ImportError:
            print(f"❌ {package} - Missing")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n🚨 Missing packages: {', '.join(missing_packages)}")
        print("\n📦 Install missing packages:")
        print("pip install flask-socketio eventlet")
    else:
        print("\n✅ All dependencies are installed!")
    
    return len(missing_packages) == 0

if __name__ == "__main__":
    check_dependencies()