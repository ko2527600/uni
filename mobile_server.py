#!/usr/bin/env python3
"""
Mobile Server Configuration for UniPortal
Helps configure the Flask app to be accessible from mobile devices
"""

import socket
import subprocess
import platform
import os
from flask import Flask

def get_local_ip():
    """Get the local IP address of this machine"""
    try:
        # Connect to a remote address to determine local IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception:
        return "127.0.0.1"

def get_network_interfaces():
    """Get all network interfaces and their IP addresses"""
    interfaces = {}
    
    try:
        if platform.system() == "Windows":
            # Windows command
            result = subprocess.run(['ipconfig'], capture_output=True, text=True)
            output = result.stdout
            
            current_interface = None
            for line in output.split('\n'):
                line = line.strip()
                if 'adapter' in line.lower() and ':' in line:
                    current_interface = line
                elif 'IPv4 Address' in line and current_interface:
                    ip = line.split(':')[-1].strip()
                    if ip and not ip.startswith('127.'):
                        interfaces[current_interface] = ip
        else:
            # Linux/Mac command
            result = subprocess.run(['ifconfig'], capture_output=True, text=True)
            # Parse ifconfig output (simplified)
            pass
            
    except Exception as e:
        print(f"Error getting network interfaces: {e}")
    
    return interfaces

def check_firewall_status():
    """Check Windows Firewall status"""
    try:
        if platform.system() == "Windows":
            result = subprocess.run([
                'netsh', 'advfirewall', 'show', 'allprofiles', 'state'
            ], capture_output=True, text=True)
            return result.stdout
    except Exception:
        return "Could not check firewall status"

def create_firewall_rule(port=5000):
    """Create Windows Firewall rule for Flask app"""
    try:
        if platform.system() == "Windows":
            # Check if running as administrator
            import ctypes
            is_admin = ctypes.windll.shell32.IsUserAnAdmin()
            
            if not is_admin:
                print("⚠️  Administrator privileges required to create firewall rules")
                print("   Run this script as Administrator or manually add firewall rule")
                return False
            
            # Create inbound rule
            cmd = [
                'netsh', 'advfirewall', 'firewall', 'add', 'rule',
                f'name=UniPortal Flask App Port {port}',
                'dir=in',
                'action=allow',
                'protocol=TCP',
                f'localport={port}'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                print(f"✅ Firewall rule created for port {port}")
                return True
            else:
                print(f"❌ Failed to create firewall rule: {result.stderr}")
                return False
                
    except Exception as e:
        print(f"Error creating firewall rule: {e}")
        return False

def generate_mobile_config():
    """Generate configuration for mobile access"""
    local_ip = get_local_ip()
    interfaces = get_network_interfaces()
    
    print("🔧 UniPortal Mobile Access Configuration")
    print("=" * 50)
    print(f"📱 Local IP Address: {local_ip}")
    print(f"🌐 Mobile Access URL: http://{local_ip}:5000")
    print()
    
    print("📡 Available Network Interfaces:")
    for interface, ip in interfaces.items():
        print(f"   {interface}: {ip}")
    print()
    
    print("🔥 Firewall Configuration:")
    firewall_status = check_firewall_status()
    print(firewall_status)
    print()
    
    print("📋 Mobile Access Checklist:")
    print("   ✓ 1. Ensure your phone is on the same WiFi network")
    print("   ✓ 2. Use the IP address shown above (not localhost)")
    print("   ✓ 3. Make sure Windows Firewall allows the connection")
    print("   ✓ 4. Try disabling antivirus temporarily if still blocked")
    print()
    
    # Ask if user wants to create firewall rule
    try:
        create_rule = input("🛡️  Create Windows Firewall rule for port 5000? (y/n): ").lower()
        if create_rule == 'y':
            create_firewall_rule(5000)
    except KeyboardInterrupt:
        print("\nConfiguration cancelled.")
    
    print()
    print("🚀 To start the server for mobile access, run:")
    print(f"   python run.py --host=0.0.0.0 --port=5000")
    print()
    print("📱 Then access from your phone:")
    print(f"   http://{local_ip}:5000")

if __name__ == "__main__":
    generate_mobile_config()