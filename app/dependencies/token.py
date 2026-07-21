from jose import jwt
from dotenv import load_dotenv

load_dotenv()
import os

from datetime import datetime , timedelta , timezone
def create_token(data  : dict)->str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=30)
    to_encode.update({'exp' : expire})
    return jwt.encode(to_encode , os.environ.get("SECRET_KEY") , algorithm=os.environ.get("ALGORITHM"))