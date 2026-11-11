# insta

FastAPI·SQLAlchemy·PostgreSQL로 게시글, 댓글, 회원가입·로그인, 좋아요, 팔로우를 구현한 수업 프로젝트.

## 처음부터 구현한 명령어 흐름

새 프로젝트를 만드는 학습 순서다. 이미 이 저장소를 내려받았다면 아래의 **기존 프로젝트 실행**만 따라 한다. 단계별 revision 메시지는 설명용이며, 현재 저장소에는 최종 테이블을 생성하는 `98e20e4f5a71_create_tables.py` 하나가 남아 있다.

### 1. 프로젝트 생성

```bash
uv init insta --bare --python 3.14
cd insta
```

Python 3.14를 사용하는 최소 프로젝트를 만들고 폴더로 이동한다.

### 2. 패키지 설치

```bash
uv add "fastapi[standard]" sqlalchemy "psycopg[binary]" alembic
```

FastAPI는 웹 요청 처리, SQLAlchemy는 모델·DB 작업, psycopg는 PostgreSQL 통신, Alembic은 테이블 변경 이력을 담당한다.

### 3. DB 생성

터미널에서 기본 DB에 접속한다. 기존 PostgreSQL 사용자 sd4가 준비되어 있다는 전제다.

```bash
psql -d postgres
```

psql 안에서 실행한다.

```sql
CREATE DATABASE insta OWNER sd4;
```

psql을 종료한다.

```text
\q
```

### 4. 홈·DB 연결·Post 모델 작성

main.py에 FastAPI 앱, 홈 라우트, engine, Base, Post 모델을 작성한다. PostgreSQL 연결 포트는 5432이며 FastAPI 개발 서버 포트 8000과 구분한다.

```bash
uv run fastapi dev main.py
```

브라우저에서 http://127.0.0.1:8000/ 에 접속한다. 서버를 끄려면 Ctrl+C를 누른다. 서버가 실행 중이면 다른 명령은 새 터미널에서 실행한다.

### 5. Alembic 초기화 및 설정

```bash
uv run alembic init alembic
```

alembic.ini, alembic/env.py, alembic/versions가 만들어진다. env.py에 DB 접속 주소와 모델 구조를 연결한 뒤 다음 단계로 진행한다.

처음에는 main.py에서 DB_URL·Base를 가져왔다. 파일 분리 후 현재 코드는 다음과 같다.

```python
from database import Base, DB_URL
import models

target_metadata = Base.metadata
config.set_main_option('sqlalchemy.url', DB_URL)
```

기존 `config = context.config` 다음에 설정하며, DB_URL을 사용하기 전에 import한다. models를 import해야 모델들이 Base.metadata에 등록된다.

### 6. posts 테이블 생성

```bash
uv run alembic revision --autogenerate -m "create posts"
```

모델과 실제 DB를 비교해 변경 파일을 만든다. 생성된 upgrade()의 내용을 확인한 뒤 적용한다.

```bash
uv run alembic upgrade head
uv run alembic current
```

revision은 파일 생성, upgrade는 실제 DB 적용이다. Post 클래스만 선언해서는 테이블이 생성되지 않는다.

### 7. 게시글 CRUD·템플릿·의존성 작성

목록·작성·상세·수정·삭제와 Jinja2 템플릿을 작성한다. get_db의 yield·Depends로 세션을 전달하고 get_post_or_404로 게시글 조회를 공통 처리한다. 라우트·HTML만 변경했다면 migration은 필요하지 않다.

```bash
uv run fastapi dev main.py
```

/posts에서 화면을 확인한다. 이미 개발 서버가 실행 중이면 저장 후 재접속한다.

### 8. 작성 시간·댓글 모델 추가

Post 작성 시간과 Comment 모델, 게시글과의 외래 키·relationship을 작성한 다음 변경 파일을 생성·검토·적용한다.

```bash
uv run alembic revision --autogenerate -m "add post timestamp and comments"
uv run alembic upgrade head
```

댓글 등록·표시·삭제를 구현한다. 위 메시지는 학습 흐름을 보여주는 예시이며 현재 남아 있는 개별 revision 이름은 아니다.

### 9. 회원가입·로그인·세션

```bash
uv add "pwdlib[argon2]"
```

비밀번호 해시·검증 도구를 설치한다. User 모델과 회원가입을 작성하고, 이어서 UserSession 모델과 로그인·로그아웃을 작성한다. 각각 모델 변경 후 같은 순서로 진행한다.

