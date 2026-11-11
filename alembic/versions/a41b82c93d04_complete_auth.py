"""Create login sessions and associate posts with their authors.

Revision ID: a41b82c93d04
Revises: 8579f294ad0f
"""

from alembic import context, op
import sqlalchemy as sa

revision = 'a41b82c93d04'
down_revision = '8579f294ad0f'
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    owner_id = None
    if bind.execute(sa.text('SELECT EXISTS (SELECT 1 FROM posts)')).scalar():
        value = context.get_x_argument(as_dictionary=True).get('legacy_user_id')
        if value is None:
            raise RuntimeError(
                'Existing posts need an author. Run: '
                'uv run alembic -x legacy_user_id=USER_ID upgrade head'
            )
        owner_id = int(value)
        if bind.execute(
            sa.text('SELECT id FROM users WHERE id = :id'), {'id': owner_id}
        ).scalar() is None:
            raise RuntimeError('legacy_user_id must identify an existing user.')

    # The preceding create_sessions revision was empty; keep its history intact.
    op.create_table(
        'sessions',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.add_column('posts', sa.Column('user_id', sa.Integer(), nullable=True))
    if owner_id is not None:
        bind.execute(sa.text('UPDATE posts SET user_id = :id'), {'id': owner_id})
    op.alter_column('posts', 'user_id', nullable=False)
    op.create_foreign_key('posts_user_id_fkey', 'posts', 'users', ['user_id'], ['id'])


def downgrade() -> None:
    op.drop_constraint('posts_user_id_fkey', 'posts', type_='foreignkey')
    op.drop_column('posts', 'user_id')
    op.drop_table('sessions')
