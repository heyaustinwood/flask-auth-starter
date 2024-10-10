"""Add unique constraint to Invitation model

Revision ID: b041cef628a5
Revises: 50d365f77dc1
Create Date: 2024-10-08 14:30:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'b041cef628a5'
down_revision = '50d365f77dc1'
branch_labels = None
depends_on = None

def upgrade():
    # Create a temporary table with the desired structure
    op.execute("""
    CREATE TABLE tmp_invitation (
        id INTEGER NOT NULL PRIMARY KEY,
        email VARCHAR(120),
        organization_id INTEGER,
        inviter_id INTEGER,
        token VARCHAR(64),
        created_at DATETIME,
        UNIQUE (email, organization_id)
    )
    """)

    # Copy data from the original table to the temporary table, keeping only the latest invitation for each email-organization pair
    op.execute("""
    INSERT INTO tmp_invitation (id, email, organization_id, inviter_id, token, created_at)
    SELECT id, email, organization_id, inviter_id, token, created_at
    FROM (
        SELECT *, ROW_NUMBER() OVER (PARTITION BY email, organization_id ORDER BY created_at DESC) as rn
        FROM invitation
    ) sub
    WHERE rn = 1
    """)

    # Drop the original table
    op.drop_table('invitation')

    # Rename the temporary table to the original name
    op.rename_table('tmp_invitation', 'invitation')

    # Re-create indexes
    with op.batch_alter_table('invitation', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_invitation_email'), ['email'], unique=False)
        batch_op.create_index(batch_op.f('ix_invitation_token'), ['token'], unique=True)

def downgrade():
    with op.batch_alter_table('invitation', schema=None) as batch_op:
        batch_op.drop_constraint('uq_invitation_email_organization_id', type_='unique')
