"""Delete PostgreSQL chat conversations that have been inactive for 90 days."""

from src.db import SessionLocal
from src.services.conversation_store import ConversationStore


def main() -> None:
    db = SessionLocal()
    try:
        deleted = ConversationStore.cleanup_expired(db)
        print(f"Deleted {deleted} expired conversations")
    finally:
        db.close()


if __name__ == "__main__":
    main()
