"""seed users and groups

Revision ID: da8d57b826a7
Revises: 3055c903b988
Create Date: 2026-10-28 11:19:45.058025

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "da8d57b826a7"
down_revision: str | Sequence[str] | None = "3055c903b988"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Seed data required by the brief.
USERNAMES = ["alice", "bob", "carol", "dan"]
GROUPS = [
    (1, "Chiang Mai trip", ["alice", "bob", "carol"]),
    (2, "Office lunch", ["bob", "dan"]),
]


def upgrade() -> None:
    """Insert the brief's users, groups and memberships."""
    for username in USERNAMES:
        op.execute(f"INSERT INTO users (username) VALUES ('{username}')")

    for group_id, name, members in GROUPS:
        # Explicit IDs, so the groups match the brief's group 1 and group 2.
        op.execute(f"INSERT INTO groups (id, name) VALUES ({group_id}, '{name}')")
        for username in members:
            op.execute(
                "INSERT INTO group_members (group_id, user_id) "
                f"SELECT {group_id}, id FROM users WHERE username = '{username}'"
            )

    # Move the identity sequence past the explicit IDs so later inserts do not collide.
    op.execute(
        "SELECT setval(pg_get_serial_sequence('groups', 'id'), "
        "(SELECT max(id) FROM groups))"
    )


def downgrade() -> None:
    """Remove the seeded rows."""
    group_ids = ", ".join(str(group_id) for group_id, _, _ in GROUPS)
    usernames = ", ".join(f"'{username}'" for username in USERNAMES)
    op.execute(f"DELETE FROM group_members WHERE group_id IN ({group_ids})")
    op.execute(f"DELETE FROM groups WHERE id IN ({group_ids})")
    op.execute(f"DELETE FROM users WHERE username IN ({usernames})")