```bash
uv run alembic revision --autogenerate -m "create users"
uv run alembic upgrade head
uv run alembic revision --autogenerate -m "create sessions"
uv run alembic upgrade head
```

위 명령은 각각의 모델을 추가하는 시점에 실행하는 예시다. 최종 모델이 모두 작성된 상태에서 그대로 연속 실행하는 목록은 아니다.

### 10. 게시글·댓글 작성자 연결과 권한 검사

user_id 외래 키를 추가한 뒤 변경 파일을 검토·적용한다.

```bash
uv run alembic revision --autogenerate -m "add post and comment authors"
uv run alembic upgrade head
```

기존 행이 있다면 필수 user_id를 넣을 방법부터 정해야 한다. 기존 데이터 처리 없이 NOT NULL 컬럼을 추가하면 실패할 수 있다. 화면의 버튼 표시와 서버의 로그인·작성자 검사는 각각 구현한다.

### 11. 좋아요

Like 모델에 user_id·post_id 복합 기본 키를 작성한다. post_id는 users.id가 아니라 posts.id를 참조한다.

```bash
uv run alembic revision --autogenerate -m "create likes"
uv run alembic upgrade head
```

이미 잘못된 외래 키가 DB에 적용됐다면 모델을 바로잡은 뒤 추가 migration을 생성·검토·적용한다.

```bash
uv run alembic revision --autogenerate -m "fix likes foreign keys"
uv run alembic upgrade head
```

### 12. Annotated·라우터 분리

DB 연결은 database.py, 모델은 models.py, 공통 의존성은 deps.py, 기능별 라우트는 routers/posts.py·auth.py·users.py로 분리한다. main.py는 앱 생성과 라우터 등록을 담당한다. 파일 분리 자체로는 DB 구조가 바뀌지 않으므로 revision이 필요하지 않다.

### 13. 프로필·팔로우

프로필 화면과 Follow 모델을 작성한다. follower_id는 팔로우하는 사람, following_id는 팔로우받는 사람이다.

```bash
uv run alembic revision --autogenerate -m "create follows"
uv run alembic upgrade head
```

팔로워·팔로잉 조회 방향과 버튼 상태를 확인한다. 조회 코드나 템플릿만 수정할 때는 migration이 필요하지 않다.

## 현재 저장소의 마이그레이션 상태

현재 파일 기준 head는 `98e20e4f5a71`이며 users, follows, posts, sessions, comments, likes 테이블을 생성한다. 과거 단계별 마이그레이션과 기존 README의 `a41b82c93d04`, legacy_user_id 명령은 현재 파일 구성에 해당하지 않는다.

```bash
uv run alembic current
uv run alembic heads
uv run alembic history
```

각각 DB의 현재 적용 위치, 파일 기준 최신 리비전, 변경 이력을 확인한다. `Target database is not up to date`가 나오면 적용 상태와 변경 파일을 확인한 뒤 기존 migration부터 적용한다.

```bash
uv run alembic downgrade -1
```

직전 migration을 되돌리는 명령이다. 현재는 최초 테이블 생성 migration 하나이므로 이 명령은 테이블과 데이터를 삭제한다. 일반 실행 과정에 포함하지 않는다.

## 기존 프로젝트 실행

이 저장소를 이미 내려받았다면 init·revision을 다시 실행하지 않는다. 패키지를 설치하고 database.py의 DB 연결 설정과 DB 존재 여부를 확인한다.

```bash
uv sync --locked
uv run alembic current
uv run alembic heads
uv run alembic upgrade head
uv run fastapi dev main.py
```

현재 migration과 호환되는 DB를 대상으로 한다. 삭제된 과거 revision을 참조하는 DB라면 바로 재생성하거나 stamp하지 말고 이력 불일치를 먼저 확인한다.

## Git 기록·푸시

기능 한 덩어리가 끝나면 변경을 검토하고 기록한다. .env와 가상환경을 제외하고, 코드에 비밀번호가 직접 들어 있지 않은지도 확인한다.

```bash
git status
git diff
git add .
git commit -m "이번 변경이 필요한 이유" -m "Tested: 실제 확인한 내용"
git push origin main
```

현재 원격은 `https://github.com/1junee/insta.git`, 브랜치는 main이다. 이미 연결되어 있으므로 git init이나 remote add를 다시 실행하지 않는다. 에이전트가 푸시할 때는 전역 규칙에 따라 변경 내용과 원격/브랜치를 제시하고 확인받는다.
