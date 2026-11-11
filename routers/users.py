# 프로필 관련
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import RedirectResponse
from deps import templates ,SessionDep, CurrentUserDep
from sqlalchemy import select
from models import User, Post, Follow

router = APIRouter()

@router.get('/users/{username}')
def profile(
    request: Request,
    username: str, # 보고 있는 프로필의 사용자 이름
    db: SessionDep,
    user: CurrentUserDep,  # 현재 로그인한 사용자, 비로그인이면 None
):
    # owner는 프로필 주인이다. 현재 로그인한 user와는 다른 사람일 수 있다.
    owner = db.scalar( select(User).where(User.username == username) )
    if owner is None:
        raise HTTPException(status_code=404, detail='해당 사용자가 없습니다.')

    # 그 유저의 게시물
    posts = db.scalars( select(Post).where(Post.user_id == owner.id).order_by(Post.created_at.desc()) ).all()

    # 팔로워: 다른 사람 → 프로필 주인. 받는 쪽(following_id)이 owner인 관계들.
    # User 목록이 아니라 Follow id 행 목록이며, 화면에서 length로 인원수를 센다.
    follower_list = db.scalars( select(Follow.follower_id).where(Follow.following_id == owner.id) ).all()

    # 팔로잉: 프로필 주인 → 다른 사람. 보내는 쪽(follower_id)이 owner인 관계들.
    following_list = db.scalars( select(Follow.following_id).where(Follow.follower_id == owner.id) ).all()

    return templates.TemplateResponse(
        request=request,
        name='profile.html',
        context={
            'owner': owner,
            'posts': posts,
            'user': user,
            'follower_list': follower_list,
            'following_list': following_list,
        }
    )

@router.post('/users/{username}/follows')
def user_follow(
    username: str, # 팔로우 또는 취소할 대상의 사용자 이름 (owner)
    db: SessionDep,
    user: CurrentUserDep # 버튼을 누른 로그인 사용자, 비로그인이면 None
):
    # 비로그인 유저는 로그인 페이지로
    if user is None:
        return RedirectResponse('/login', status_code=303)

    owner = db.scalar(  select(User).where(User.username == username)  )

    # 현재 user → owner 방향의 관계가 있는지 복합 기본 키로 조회한다.
    follow = db.get(Follow, (user.id, owner.id))  # 키 순서: (follower_id, following_id)

    # 같은 방향의 관계가 이미 있으면 해당 행을 삭제해 팔로우를 취소한다.
    if follow:
        db.delete(follow)
    # 관계가 없으면 user → owner 행을 추가한다. 반대 방향은 자동 생성하지 않는다.
    else:
        follow = Follow(
            follower_id=user.id, # 보내는 사람: 현재 로그인 사용자
            following_id=owner.id  # 받는 사람: 대상 프로필 주인
        )
        db.add(follow)
    
    db.commit()

    return RedirectResponse(f'/users/{username}', status_code=303)

