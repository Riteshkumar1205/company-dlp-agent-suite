from pydantic import BaseModel
from typing import Optional, Dict

class CommandCreate(BaseModel):
    type: str
    payload: Optional[Dict] = None
