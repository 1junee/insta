from fastapi import FastAPI, Request, Depends, Form, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from sqlalchemy import create_engine, select, func, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, Session, relationship
from datetime import datetime
from pwdlib import PasswordHash
import secrets

# DB 연결 설정: engine은 연결을 관리하고 echo=True는 실행 SQL을 출력한다.
DB_URL = 'postgresql+psycopg://sd4:sd4@localhost:5432/insta'
engine = create_engine(DB_URL, echo=True)


# MODEL: DB에 저장할 데이터 구조 =====================================
# 모델 클래스는 테이블에, 객체 하나는 행 하나에 대응한다.
# Mapped[...]는 값의 타입, mapped_column은 DB 열의 설정이다.
class Base(DeclarativeBase):
    pass


# 게시글: 작성자 한 명(user)과 댓글 여러 개(comments)에 연결된다.
class Post(Base):
    __tablename__ = 'posts'

    id: Mapped[int] = mapped_column(primary_key=True)
    content: Mapped[str]
    # 작성 시각을 생략하면 DB가 현재 시각을 기본값으로 넣는다.
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    # post.comments: 이 글의 id를 post_id로 가진 댓글들. DB 열이 아닌 관계 속성이다.
    # back_populates는 반대편 Comment.post의 속성 이름이다.
    # cascade는 ORM으로 글을 삭제하거나 관계에서 댓글을 분리할 때 댓글 삭제를 처리한다.
    comments: Mapped[list['Comment']] = relationship(
        back_populates='post', cascade='all, delete-orphan'
    )
    # DB에 저장하는 사용자 번호. 아래 user는 그 번호에 연결된 User 객체이다.
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    user: Mapped['User'] = relationship(back_populates='posts')

    likes: Mapped[list['Like']] = relationship(cascade='all, delete-orphan')


# 댓글: post_id로 어느 게시글에 달린 댓글인지 구분한다.
class Comment(Base):
    __tablename__ = 'comments'

    id: Mapped[int] = mapped_column(primary_key=True)
    content: Mapped[str]
    # 작성 시각을 생략하면 DB가 현재 시각을 기본값으로 넣는다.
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    # 예: 댓글 id=21, post_id=7 → 21번 댓글이 7번 게시글에 달렸다.
    
    # ForeignKey는 DB에서 posts.id를 참조하도록 하는 연결 기준이다.
    # Post(1) : Comment(N)
    post_id: Mapped[int] = mapped_column(ForeignKey('posts.id'))
    # comment.post는 연결된 게시글 객체. Comment.post와 Post.comments는 서로 짝이다.
    post: Mapped['Post'] = relationship(back_populates='comments')
    # User(1) : Comment(N)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    user: Mapped['User'] = relationship()

# 사용자: 가입 정보와 비밀번호 해시를 저장한다.
class User(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True)
    # unique=True: 동일한 로그인 아이디가 중복 저장되지 않게 한다.
    username: Mapped[str] = mapped_column(unique=True)
    password_hash: Mapped[str]
    # user.posts: 이 사용자가 작성한 글들. 반대편 Post.user와 연결된다.
    posts: Mapped[list['Post']] = relationship(back_populates='user')
    # 댓글만 모아보기 - 
    # comments: Mapped[list['Comment']] = relationship(back_populates='user')


# 로그인 세션: 임의의 세션 ID와 사용자 번호를 DB에 연결한다.
# 같은 사용자가 여러 번 로그인하면 세션 행도 여러 개 생길 수 있다.
class UserSession(Base):
    __tablename__ = 'sessions'

    # 로그인 성공 시 생성할 임의의 문자열. 사용자 번호와는 다른 값이다.
    id: Mapped[str] = mapped_column(primary_key=True)
    # DB에 저장하는 사용자 번호. 아래 user는 그 번호에 연결된 User 객체이다.
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    # 작성 시각을 생략하면 DB가 현재 시각을 기본값으로 넣는다.
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    # user_session.user로 사용자에 접근한다. 여기서는 단방향 관계만 사용한다.
    user: Mapped['User'] = relationship()


# 좋아요: 
class Like(Base):
    __tablename__ = 'likes'

    # User(N) : Like(1) : Post(M)
    user_id: Mapped[int] = mapped_column(
        ForeignKey('users.id'), 
        primary_key=True,
    )
    post_id: Mapped[int] = mapped_column(
        ForeignKey('posts.id'), 
        primary_key=True,
    )


# 앱 및 HTML 템플릿 설정 ============================================
app = FastAPI()
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


# 공통 함수: 게시글 조회 또는 404 응답 ===============================
# URL의 {post_id}로 글을 찾고, 없으면 404로 처리를 끝낸다.
def get_post_or_404(post_id: int, db: Session = Depends(get_db)):
    # 기본 키로 조회한다. 예: post_id=7이면 posts 테이블의 id=7인 행을 찾는다.
    post = db.get(Post, post_id)

    if post is None:
        raise HTTPException(status_code=404, detail='해당 게시물이 없습니다.')

    return post


# 공통 함수: 현재 로그인 사용자 확인 ================================
# 요청 쿠키의 세션 ID → DB의 세션 행 → 연결된 User 객체 순서로 찾는다.
# 반환값은 로그인한 User 객체 또는 None이다.
def get_current_user(request: Request, db: Session = Depends(get_db)):
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




# HOME: 기본 응답 확인 ==============================================
@app.get('/')
def home():
    return {'hi': 'hello'}


# READ ALL: 전체 게시글 화면 ========================================
# Request는 현재 HTTP 요청, User | None은 사용자 객체 또는 None이라는 타입 표시.
# Depends(get_current_user)의 반환값이 user에 들어간다.
@app.get('/posts')
def post_list(
    request: Request,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_current_user),
):
    liked_ids = []
    if user:
        liked_ids = db.scalars( select(Like.post_id).where( user.id == Like.user_id ) ).all()

    # select로 조회 조건 생성 → scalars로 Post 객체 조회 → all로 목록 받기.
    # created_at.desc()는 최근에 작성한 글부터 정렬한다.
    posts = db.scalars(select(Post).order_by(Post.created_at.desc())).all()
    return templates.TemplateResponse(
        # context에 넣은 이름을 HTML에서 posts, user 변수로 사용할 수 있다.
        request=request, 
        name='list.html', 
        context={'posts': posts, 'user': user, 'liked_ids': liked_ids}
    )


# CREATE 1: 글 작성 폼 표시 (GET) ====================================
@app.get('/posts/new')
def post_new(request: Request, user: User | None = Depends(get_current_user)):
    # 로그인 사용자 정보가 없으면 로그인 화면으로 이동한다.
    if user is None:
        return RedirectResponse('/login', status_code=303)

    return templates.TemplateResponse(
        request=request, name='new.html', context={'user': user}
    )


# CREATE 2: 입력한 글 저장 (POST) ====================================
# Form()은 HTML의 name="content"로 보낸 입력값을 받는다.
@app.post('/posts/create')
def post_create(
    content: str = Form(),
    db: Session = Depends(get_db),
    user: User | None = Depends(get_current_user),
):
    # 로그인 사용자 정보가 없으면 로그인 화면으로 이동한다.
    if user is None:
        # 303 응답: 브라우저가 지정된 주소를 GET으로 다시 요청하도록 안내한다.
        return RedirectResponse('/login', status_code=303)

    # 현재 로그인한 User를 작성자로 연결한다. 저장 시 post.user_id에 반영된다.
    post = Post(content=content, user=user)
    # 객체 생성만으로 저장되지는 않는다. add로 등록하고 commit으로 DB에 확정한다.
    db.add(post)
    db.commit()

    # 303 응답: 브라우저가 지정된 주소를 GET으로 다시 요청하도록 안내한다.
    return RedirectResponse('/posts', status_code=303)


# READ ONE: 게시글 하나와 댓글 표시 =================================
# Depends(get_post_or_404)가 조회한 게시글을 post에 넣어 준다.
@app.get('/posts/{post_id}')
def post_detail(
    request: Request,
    post: Post = Depends(get_post_or_404),
    user: User | None = Depends(get_current_user),
):
    return templates.TemplateResponse(
        # 화면은 post.comments로 댓글을, post.user.username으로 작성자 이름을 읽는다.
        request=request, name='detail.html', context={'post': post, 'user': user}
    )


# UPDATE 1: 작성자에게 수정 폼 표시 ==================================
@app.get('/posts/{post_id}/edit')
def post_edit(
    request: Request,
    post: Post = Depends(get_post_or_404),
    user: User | None = Depends(get_current_user),
):
    # 로그인 사용자 정보가 없으면 로그인 화면으로 이동한다.
    if user is None:
        return RedirectResponse('/login', status_code=303)

    # 글 작성자 번호와 현재 사용자 번호가 다르면 403(권한 없음)으로 거절한다.
    if post.user_id != user.id:
        raise HTTPException(status_code=403, detail='내 글만 수정 할 수 있습니다.')

    return templates.TemplateResponse(
        request=request, name='edit.html', context={'post': post, 'user': user}
    )


# UPDATE 2: 수정한 내용 저장 =========================================
# 버튼을 숨겨도 직접 요청할 수 있으므로 서버에서도 작성자를 확인한다.
@app.post('/posts/{post_id}/update')
def post_update(
    content: str = Form(),
    post: Post = Depends(get_post_or_404),
    db: Session = Depends(get_db),
    user: User | None = Depends(get_current_user),
):
    # 로그인 사용자 정보가 없으면 로그인 화면으로 이동한다.
    if user is None:
        return RedirectResponse('/login', status_code=303)
    # 글 작성자 번호와 현재 사용자 번호가 다르면 403(권한 없음)으로 거절한다.
    if post.user_id != user.id:
        raise HTTPException(status_code=403, detail='내 글만 수정 할 수 있습니다.')

    # 조회한 객체의 내용을 바꾸고 commit하면 DB에 변경 사항이 반영된다.
    post.content = content
    db.commit()

    return RedirectResponse('/posts', status_code=303)


