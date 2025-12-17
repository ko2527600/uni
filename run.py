from app import create_app, db, socketio
from app.models import University, ClassGroup, User

app = create_app()

def setup_database():
    """Initialize database with default data including join codes"""
    with app.app_context():
        # Create all tables
        db.create_all()
        
        # Check if data already exists
        if University.query.first():
            print("Database already initialized.")
            return
        
        print("Setting up database with default data...")
        
        # Create default university
        university = University(
            name='University of Ghana',
            domain='ug.edu.gh'
        )
        db.session.add(university)
        db.session.commit()
        
        # Create default class groups with join codes and lecturer codes
        classes = [
            {'name': 'Level 100 CS', 'code': 'CS-100', 'join_code': 'CS100', 'lecturer_code': 'LEC100CS'},
            {'name': 'Level 200 CS', 'code': 'CS-200', 'join_code': 'CS200', 'lecturer_code': 'LEC200CS'},
            {'name': 'Level 300 IT', 'code': 'IT-300', 'join_code': 'IT300', 'lecturer_code': 'LEC300IT'}
        ]
        
        for class_data in classes:
            class_group = ClassGroup(
                name=class_data['name'],
                code=class_data['code'],
                join_code=class_data['join_code'],
                lecturer_code=class_data['lecturer_code'],
                university_id=university.id
            )
            db.session.add(class_group)
        
        db.session.commit()
        
        print("✅ Database setup complete!")
        print("\n📋 Available Class Codes:")
        print("   Level 100 CS:")
        print("      Student Code: CS100")
        print("      Lecturer Code: LEC100CS")
        print("   Level 200 CS:")
        print("      Student Code: CS200")
        print("      Lecturer Code: LEC200CS")
        print("   Level 300 IT:")
        print("      Student Code: IT300")
        print("      Lecturer Code: LEC300IT")
        print("\nStudents/Reps use Student Codes. Lecturers use Lecturer Codes at /claim_class\n")

if __name__ == '__main__':
    # Setup database on first run
    setup_database()
    
    # Get local IP address
    import socket
    import sys
    
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        
        print("\n" + "="*60)
        print("🌐 SERVER STARTED")
        print("="*60)
        print(f"\n📱 Access from your phone:")
        print(f"   http://{local_ip}:5000")
        print(f"\n💻 Access from this computer:")
        print(f"   http://localhost:5000")
        print(f"\n⚠️  IMPORTANT:")
        print(f"   - Phone must be on SAME WiFi network")
        print(f"   - Geolocation works on computer (localhost)")
        print(f"   - Geolocation on phone needs HTTPS (see below)")
        print(f"\n🔒 For geolocation on phone, use HTTPS:")
        print(f"   Run: python run.py --https")
        print(f"   Then: https://{local_ip}:5000")
        print(f"   (Accept security warning in browser)")
        print("\n" + "="*60 + "\n")
    except:
        print("\n🌐 Server starting...")
        print("📱 Run 'ipconfig' to find your IP address\n")
    
    # Check if --https flag is provided
    use_https = '--https' in sys.argv
    
    if use_https:
        # Generate self-signed certificate for HTTPS
        import ssl
        import os
        
        cert_file = 'cert.pem'
        key_file = 'key.pem'
        
        # Generate certificate if it doesn't exist
        if not os.path.exists(cert_file) or not os.path.exists(key_file):
            print("🔐 Generating self-signed SSL certificate...")
            try:
                from OpenSSL import crypto
                
                # Create key pair
                k = crypto.PKey()
                k.generate_key(crypto.TYPE_RSA, 2048)
                
                # Create self-signed cert
                cert = crypto.X509()
                cert.get_subject().C = "GH"
                cert.get_subject().ST = "Greater Accra"
                cert.get_subject().L = "Accra"
                cert.get_subject().O = "UniPortal"
                cert.get_subject().OU = "Development"
                cert.get_subject().CN = local_ip
                cert.set_serial_number(1000)
                cert.gmtime_adj_notBefore(0)
                cert.gmtime_adj_notAfter(365*24*60*60)  # Valid for 1 year
                cert.set_issuer(cert.get_subject())
                cert.set_pubkey(k)
                cert.sign(k, 'sha256')
                
                # Save certificate and key
                with open(cert_file, "wb") as f:
                    f.write(crypto.dump_certificate(crypto.FILETYPE_PEM, cert))
                with open(key_file, "wb") as f:
                    f.write(crypto.dump_privatekey(crypto.FILETYPE_PEM, k))
                
                print("✅ SSL certificate generated!")
            except ImportError:
                print("❌ pyOpenSSL not installed. Install with: pip install pyOpenSSL")
                print("   Or use HTTP mode (geolocation won't work on phone)")
                sys.exit(1)
        
        # Create SSL context
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(cert_file, key_file)
        
        print("🔒 Running in HTTPS mode")
        print("⚠️  You'll need to accept the security warning in your browser")
        
        # Run with HTTPS using SocketIO
        socketio.run(app, host='0.0.0.0', port=5000, debug=True, ssl_context=context)
    else:
        # Run with HTTP (default) using SocketIO
        socketio.run(app, host='0.0.0.0', port=5000, debug=True)
