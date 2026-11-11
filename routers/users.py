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
    username: str,
    db: SessionDep,
    user: CurrentUserDep,
):
    # 보려고 하는 프로필의 유저정보
    owner = db.scalar( select(User).where(User.username == username) )
    if owner is None:
        raise HTTPException(status_code=404, detail='해당 사용자가 없습니다.')

    # 그 유저의 게시물
    posts = db.scalars( select(Post).where(Post.user_id == owner.id).order_by(Post.created_at.desc()) ).all()

    # 해당 프로필의 팔로워가 몇명인지
    follower_list = db.scalars( select(Follow).where(Follow.follower_id == owner.id) ).all()

    # 해당 프로필의 팔로잉이 몇명인지
    following_list = db.scalars( select(Follow).where(Follow.following_id == owner.id) ).all()

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
    username: str, # 프로필 유저 (owner)
    db: SessionDep,
    user: CurrentUserDep # 로그인 유저 (user)
):
    # 비로그인 유저는 로그인 페이지로
    if user is None:
        return RedirectResponse('/login', status_code=303)

    owner = db.scalar(  select(User).where(User.username == username)  )

    # 팔로우했는지 조회
    follow = db.get(Follow, (user.id, owner.id))  # 로그인한 사람이 -> 프로필 유저 팔로우 했으면

    # 팔로우가 되어있으면 취소
    if follow:
        db.delete(follow)
    # 팔로우가 안되어있으면 팔로우 생성
    else:
        follow = Follow(follower_id=user.id, following_id=owner.id)
        db.add(follow)
    
    db.commit()

    return RedirectResponse(f'/users/{username}', status_code=303)

