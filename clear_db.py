from app import create_app, db
import os

app = create_app()

with app.app_context():
    # Drop all tables
    db.drop_all()
    # Recreate all tables
    db.create_all()
    print("Database cleared successfully!")
    print("All tables have been recreated and are now empty.")
