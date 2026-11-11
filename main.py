from fastapi import FastAPI
from routers import posts, auth, users

# 앱 및 HTML 템플릿 설정 ============================================
app = FastAPI()

app.include_router(posts.router)
app.include_router(auth.router)
app.include_router(users.router)

# HOME: 기본 응답 확인 ==============================================
@app.get('/')
def home():
    return {'hi': 'hello'}