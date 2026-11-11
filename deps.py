from fastapi import Depends, Request, HTTPException
from fastapi.templating import Jinja2Templates
from pwdlib import PasswordHash
from sqlalchemy.orm import Session
from typing import Annotated
from database import engine
from models import User, Post, UserSession


templates = Jinja2Templates(directory='templates')
# 전역 password_hash는 해시 생성/검증 도구, user.password_hash는 저장된 해시 값.
password_hash = PasswordHash.recommended()


# 공통 함수: DB 작업 도구 제공 =======================================
# Depends(get_db)는 아래 함수가 제공하는 db를 매개변수에 넣어 준다.
# Session은 DB 작업 도구이고, UserSession은 로그인 정보를 저장하는 모델이다.
def get_db():
    with Session(engine) as db:
        # db를 제공하고 사용이 끝나면 with가 세션을 닫는다. commit은 각 처리에서 한다.
        yield db

SessionDep = Annotated[Session, Depends(get_db)]


# 공통 함수: 게시글 조회 또는 404 응답 ===============================
# URL의 {post_id}로 글을 찾고, 없으면 404로 처리를 끝낸다.
def get_post_or_404(post_id: int, db: SessionDep):
    # 기본 키로 조회한다. 예: post_id=7이면 posts 테이블의 id=7인 행을 찾는다.
    post = db.get(Post, post_id)

    if post is None:
        raise HTTPException(status_code=404, detail='해당 게시물이 없습니다.')

    return post

PostDep = Annotated[Post, Depends(get_post_or_404)]


# 공통 함수: 현재 로그인 사용자 확인 ================================
# 요청 쿠키의 세션 ID → DB의 세션 행 → 연결된 User 객체 순서로 찾는다.
# 반환값은 로그인한 User 객체 또는 None이다.
def get_current_user(request: Request, db: SessionDep):
    # 이번 요청에서 브라우저가 보낸 session_id 쿠키 값을 꺼낸다.
    session_id = request.cookies.get('session_id')

    # 쿠키가 없으면 로그인한 사용자를 확인할 수 없다.
    if session_id is None:
        return None

    user_session = db.get(UserSession, session_id)

    # 쿠키가 있어도 DB에 해당 세션이 없으면 로그인한 것으로 처리하지 않는다.
    if user_session is None:
        return None

    # 세션에 연결된 User 객체를 반환한다. 현재 코드에는 세션 시간 만료 검사가 없다.
    return user_session.user

CurrentUserDep = Annotated[User | None, Depends(get_current_user)]