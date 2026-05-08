#!/bin/bash
set -e

echo "Running database migrations..."
alembic upgrade head || {
    echo "Alembic migration failed, falling back to create_all..."
    python -c "from app.database import Base, engine; from app.models import *; Base.metadata.create_all(bind=engine)"
}

echo "Initializing default data..."
python -c "
from app.database import SessionLocal
from app.models import SiteConfig, User
db = SessionLocal()
if not db.query(SiteConfig).filter(SiteConfig.key == 'teacher_invite_code').first():
    db.add(SiteConfig(key='teacher_invite_code', value='FUSHUA2024'))
    db.commit()
first_teacher = db.query(User).filter(User.role == 'teacher').first()
if first_teacher and not first_teacher.is_admin:
    first_teacher.is_admin = True
    db.commit()
db.close()
print('Default data initialized.')
"

echo "Starting application..."
exec "$@"
