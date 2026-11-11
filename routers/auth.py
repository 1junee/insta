# 설치한 모듈
from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse
from sqlalchemy import select
import secrets

# 우리가 만든 파일
from deps import templates, password_hash, CurrentUserDep, SessionDep
from models import User, UserSession


router = APIRouter()


# SIGNUP 1: 회원가입 폼 표시 (GET) ===================================
@router.get('/signup')
def signup_form(request: Request, user: CurrentUserDep):
    return templates.TemplateResponse(
        request=request, name='signup.html', context={'user': user}
    )


# SIGNUP 2: 입력한 아이디와 비밀번호로 가입 처리 (POST) ===============
@router.post('/signup')
def signup(
    request: Request,
    db: SessionDep,
    username: str = Form(),
    password: str = Form(),
):
    # 입력한 아이디로 조회한다. 결과는 User 객체 또는 None이다.
    exists = db.scalar(select(User).where(User.username == username))

    # 중복 아이디라면 가입 화면에 에러를 표시하고 return으로 처리를 끝낸다.
    if exists:
        return templates.TemplateResponse(
            request=request,
            name='signup.html',
            context={'error': '이미 있는 아이디입니다.'},
        )


    # 비밀번호 원문 대신 해시를 저장한다. 해시는 복호화해서 원문을 꺼내는 방식이 아니다.
    hashed_pw = password_hash.hash(password)

    # 가입 정보를 만든다. 회원가입만으로 로그인 세션까지 생성되는 것은 아니다.
    user = User(username=username, password_hash=hashed_pw)
    db.add(user)
    db.commit()

    return RedirectResponse('/login', status_code=303)


# LOGIN 1: 로그인 폼 표시 (GET) ======================================
@router.get('/login')
def login_form(request: Request, user: CurrentUserDep):
    return templates.TemplateResponse(
        request=request, name='login.html', context={'user': user}
    )


# LOGIN 2: 비밀번호 확인 → 세션 저장 → 쿠키 전달 ======================
@router.post('/login')
def login(
    request: Request,
    db: SessionDep,
    username: str = Form(),
    password: str = Form(),
):
    # 1. 폼에서 받은 아이디에 해당하는 사용자를 찾는다.
    user = db.scalar(select(User).where(User.username == username))

    # 2. verify(입력한 비밀번호, 저장된 해시)로 일치 여부를 확인한다.
    # or는 왼쪽이 참이면 오른쪽을 실행하지 않아 None의 속성에 접근하지 않는다.
    if (user is None) or not (password_hash.verify(password, user.password_hash)):
        return templates.TemplateResponse(
            request=request,
            name='login.html',
            context={'error': '아이디가 존재하지 않거나 비밀번호가 틀렸습니다.'},
        )

    # 3. 검증 성공: 다음 요청에서도 사용자를 식별할 임의의 세션 ID를 만든다.
    session_id = secrets.token_urlsafe(32)
    # 4. DB에 "이 세션 ID는 이 사용자의 것"이라는 연결을 저장한다.
    user_session = UserSession(id=session_id, user=user)
    db.add(user_session)
    db.commit()

    response = RedirectResponse('/posts', status_code=303)
    # 5. 쿠키로 세션 ID를 전달한다. 브라우저가 이후 요청에 이 값을 보내게 된다.
    # httponly는 JS의 쿠키 읽기를 막고, samesite는 다른 사이트에서 온 요청의 쿠키 전송을 제한한다.
    response.set_cookie('session_id', session_id, httponly=True, samesite='lax')
    return response


# LOGOUT: 현재 로그인 세션과 브라우저 쿠키 삭제 =======================
# 사용자 계정이나 게시글을 삭제하는 것은 아니다.
@router.post('/logout')
def logout(request: Request, db: SessionDep):
    # 이번 요청에서 브라우저가 보낸 session_id 쿠키 값을 꺼낸다.
    session_id = request.cookies.get('session_id')
    user_session = db.get(UserSession, session_id)

    if user_session:
        db.delete(user_session)
        db.commit()

    response = RedirectResponse('/posts', status_code=303)
    # DB 세션 삭제에 이어 브라우저에도 쿠키를 지우도록 응답한다.
    response.delete_cookie('session_id')
    return response