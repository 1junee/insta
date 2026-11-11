from sqlalchemy import func, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column,relationship
from datetime import datetime
from database import Base

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