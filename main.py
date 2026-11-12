from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from routers import posts, auth, users

# 앱 및 HTML 템플릿 설정 ============================================
app = FastAPI()

app.include_router(posts.router)
app.include_router(auth.router)
app.include_router(users.router)

# media 폴더의 파일을 브라우저에서 /media 주소로 볼 수 있게 연결한다.
app.mount('/media', StaticFiles(directory='media'), name='media')
app.mount('/static', StaticFiles(directory='static'), name='static')

# HOME: 기본 응답 확인 ==============================================
@app.get('/')
def home():
    return {'hi': 'hello'}
