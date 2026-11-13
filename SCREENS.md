# 화면 약속

`.py`(직접 치는 코드)와 `templates/`(Claude와 꾸미는 화면)가 만나는 자리.
아래 이름은 바꾸지 않는다. 페이지를 꾸미기 전에 그 페이지 칸을 먼저 적는다.

## 모든 화면이 받는 변수

- `user` — 지금 로그인한 사용자. 로그인 안 했으면 `None`
- 로그인했는지는 `{% if user %}`로 나눈다

## 사용자 칸 (`user` · `post.user` · `owner`)

| 칸 | 타입 | 화면에서 |
| --- | --- | --- |
| `id` | int | 내 글인지 · 내 프로필인지 확인 |
| `username` | str | 이름 · 프로필 링크 `/users/{{ ….username }}` |
| `avatar_url` | str 또는 `None` | 프로필 사진 `<img src="{{ ….avatar_url }}">`. 안 올렸으면 `None` → `{% if ….avatar_url %}`로 나눠 기본 프로필(회색 동그라미 + 사람 모양)을 보인다 |
| `followers` | 팔로우 목록 | 팔로워 수(`length` 필터). 사용자 목록이 아니라 `Follow` 행 목록 |
| `followings` | 팔로우 목록 | 팔로잉 수(`length` 필터). 사용자 목록이 아니라 `Follow` 행 목록 |

## 게시물 칸 (`post`)

| 칸 | 타입 | 화면에서 |
| --- | --- | --- |
| `id` | int | 주소(`/posts/{{ post.id }}`) |
| `content` | str | 본문 |
| `image_url` | str 또는 `None` | 사진 `<img src="{{ post.image_url }}">`. 사진 없는 옛 글이 있어서 `{% if post.image_url %}` 안에 둔다 |
| `created_at` | datetime | `{{ post.created_at.strftime('%Y-%m-%d %H:%M') }}` |
| `user` | 사용자 | 글쓴이 이름 `{{ post.user.username }}` · 프로필 사진 `{{ post.user.avatar_url }}` · 프로필 링크 `/users/{{ post.user.username }}` |
| `user_id` | int | 내 글인지 확인(`user.id == post.user_id`) |
| `comments` | 댓글 목록 | 댓글 수(`length` 필터) · 상세의 댓글 목록 |
| `likes` | 좋아요 목록 | 좋아요 수(`length` 필터) |

## 댓글 칸 (`comment`)

| 칸 | 타입 | 화면에서 |
| --- | --- | --- |
| `id` | int | 삭제 주소 |
| `content` | str | 댓글 내용 |
| `created_at` | datetime | 단 시각 |
| `user` | 사용자 | 댓글 쓴 사람 이름 · 프로필 사진 · 프로필 링크 |
| `user_id` | int | 내 댓글인지 확인(`user.id == comment.user_id`) |

## 다른 사람 프로필로 가는 길

프로필 주소는 하나: `/users/{{ ….username }}`

- 내 프로필 — 왼쪽 메뉴의 내 프로필 사진(`user.avatar_url`, 없으면 기본 프로필)
- 다른 사람 프로필 — 게시물의 글쓴이 프로필 사진 · 이름(`post.user`)
- 다른 사람 프로필 — 팔로워 · 팔로잉 목록의 사람 (**아직 없음**. 목록 페이지가 생기면 여기에 적는다)

## 페이지

### 공통 틀

- 템플릿: `base.html` — 다른 템플릿이 `{% extends 'base.html' %}`로 쓴다
- 블록: `title` · `content`
- 메뉴 위치: 왼쪽 세로 메뉴 (화면이 좁으면 아래쪽 가로 막대)
- 메뉴 — 로그인했을 때: `/posts` · `/posts/new` · 내 프로필 `/users/{{ user.username }}`(내 프로필 사진으로 보인다) · 이름 · 로그아웃 폼(`method="post"` `action="/logout"`, 칸 없음)
- 메뉴 — 로그인 안 했을 때: `/posts` · `/signup` · `/login`
- CSS: `/static/style.css`(Bootstrap CSS 줄 아래)

### 전체 글

- 주소: `GET /posts`
- 템플릿: `list.html`
- 받는 변수: `posts` — 게시물 목록(새 글이 위) · `liked_ids` — 내가 좋아요한 게시물 번호 목록(로그인 안 했으면 빈 목록)
- 글마다: 사진 · 본문 · 글쓴이(프로필 사진 · 이름, 프로필 링크) · 댓글 수 · 좋아요 수 · 올린 시각 · 상세 링크
- 좋아요 폼(글마다): `method="post"` `action="/posts/{{ post.id }}/likes"` — 칸 없음. 버튼 글자는 `{% if post.id in liked_ids %}`로 나눈다
- 링크: 게시물마다 `/posts/{{ post.id }}` · 글쓴이 `/users/{{ post.user.username }}`
- 게시물마다 `id="post-{{ post.id }}"` — 좋아요를 누른 뒤 `/posts#post-{번호}`로 돌아오면 그 글 위치로 스크롤된다

