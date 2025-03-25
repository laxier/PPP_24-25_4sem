from sqlalchemy import Column, Integer, String
from ..models import Base

class Token(Base):
    __tablename__ = "tokens"

    id = Column(Integer, primary_key=True, index=True)
    access_token = Column(String, nullable=False)
    token_type = Column(String, nullable=False)
    user_id = Column(Integer, nullable=False)
