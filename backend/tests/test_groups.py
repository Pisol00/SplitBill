def test_list_groups_returns_only_the_requesting_users_groups(client):
    response = client.get("/groups", headers={"X-User": "alice"})

    assert response.status_code == 200
    assert response.json() == [{"id": 1, "name": "Chiang Mai trip"}]


def test_list_groups_returns_every_group_of_the_user_ordered_by_id(client):
    response = client.get("/groups", headers={"X-User": "bob"})

    assert response.status_code == 200
    assert response.json() == [
        {"id": 1, "name": "Chiang Mai trip"},
        {"id": 2, "name": "Office lunch"},
    ]


def test_get_group_returns_the_group_with_its_members(client):
    response = client.get("/groups/1", headers={"X-User": "alice"})

    assert response.status_code == 200
    assert response.json() == {
        "id": 1,
        "name": "Chiang Mai trip",
        "members": ["alice", "bob", "carol"],
    }


def test_get_group_is_available_to_every_member(client):
    response = client.get("/groups/2", headers={"X-User": "dan"})

    assert response.status_code == 200
    assert response.json() == {
        "id": 2,
        "name": "Office lunch",
        "members": ["bob", "dan"],
    }
