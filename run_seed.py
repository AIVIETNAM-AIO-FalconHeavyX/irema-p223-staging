from src.db import SessionLocal
from src.db.crud import seed_onboarding_steps
db = SessionLocal()
seed_onboarding_steps(db)
db.close()
