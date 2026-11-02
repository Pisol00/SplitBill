"""The seed migration provides the brief's users and groups. Checked through the API."""

import pytest

SEED_GROUPS = {
    1: ("Chiang Mai trip", ["alice", "bob", "carol"]),
    2: ("Office lunch", ["bob", "dan"]),
}


@pytest.mark.parametrize("username", ["alice", "bob", "carol", "dan"])
def test_every_seeded_user_exists(client, username):
    # An unknown user would get 401 unknown_user.
    response = client.get("/groups", headers={"X-User": username})

    assert response.status_code == 200


@pytest.mark.parametrize("group_id", SEED_GROUPS)
def test_seeded_groups_have_the_briefs_names_and_members(client, group_id):
    name, members = SEED_GROUPS[group_id]

    response = client.get(f"/groups/{group_id}", headers={"X-User": members[0]})

    assert response.json() == {"id": group_id, "name": name, "members": members}


def test_each_user_sees_exactly_the_groups_they_were_seeded_into(client):
    expected = {"alice": [1], "bob": [1, 2], "carol": [1], "dan": [2]}

    for username, group_ids in expected.items():
        response = client.get("/groups", headers={"X-User": username})
        assert [group["id"] for group in response.json()] == group_ids, username
