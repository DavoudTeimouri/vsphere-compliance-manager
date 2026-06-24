"""
Reset admin password or create admin user from inside the container.

Usage:
    docker exec <backend-container> python scripts/reset_admin.py
    docker exec <backend-container> python scripts/reset_admin.py --password "NewPass@123"
    kubectl exec -n vcm deployment/vcm-backend -- python scripts/reset_admin.py

The script will:
  1. Re-hash the password using the current bcrypt implementation
  2. Create the admin user if it does not exist
  3. Print the credentials to stdout
"""
import sys, os, argparse
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal, engine, Base
from app.core.security import get_password_hash, verify_password
from app.core.config import settings
from app.models.models import User, UserRole

Base.metadata.create_all(bind=engine)

parser = argparse.ArgumentParser(description="Reset VCM admin password")
parser.add_argument("--username", default=settings.ADMIN_USERNAME,
                    help="Admin username (default from ADMIN_USERNAME env)")
parser.add_argument("--password", default=settings.ADMIN_PASSWORD,
                    help="New password (default from ADMIN_PASSWORD env)")
parser.add_argument("--email",    default=settings.ADMIN_EMAIL)
parser.add_argument("--verify",   action="store_true",
                    help="Verify the password after setting it")
args = parser.parse_args()

db = SessionLocal()
try:
    new_hash = get_password_hash(args.password)

    user = db.query(User).filter(User.username == args.username).first()
    if user:
        user.hashed_password = new_hash
        user.is_active = True
        db.commit()
        action = "updated"
    else:
        user = User(
            username=args.username,
            hashed_password=new_hash,
            email=args.email,
            full_name="Administrator",
            role=UserRole.admin,
            is_active=True,
        )
        db.add(user)
        db.commit()
        action = "created"

    print(f"Admin user {action}:")
    print(f"  Username : {args.username}")
    print(f"  Password : {args.password}")
    print(f"  Hash     : {new_hash[:20]}...")

    if args.verify:
        ok = verify_password(args.password, new_hash)
        print(f"  Verify   : {'PASS' if ok else 'FAIL — bcrypt error!'}")
        if not ok:
            sys.exit(1)

    print("\nLogin at: http://localhost:3000")
finally:
    db.close()
