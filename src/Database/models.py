# Библиотеки
import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel

class Template(BaseModel):
    id: str = str(uuid.uuid4()) # UUID
    user_id: int # ID пользователя
    template_name: str # Название шаблона
    template_text: Optional[str] = None # Текст шаблона
    python_code: str # Код на python?
    created_at: datetime = datetime.now() # Время создания

    class Collection:
        name = 'templates'

__all__ = ['Template']