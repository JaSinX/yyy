# bot/schemas.py

from pydantic import BaseModel

class PhotoTaskCreate(BaseModel):
    description: str
    image_data: str  # предполагается, что это будет ссылка на изображение

class PhotoTaskUpdate(BaseModel):
    description: str
    image_data: str  # предполагается, что это будет ссылка на изображение

# bot/schemas.py

from pydantic import BaseModel

class TextTaskCreate(BaseModel):
    description: str

class TextTaskUpdate(BaseModel):
    description: str

# bot/schemas.py

from pydantic import BaseModel

class VoiceTaskCreate(BaseModel):
    description: str
    voice_data: str  # Предполагается, что это будет ссылка на аудиофайл

class VoiceTaskUpdate(BaseModel):
    description: str
    voice_data: str  # Предполагается, что это будет ссылка на аудиофайл
