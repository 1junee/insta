# insta

FastAPI·SQLAlchemy·PostgreSQL로 게시글·댓글·회원가입·로그인·좋아요·팔로우를 구현한 수업 프로젝트.

## 실제 진행한 명령어 흐름

수업 때 사용한 명령어와 직접 수정한 설정을 순서대로 정리했다. 각 단계에서 코드를 작성한 뒤 다음 명령을 실행했다. 과거 명령어 기록이므로 현재 완성된 프로젝트에서 처음부터 전부 다시 실행하지 않는다.

### 1. 프로젝트 생성

```bash
uv init insta --bare --python 3.14
cd insta
```

insta 폴더에 Python 프로젝트를 만들고 이동한다.

### 2. 패키지 설치

```bash
uv add "fastapi[standard]" sqlalchemy "psycopg[binary]" alembic
```

FastAPI는 웹 요청, SQLAlchemy는 모델·DB 작업, psycopg는 PostgreSQL 연결, Alembic은 테이블 변경 이력을 담당한다.

### 3. DB 생성

터미널에서 PostgreSQL에 접속한다.

```bash
psql -d postgres
```

psql 안에서 실행한다. sd4는 앞선 DB 수업에서 만들어 둔 사용자다.

```sql
CREATE DATABASE insta OWNER sd4;
```

psql을 종료하고 터미널로 돌아온다.

```text
\q
```

### 4. DB 연결 주소·engine·Base 작성

처음에는 main.py에 작성했고, 나중에 database.py로 분리했다.

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase

DB_URL = "postgresql+psycopg://sd4:비밀번호@localhost:5432/insta"
engine = create_engine(DB_URL, echo=True)

class Base(DeclarativeBase):
    pass
```

비밀번호 자리는 sd4 계정의 실제 비밀번호로 채운다. README에는 비밀번호를 그대로 옮기지 않았다.

- postgresql+psycopg: PostgreSQL에 psycopg로 연결.
- sd4: 접속 사용자.
- localhost: 내 컴퓨터에서 실행 중인 DB.
- 5432: PostgreSQL 포트. FastAPI의 8000과 다르다.
- insta: 사용할 DB 이름.
- echo=True: 실행되는 SQL을 터미널에 표시.

### 5. Post 모델·홈·게시글 조회 작성

처음에는 같은 main.py에서 Post를 작성했다.

```python
from sqlalchemy.orm import Mapped, mapped_column

class Post(Base):
    __tablename__ = 'posts'

    id: Mapped[int] = mapped_column(primary_key=True)
    content: Mapped[str]
```

홈과 게시글 조회·템플릿 코드를 작성하고 개발 서버를 실행했다.

```bash
uv run fastapi dev main.py
```

브라우저에서 http://127.0.0.1:8000/posts 로 접속한다. 서버 종료는 Ctrl+C다. 모델 선언만으로 실제 posts 테이블이 생기지는 않으므로 조회 전에 아래 Alembic 적용이 필요하다.

### 6. Alembic 초기화

```bash
uv run alembic init alembic
```

alembic.ini, alembic/env.py, alembic/versions가 만들어진다.

### 7. alembic/env.py 설정

처음 main.py에 모델과 DB 설정이 있을 때는 다음 내용을 연결했다. env.py 전체를 교체하는 것이 아니라 해당 설정만 수정한다.

```python
from main import DB_URL, Base

# 기존 config = context.config 아래에 추가
config.set_main_option('sqlalchemy.url', DB_URL)

