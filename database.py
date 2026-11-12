# DB 접근과 관련된 코드
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase


# DB 연결 설정: engine은 연결을 관리하고 echo=True는 실행 SQL을 출력한다.
DB_URL = 'postgresql+psycopg://sd4:sd4@localhost:5432/insta'
# engine = create_engine(DB_URL, echo=True)
engine = create_engine(DB_URL)

# MODEL: DB에 저장할 데이터 구조 =====================================
# 모델 클래스는 테이블에, 객체 하나는 행 하나에 대응한다.
# Mapped[...]는 값의 타입, mapped_column은 DB 열의 설정이다.
class Base(DeclarativeBase):
    pass