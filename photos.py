from fastapi import UploadFile
from pathlib import Path
import uuid
import shutil

Path('media').mkdir(exist_ok=True)

def save_photo(photo: UploadFile):
    # 실제 인스타 같은 큰 서비스의 파일시스템 같은 경우는 년월일순으로, 등등 기록해서 저장

    ext = Path(photo.filename).suffix # => imagename.jpeg
    # '.' + photo.filename.split('.')[-1]

    name = f'{uuid.uuid4().hex}{ext}' # 3928984e1f53.jpeg

    # 'wb' 옵션  byte 단위 기록 (사진)
    with open(f'media/{name}', 'wb') as f:
        shutil.copyfileobj(photo.file, f)

    return f'/media/{name}'