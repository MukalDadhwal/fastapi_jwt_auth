# All the schemas for the api
from typing import BaseModel

class User(BaseModel):
    user_id: str = None
    username: str
    hashed_password: str
    email: str


class UserCred(BaseModel):
    user_name: str = None
    email: str = None
    password: str
