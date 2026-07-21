from sqlmodel import SQLModel , Session , create_engine
from dotenv import load_dotenv
import os
load_dotenv()
DATABASE=os.environ.get("DATABASE_URL")
engine = create_engine(url= DATABASE, echo = False)

def create_table():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session :
        try : 
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise