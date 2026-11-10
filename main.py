from fastapi import FastAPI, Request, Depends, Form, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from sqlalchemy import create_engine, select, func, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, Session, relationship
from datetime import datetime
from pwdlib import PasswordHash

DB_URL = 'postgresql+psycopg://sd4:sd4@localhost:5432/insta'
engine = create_engine(DB_URL, echo=True)

# 모델 정의
class Base(DeclarativeBase):
    pass

class Post(Base):
    __tablename__ = 'posts'

    id: Mapped[int] = mapped_column(primary_key=True)
    content: Mapped[str]
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    # created_at: Mapped[datetime]
    comments: Mapped[list['Comment']] = relationship(
        back_populates='post',
        cascade='all, delete-orphan'
    )

class Comment(Base):
    __tablename__ = 'comments'

    id: Mapped[int] = mapped_column(primary_key=True)
    content: Mapped[str]
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    post_id: Mapped[int] = mapped_column(ForeignKey('posts.id'))
    post: Mapped['Post'] = relationship(back_populates='comments')

class User(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(unique=True)
    password_hash: Mapped[str]

class UserSession():
    __tablename__ = 'sessions'

    # 신분증
    id: Mapped[str] = mapped_column()
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    # 클래스를 따옴표 안에 넣어서 어느 순서에 있든 불러올 수 있게
    # 단방향 연결
    user: Mapped['User'] = relationship()


app = FastAPI()
templates = Jinja2Templates(directory='templates')
password_to_hash = PasswordHash.recommended()

def get_db():
    with Session(engine) as db:
        yield db

def get_post_or_404(post_id: int, db: Session = Depends(get_db)):
    post = db.get(Post, post_id)

    if post is None:
        # from fastapi import HTTPException
        raise HTTPException(status_code=404, detail='해당 게시물이 없습니다.')

    return post


@app.get('/')
def home():
    return {'hi': 'hello'}


@app.get('/posts')
def post_list(request: Request, db: Session = Depends(get_db)):
    # with Session(engine) as db:

    # posts = db.scalars(select(Post)).all()
    posts = db.scalars(select(Post).order_by(Post.created_at.desc())).all()
    return templates.TemplateResponse(
        request=request,
        name='list.html',
        context={'posts': posts}
    )


@app.get('/posts/new')
def post_new(request: Request):
    return templates.TemplateResponse(
        request=request,
        name='new.html'
    )


@app.post('/posts/create')
def post_create(content: str = Form(), db: Session = Depends(get_db)):
    # db = Session(engine)
    post = Post(content=content)
    db.add(post)
    db.commit()

    # from fastapi.responses import RedirectResponse
    return RedirectResponse('/posts', status_code=303)


@app.get('/posts/{post_id}')
def post_detail(request: Request, post: Post = Depends(get_post_or_404)):
    # comments = db.scalars(select(Comment).where().order_by(Comment.created_at.desc()))
    return templates.TemplateResponse(
        request=request,
        name='detail.html',
        context={
            'post': post
        }
    )


@app.get('/posts/{post_id}/edit')
def post_edit(request: Request, post: Post = Depends(get_post_or_404)):
    return templates.TemplateResponse(
        request=request,
        name='edit.html',
        context={'post': post}
    )


@app.post('/posts/{post_id}/update')
def post_update(
    content: str = Form(),
    post: Post = Depends(get_post_or_404),
    db: Session = Depends(get_db)
):
    post.content = content
    db.commit()

    return RedirectResponse('/posts', status_code=303)


@app.post('/posts/{post_id}/delete')
def post_delete(
    post: Post = Depends(get_post_or_404),
    db: Session = Depends(get_db)
):
    db.delete(post)
    db.commit()
    return RedirectResponse('/posts', status_code=303)


@app.post('/posts/{post_id}/comments/create')
def comment_create(
    content: str = Form(),
    post: Post = Depends(get_post_or_404),
    db: Session = Depends(get_db)
):
    comment = Comment(content=content, post=post)
    db.add(comment)
    db.commit()

    return RedirectResponse(f'/posts/{post.id}', status_code=303)


@app.post('/posts/{post_id}/comments/{comment_id}/delete')
def comment_delete(post_id: int, comment_id: int, db: Session = Depends(get_db)):
    comment = db.get(Comment, comment_id)
    db.delete(comment)
    db.commit()

    return RedirectResponse(f'/posts/{post_id}', status_code=303)


# a태그를 통해 들어오는 signup
@app.get('/signup')
def signup_form(request: Request):
    return templates.TemplateResponse(
        request=request,
        name='signup.html'
    )

# form method = 'post' 방식으로 들어오는 signup
@app.post('/signup')
def signup(
    request: Request,
    username: str = Form(),
    password: str = Form(),
    db: Session = Depends(get_db)
):
    # 이미 있는 유저인지 검증
    exists = db.scalar(select(User).where(User.username == username))
    if exists:
        # return RedirectResponse('/signup', status_code=303)
        return templates.TemplateResponse(
            request=request,
            name='/signup.html',
            context={'error': '이미 있는 아이디입니다.'}
        )

    # password를 해시로 변환
    # from pwdlib import PasswordHash
    password_hash = password_to_hash.hash(password)

    user = User(username=username, password_hash=password_hash)
    db.add(user)
    db.commit()
    return RedirectResponse('/login', status_code=303)


@app.get('/login')
def login_form(request: Request):
    return templates.TemplateResponse(
        request=request,
        name='login.html'
    )

@app.post('/login')
def login():
    pass
