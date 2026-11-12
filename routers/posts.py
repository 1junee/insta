# 설치한 모듈 들
from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy import select

# 우리가 만든 파일
from models import Post, Comment, Like
from deps import SessionDep, PostDep, CurrentUserDep, templates

# app = FastAPI()
router = APIRouter()


# READ ALL: 전체 게시글 조회
@router.get('/posts')
def post_list(
    request: Request,
    db: SessionDep,
    user: CurrentUserDep,
):
    # 로그인한 사용자가 좋아요를 누른 게시글 번호들
    liked_ids = []

    if user:
        # liked_ids = db.scalars(
        #     select(Like.post_id).where(Like.user_id == user.id)
        # ).all()

        # User(Base) 에 likes를 relations로 추가함
        # user.likes => selec(Like) where(user.id == Like.user_id)
        liked_ids = [like.post_id for like in user.likes]

    # 최근 작성한 게시글부터 조회
    posts = db.scalars(
        select(Post).order_by(Post.created_at.desc())
    ).all()

    # 목록 화면에 게시글, 로그인 사용자, 좋아요 정보를 전달
    return templates.TemplateResponse(
        request=request,
        name='list.html',
        context={
            'posts': posts,
            'user': user,
            'liked_ids': liked_ids,
        },
    )


# CREATE 1: 글 작성 폼 표시 (GET) ====================================
@router.get('/posts/new')
def post_new(
    request: Request, 
    user: CurrentUserDep
):
    # 로그인 사용자 정보가 없으면 로그인 화면으로 이동한다.
    if user is None:
        return RedirectResponse('/login', status_code=303)

    return templates.TemplateResponse(
        request=request, name='new.html', context={'user': user}
    )


# CREATE 2: 입력한 글 저장 (POST) ====================================
# Form()은 HTML의 name="content"로 보낸 입력값을 받는다.
@router.post('/posts/create')
def post_create(
    db: SessionDep,
    user: CurrentUserDep,
    content: str = Form(),
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
@router.get('/posts/{post_id}')
def post_detail(
    request: Request,
    post: PostDep,
    user: CurrentUserDep,
):
    return templates.TemplateResponse(
        # 화면은 post.comments로 댓글을, post.user.username으로 작성자 이름을 읽는다.
        request=request, name='detail.html', context={'post': post, 'user': user}
    )


# UPDATE 1: 작성자에게 수정 폼 표시 ==================================
@router.get('/posts/{post_id}/edit')
def post_edit(
    request: Request,
    post: PostDep,
    user: CurrentUserDep,
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
@router.post('/posts/{post_id}/update')
def post_update(
    post: PostDep,
    db: SessionDep,
    user: CurrentUserDep,
    content: str = Form(),
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
@router.post('/posts/{post_id}/delete')
def post_delete(
    post: PostDep,
    db: SessionDep,
    user: CurrentUserDep,
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
@router.post('/posts/{post_id}/comments/create')
def comment_create(
    post: PostDep,
    db: SessionDep,
    user: CurrentUserDep,
    content: str = Form(),
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
@router.post('/posts/{post_id}/comments/{comment_id}/delete')
def comment_delete(
    post_id: int, 
    comment_id: int, 
    db: SessionDep,
    user: CurrentUserDep):

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


@router.post('/posts/{post_id}/likes')
def post_like(
    post: PostDep,
    db: SessionDep,
    user: CurrentUserDep
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