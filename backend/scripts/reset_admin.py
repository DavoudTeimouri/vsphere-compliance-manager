"""
Reset admin password or create admin user.
Run inside the backend container:

    docker exec vcm-test-backend python scripts/reset_admin.py
    docker exec vcm-test-backend python scripts/reset_admin.py --password "NewPass@123"
"""
import sys
import os
import argparse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal, engine, Base
from app.core.security import get_password_hash
from app.core.config import settings
from app.models.models import User, UserRole

Base.metadata.create_all(bind=engine)

parser = argparse.ArgumentParser()
parser.add_argument("--username", default=settings.ADMIN_USERNAME)
parser.add_argument("--password", default=settings.ADMIN_PASSWORD)
parser.add_argument("--email",    default=settings.ADMIN_EMAIL)
args = parser.parse_args()

db = SessionLocal()
try:
    user = db.query(User).filter(User.username == args.username).first()
    if user:
        user.hashed_password = get_password_hash(args.password)
        user.is_active = True
        db.commit()
        print(f"✓ Password reset for '{args.username}'")
    else:
        user = User(
            username=args.username,
            hashed_password=get_password_hash(args.password),
            email=args.email,
            full_name="Administrator",
            role=UserRole.admin,
            is_active=True,
        )
        db.add(user)
        db.commit()
        print(f"✓ Admin user '{args.username}' created")

    print(f"  Username: {args.username}")
    print(f"  Password: {args.password}")
finally:
    db.close()
