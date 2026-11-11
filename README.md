# insta PJT

## 강사 코드 반영 후 실행 (2026-11-11)

앱과 템플릿은 `insta-tutor` 기준이다. 이 프로젝트의 기존 Alembic 이력은
유지하고 `a41b82c93d04`에서 세션 테이블 생성과 게시글 작성자 연결을 추가한다.
기존 `create_sessions` 마이그레이션은 비어 있으므로 새 마이그레이션이 보완한다.

```sh
cd "/Users/heowonjun/Library/Mobile Documents/com~apple~CloudDocs/Documents/SD4/insta"
uv sync --locked
uv run alembic current
psql -h localhost -U sd4 -d insta -c "SELECT id, username FROM users ORDER BY id;"
```

기존 글에 지정할 작성자의 ID를 위 조회 결과에서 고른다. 아래 명령은 입력한
사용자를 기존 게시글 전체의 작성자로 지정한다. 계정을 임의로 선택하거나
기존 글을 삭제하지 않는다. 현재 확인한 기존 게시글은 1개다.

```sh
printf '기존 글의 작성자 ID: '
read -r legacy_user_id
uv run alembic -x "legacy_user_id=$legacy_user_id" upgrade head
uv run alembic current
uv run fastapi dev main.py
```

`current`가 `a41b82c93d04 (head)`인지 확인하고 서버를 실행한다.
브라우저에서 http://127.0.0.1:8000/posts 에 접속한다. 서버 종료는 Ctrl+C.
기존 글이 없는 새 DB에서는 `uv run alembic upgrade head`만으로 적용할 수 있다.
이미 적용했다면 다시 작성자를 지정할 필요가 없다.
이번 업데이트에는 마이그레이션 파일이 포함되어 있으므로 `alembic init`이나
`revision --autogenerate`를 다시 실행하지 않는다.

## Git 저장 및 푸시

현재 브랜치는 `main`, 원격은 `origin` (`https://github.com/1junee/insta.git`)이다.
아래 명령은 사용자가 직접 실행할 때의 순서이며 자동 커밋·푸시는 하지 않았다.

```sh
git status
git diff --stat
git add main.py templates uv.lock README.md alembic/versions/a41b82c93d04_complete_auth.py
git commit -m "수업의 인증과 작성자 권한 흐름을 이어서 학습할 수 있게 한다" -m "Constraint: 기존 Alembic 이력과 학습 데이터를 보존한다" -m "Tested: 격리 DB의 인증·게시글·댓글 흐름 및 PostgreSQL 마이그레이션 검증" -m "Scope-risk: moderate"
git push origin main
```

에이전트에게 푸시를 맡길 경우에는 변경 내용과 대상 브랜치를 확인한 후
명시적으로 승인해야 한다.

- 프로젝트 세팅
```
uv init insta --bare --python 3.14
```

- 필요한 라이브러리 설치
```
uv add "fastapi[standard]" sqlalchemy "psycopg[binary]" alembic
```

- 데이터 베이스 생성
```
psql -d postgres # macOS
psql -U postgres # window

CREATE DATABASE insta OWNER sd4;
```

- alembic init
```
uv run alembic init alembic
```

- alembic revision
```
uv run alembic revision --autogenerate -m "create posts"
```

- alembic upgrade
```
uv run alembic upgrade head
```

- alembic downgrade
```
uv run alembic downgrade -1
```

- alembic history
```
uv run alembic history
```

## 암호화
- pwdlib 설치
```
uv add "pwdlib[argon2]"
```
