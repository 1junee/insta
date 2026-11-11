"""Correct the user and post references on likes.

Revision ID: f82a71d640bc
Revises: e3f674110138
"""

from alembic import op

revision = 'f82a71d640bc'
down_revision = 'e3f674110138'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 테이블과 데이터는 유지하고, 잘못 연결된 외래 키 제약조건만 교체한다.
    op.drop_constraint('likes_user_id_fkey', 'likes', type_='foreignkey')
    op.drop_constraint('likes_post_id_fkey', 'likes', type_='foreignkey')
    op.create_foreign_key(
        'likes_user_id_fkey', 'likes', 'users', ['user_id'], ['id']
    )
    op.create_foreign_key(
        'likes_post_id_fkey', 'likes', 'posts', ['post_id'], ['id']
    )


def downgrade() -> None:
    # 이전 버전의 구조로 복원한다. 그 구조에 맞지 않는 데이터가 있으면 실패한다.
    op.drop_constraint('likes_user_id_fkey', 'likes', type_='foreignkey')
    op.drop_constraint('likes_post_id_fkey', 'likes', type_='foreignkey')
    op.create_foreign_key(
        'likes_user_id_fkey', 'likes', 'posts', ['user_id'], ['id']
    )
    op.create_foreign_key(
        'likes_post_id_fkey', 'likes', 'users', ['post_id'], ['id']
    )
