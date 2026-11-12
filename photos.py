from fastapi import UploadFile
from pathlib import Path
import uuid
import shutil
from PIL import Image, ImageOps
from pillow_heif import register_heif_opener

# Pillow의 Image.open()이 HEIC 파일도 읽을 수 있도록 등록
register_heif_opener()

Path('media').mkdir(exist_ok=True)

def save_photo(photo: UploadFile):
    # 실제 인스타 같은 큰 서비스의 파일시스템 같은 경우는 년월일순으로, 등등 기록해서 저장
    ## '.' + photo.filename.split('.')[-1]
    # ext = Path(photo.filename).suffix # => imagename.jpeg

    # name = f'{uuid.uuid4().hex}{ext}' # 3928984e1f53.jpeg

    # 'wb' 옵션  byte 단위 기록 (사진)
    # with open(f'media/{name}', 'wb') as f:
    #     shutil.copyfileobj(photo.file, f)

    image = Image.open(photo.file)             # HEIC도 읽기 가능
    image = ImageOps.exif_transpose(image)     # 촬영 방향 반영
    image = image.convert('RGB')               # JPEG 저장용 색상 모드
    image = ImageOps.fit(image, (1080, 1080))

    name = f'{uuid.uuid4().hex}.jpg'
    image.save(f'media/{name}')

    return f'/media/{name}'