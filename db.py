from sqlmodel import create_engine, Session
from data import FundNav

engine = create_engine(
    "postgresql://postgres:fam-demo@localhost:5432/postgres",
    echo=True
)


def get_session():
    with Session(engine) as session:
        yield session
