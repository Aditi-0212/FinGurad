"""Create the shared account registry. Each company's finance tables are created in its own schema at signup."""

from app.database.models import Account, AccountUser
from app.database.session import Base, engine


def main():
    Base.metadata.create_all(bind=engine, tables=[Account.__table__, AccountUser.__table__])
    print("FinGuard account registry is ready. New company workspaces start empty.")


if __name__ == "__main__":
    main()