# 기존 target_metadata = None을 교체
target_metadata = Base.metadata
```

DB_URL을 사용하는 줄보다 import가 위에 있어야 한다. DB_URL은 실제 접속할 DB, Base.metadata는 비교할 테이블 구조다.

### 8. posts 테이블 생성·적용

```bash
uv run alembic revision --autogenerate -m "create posts"
uv run alembic upgrade head
```

revision은 변경 파일 생성, upgrade는 DB 적용이다. 생성된 파일의 upgrade()를 확인한 뒤 적용한다.

적용 상태와 변경 이력은 다음 명령으로 확인했다.

```bash
uv run alembic current
uv run alembic history
```

### 9. 게시글 CRUD·댓글 구현

게시글 목록·작성·상세·수정·삭제와 템플릿을 작성했다. get_db의 yield·Depends, get_post_or_404로 세션과 게시글 조회를 공통 처리했다. 이후 작성 시간과 댓글 모델·관계를 추가했다.

라우트·HTML만 수정할 때는 revision이 필요하지 않다. 모델의 테이블 구조가 바뀔 때 변경 파일을 생성·검토·적용했다. 댓글 최초 생성 명령의 정확한 메시지는 확인한 기록에 없어 임의로 추가하지 않았다.

### 10. 비밀번호 해시·회원가입

```bash
uv add "pwdlib[argon2]"
```

비밀번호 해시와 검증에 사용할 패키지를 설치했다. User 모델을 작성한 뒤 실행했다.

```bash
uv run alembic revision --autogenerate -m "create users"
uv run alembic upgrade head
```

### 11. 로그인 세션

UserSession 모델을 작성한 뒤 실행했다.

```bash
uv run alembic revision --autogenerate -m "create sessions"
uv run alembic upgrade head
```

로그인 시 세션을 저장하고 쿠키로 세션 ID를 전달하도록 구현했다.

### 12. 댓글 작성자 연결

Comment에 user_id와 User 관계를 추가한 뒤 실행했다.

```bash
uv run alembic revision --autogenerate -m "create Comment_User Relation"
uv run alembic upgrade head
```

기존 댓글에 user_id가 없으면 필수 컬럼 적용 과정에서 문제가 생길 수 있다. 당시 revision 생성 성공과 실제 upgrade 성공을 혼동했다. 생성 파일을 검토하고 기존 데이터 처리 여부를 먼저 확인해야 한다.

사용자와 DB 상태를 확인할 때 사용한 명령:

```bash
psql -U sd4 -d insta
```

또는 터미널에서 쿼리 한 번만 실행했다.

```bash
psql -h localhost -U sd4 -d insta -c "SELECT id, username FROM users ORDER BY id;"
```

### 13. 좋아요

Like 모델을 작성한 뒤 실행했다.

```bash
uv run alembic revision --autogenerate -m "create likes"
uv run alembic upgrade head
```

user_id·post_id를 복합 기본 키로 사용했다. post_id가 users.id를 참조하던 문제를 posts.id로 바로잡고 추가 마이그레이션으로 수정했다. 로그인·작성자 검사와 cascade 삭제 처리도 함께 학습했다.

### 14. Annotated·라우터 분리

코드를 다음 파일로 분리했다. 파일을 나누는 작업 자체에는 새로운 터미널 명령이나 revision이 필요하지 않다.

| 파일 | 역할 |
| --- | --- |
| database.py | DB_URL, engine, Base |
| models.py | Post, Comment, User, UserSession, Like, Follow |
| deps.py | SessionDep, PostDep, CurrentUserDep, templates |
| routers/posts.py | 게시글·댓글·좋아요 |
| routers/auth.py | 회원가입·로그인·로그아웃 |
| routers/users.py | 프로필·팔로우 |
| main.py | FastAPI 앱 생성·include_router 등록 |

파일 분리 후 env.py의 import를 바꿨다.

```python
from database import Base, DB_URL
import models

target_metadata = Base.metadata
config.set_main_option('sqlalchemy.url', DB_URL)
```

models를 import해야 테이블 정보가 Base.metadata에 등록된다. deps.py에서는 `Jinja2Templates(directory='templates')`를 사용하므로 프로젝트 루트에서 서버를 실행한다.

### 15. 프로필·팔로우

Follow 모델을 작성한 뒤 실행한 revision 명령:

```bash
uv run alembic revision --autogenerate -m "create follows"
```

이 과정에서 `Target database is not up to date` 오류를 확인했다. 새 변경 파일을 만들기 전에 기존 변경이 DB에 적용됐는지 확인해야 한다.

follower_id는 팔로우하는 사람, following_id는 팔로우받는 사람이다. 이후 팔로워·팔로잉 ID 조회 방향과 버튼 표시를 수정했다.

### 16. 현재 남아 있는 최종 마이그레이션

이력을 정리하는 과정에서 사용한 명령:

```bash
uv run alembic revision --autogenerate -m "create tables"
uv run alembic upgrade head
uv run alembic current
```

현재 저장소에는 `98e20e4f5a71_create_tables.py` 하나가 남아 있다. users, follows, posts, sessions, comments, likes 테이블을 생성한다. 위의 단계별 명령은 과거 학습 흐름이며 현재 DB에서 다시 순서대로 실행할 명령이 아니다.

## 이후 다시 실행할 때

패키지가 준비된 현재 프로젝트에서는 다음 명령으로 서버를 실행한다.

```bash
uv run fastapi dev main.py
```

기존 저장소의 패키지를 다시 설치할 때 사용한 명령:

```bash
uv sync --locked
```

새 migration을 내려받은 경우 적용 상태를 확인하고 적용한다.

```bash
uv run alembic current
uv run alembic upgrade head
```

## Git 저장·푸시

기능 한 덩어리가 끝나면 변경 내용을 확인하고 저장한다. 아래 커밋 메시지는 실제 README 정리에 사용한 메시지다.

```bash
git status
git diff
git add README.md
git commit -m "처음부터 최종 기능까지 명령어 흐름을 다시 따라갈 수 있게 한다" \
  -m "Tested: 현재 모델·라우터·마이그레이션 파일과 문서 대조, git diff --check 통과" \
  -m "Scope-risk: narrow"
git push origin main
```

기능 전체를 기록할 때는 변경 파일을 검토한 뒤 `git add .`을 사용하고 해당 변경에 맞는 커밋 메시지를 작성한다. 현재 원격은 `https://github.com/1junee/insta.git`, 브랜치는 main이다. 이미 연결되어 있으므로 remote add를 반복하지 않는다.
