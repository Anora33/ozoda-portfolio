from sqlalchemy import create_engine, Column, Integer, String
# create_url degan so'zni olib tashladik, chunki u xatolik beryapti
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Ma'lumotlar bazasi fayli nomi: portfolio.db
SQLALCHEMY_DATABASE_URL = "sqlite:///./portfolio.db"

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Bazada "users" jadvalini yaratish
class UserDB(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    fullname = Column(String)
    email = Column(String, unique=True, index=True)

# Jadvalni yaratish buyrug'i
Base.metadata.create_all(bind=engine)