### 프로필

- 주소: `GET /users/{username}`
- 템플릿: `profile.html`
- 받는 변수: `owner` — 프로필 주인 · `posts` — 주인의 게시물 목록(새 글이 위) · `follow` — 내가 주인을 팔로우하고 있으면 값, 아니면 `None` · `user`
- 내 프로필인지는 `user.id == owner.id`로 나눈다
- 위쪽: 주인 프로필 사진(`owner.avatar_url`, 없으면 기본 프로필) · `owner.username` · 게시물 수(`posts | length`) · 팔로워 수(`owner.followers | length`) · 팔로잉 수(`owner.followings | length`)
- 팔로우 폼(남의 프로필): `method="post"` `action="/users/{{ owner.username }}/follows"` — 칸 없음. 버튼 글자는 `{% if follow %}`로 나눈다
- 프로필 사진 올리기 폼(내 프로필, 사진 없을 때): `method="post"` `action="/users/{{ user.username }}/avatar"` `enctype="multipart/form-data"` — 칸 `name="photo"`(`type="file"`)
- 프로필 사진 삭제 폼(내 프로필, 사진 있을 때): `method="post"` `action="/users/{{ owner.username }}/avatar/delete"` — 칸 없음
- 아래쪽 격자: 게시물마다 사진 · 좋아요 수 · 댓글 수, 링크 `/posts/{{ post.id }}`

### 새 글

- 주소: `GET /posts/new` (로그인 안 했으면 `/login`으로 감)
- 템플릿: `new.html`
- 받는 변수: `user`
- 폼: `method="post"` `action="/posts/create"` `enctype="multipart/form-data"`
  - 칸 `name="content"` — `textarea`, `required`
  - 칸 `name="photo"` — `type="file"`, `required` (`post_create`가 사진을 꼭 받는다)

### 상세

- 주소: `GET /posts/{post_id}`
- 템플릿: `detail.html`
- 받는 변수: `post` · `user` (`liked_ids`는 받지 않는다 → 좋아요는 수만 보인다)
- 내 글일 때(`user and user.id == post.user_id`)
  - 수정 링크 `/posts/{{ post.id }}/edit`
  - 삭제 폼: `method="post"` `action="/posts/{{ post.id }}/delete"` — 칸 없음
- 댓글 쓰기 폼(로그인했을 때): `method="post"` `action="/posts/{{ post.id }}/comments/create"` — 칸 `name="content"`
- 댓글 목록: `post.comments | sort(attribute='created_at', reverse=True)` (새 댓글이 위)
- 댓글 삭제 폼(내 댓글일 때): `method="post"` `action="/posts/{{ post.id }}/comments/{{ comment.id }}/delete"` — 칸 없음

### 수정

- 주소: `GET /posts/{post_id}/edit` (로그인 안 했으면 `/login`, 남의 글이면 403)
- 템플릿: `edit.html`
- 받는 변수: `post` · `user`
- 폼: `method="post"` `action="/posts/{{ post.id }}/update"`
  - 칸 `name="content"` — `textarea`, `required`. 원래 내용 `{{post.content}}`은 태그 사이에 붙여 쓴다
- 사진은 바꿀 수 없다 (보여 주기만)
- 링크: 취소 `/posts/{{ post.id }}`

### 로그인

- 주소: `GET /login` · 보내기 `POST /login` (성공하면 `/posts`)
- 템플릿: `login.html`
- 받는 변수: `user` · `error` — 실패했을 때만 들어온다. 이때는 `user`를 받지 않는다
- 폼: `method="post"` `action="/login"`
  - 칸 `name="username"` — `type="text"`, `required`
  - 칸 `name="password"` — `type="password"`, `required`
- 링크: 가입 `/signup`

### 회원가입

- 주소: `GET /signup` · 보내기 `POST /signup` (성공하면 `/login`)
- 템플릿: `signup.html`
- 받는 변수: `user` · `error` — 이미 있는 아이디일 때만 들어온다. 이때는 `user`를 받지 않는다
- 폼: `method="post"` `action="/signup"`
  - 칸 `name="username"` — `type="text"`, `required`
  - 칸 `name="password"` — `type="password"`, `required`
- 링크: 로그인 `/login`