# DELETE: 작성자 확인 후 게시글 삭제 =================================
@app.post('/posts/{post_id}/delete')
def post_delete(
    post: Post = Depends(get_post_or_404),
    db: Session = Depends(get_db),
    user: User | None = Depends(get_current_user),
):
    # 로그인 사용자 정보가 없으면 로그인 화면으로 이동한다.
    if user is None:
        return RedirectResponse('/login', status_code=303)
    # 글 작성자 번호와 현재 사용자 번호가 다르면 403(권한 없음)으로 거절한다.
    if post.user_id != user.id:
        raise HTTPException(status_code=403, detail='내 글만 수정 할 수 있습니다.')

    # 게시글을 삭제 대상으로 지정한다. ORM 관계 설정에 따라 댓글도 함께 삭제된다.
    db.delete(post)
    db.commit()
    return RedirectResponse('/posts', status_code=303)


# COMMENT CREATE: 게시글에 댓글 등록 =================================
# 예: /posts/7/comments/create → 글 번호는 URL, 댓글 내용은 Form으로 받는다.
@app.post('/posts/{post_id}/comments/create')
def comment_create(
    content: str = Form(),
    post: Post = Depends(get_post_or_404),
    db: Session = Depends(get_db),
    user: User | None = Depends(get_current_user),
):
    # 왼쪽 post는 Comment의 관계 속성, 오른쪽 post는 조회한 Post 객체.
    # 관계를 연결하면 저장 과정에서 comment.post_id에 게시글 번호가 반영된다.
    if user is None:
        # 로그인 화면으로 이동하고, 아래 댓글 저장 코드는 실행하지 않는다.
        return RedirectResponse('/login', status_code=303)
    comment = Comment(content=content, post=post, user=user)
    db.add(comment)
    db.commit()

    # 303 응답: 브라우저가 지정된 주소를 GET으로 다시 요청하도록 안내한다.
    return RedirectResponse(f'/posts/{post.id}', status_code=303)


# COMMENT DELETE: 댓글 하나 삭제 ====================================
# 예: /posts/7/comments/21/delete → 21번 댓글 삭제 후 7번 글로 돌아간다.
# 현재 코드는 댓글 존재 여부·소속 게시글·작성자 권한 검사를 하지 않는다.
@app.post('/posts/{post_id}/comments/{comment_id}/delete')
def comment_delete(
    post_id: int, 
    comment_id: int, 
    db: Session = Depends(get_db),
    user: User | None = Depends(get_current_user)):

    # 로그인 안한사람
    if user is None:
        return RedirectResponse('/login', status_code=303)

    # 내가 쓴 댓글인지
    comment = db.get(Comment, comment_id)
    if comment.user_id != user.id:
        # 403: 권한 없음
        raise HTTPException(status_code=403, detail='내 댓글만 삭제 가능')
    db.delete(comment)
    db.commit()

    return RedirectResponse(f'/posts/{post_id}', status_code=303)


# SIGNUP 1: 회원가입 폼 표시 (GET) ===================================
@app.get('/signup')
def signup_form(request: Request, user: User | None = Depends(get_current_user)):
    return templates.TemplateResponse(
        request=request, name='signup.html', context={'user': user}
    )


# SIGNUP 2: 입력한 아이디와 비밀번호로 가입 처리 (POST) ===============
@app.post('/signup')
def signup(
    request: Request,
    username: str = Form(),
    password: str = Form(),
    db: Session = Depends(get_db),
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
@app.get('/login')
def login_form(request: Request, user: User | None = Depends(get_current_user)):
    return templates.TemplateResponse(
        request=request, name='login.html', context={'user': user}
    )


# LOGIN 2: 비밀번호 확인 → 세션 저장 → 쿠키 전달 ======================
@app.post('/login')
def login(
    request: Request,
    username: str = Form(),
    password: str = Form(),
    db: Session = Depends(get_db),
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
@app.post('/logout')
def logout(request: Request, db: Session = Depends(get_db)):
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


@app.post('/posts/{post_id}/likes')
def post_like(
    post: Post = Depends(get_post_or_404),
    db: Session = Depends(get_db),
    user: User | None = Depends(get_current_user)
):
    if user is None:
        return RedirectResponse('/login', status_code=303)

    # like가 있는지
    result = db.get(Like, (user.id ,post.id))

    if result:
        # 좋아요가 이미 눌림 -> 다시 누르면 삭제
        db.delete(result)
    else:
        # 좋아요가 아직 안눌림 -> 좋아요 추가
        like = Like(user_id=user.id, post_id=post.id)
        db.add(like)

    db.commit()

    return RedirectResponse('/posts', status_code=303)