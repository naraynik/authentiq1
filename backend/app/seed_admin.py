import sys
import logging
from app.database.database import SessionLocal
from app.models.user import User
from app.core.config import settings
from app.core.security import hash_password

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("seed_admin")

def seed_admin():
    # Make sure the tables exist, so this also works before the API has ever started.
    from app.database.database import engine
    from app.database.base import Base
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        admin_email = settings.ADMIN_EMAIL.strip().lower()
        admin_password = settings.ADMIN_PASSWORD

        if not admin_email or not admin_password:
            logger.error("ADMIN_EMAIL and ADMIN_PASSWORD must be configured in environment variables or settings.")
            sys.exit(1)

        existing_admin = db.query(User).filter(User.email == admin_email).first()
        if existing_admin:
            logger.info(f"Admin user '{admin_email}' already exists. Updating credentials and ensuring role=ADMIN...")
            existing_admin.password_hash = hash_password(admin_password)
            existing_admin.role = "ADMIN"
            existing_admin.is_active = True
            db.commit()
            logger.info(f"Admin user '{admin_email}' updated successfully.")
        else:
            logger.info(f"Seeding new admin user '{admin_email}'...")
            admin_user = User(
                email=admin_email,
                password_hash=hash_password(admin_password),
                role="ADMIN",
                is_active=True
            )
            db.add(admin_user)
            db.commit()
            logger.info(f"Admin user '{admin_email}' seeded successfully.")
    except Exception as e:
        logger.error(f"Error seeding admin user: {e}")
        db.rollback()
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    seed_admin()
