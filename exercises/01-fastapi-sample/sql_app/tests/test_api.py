from datetime import datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from ..models import Item, User


@pytest.mark.usefixtures("test_db")
def test_create_user(client: TestClient) -> None:
    response = client.post(
        "/users",
        json={"email": "deadpool@example.com", "password": "chimichangas4life"},
    )
    # 認証不要エンドポイントでユーザー作成が成功すること
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["email"] == "deadpool@example.com"
    # IDが払い出されること
    assert "id" in data
    # api_token がレスポンスに含まれること（以降の認証に使う）
    assert "api_token" in data
    user_id = data["id"]
    token = data["api_token"]

    response = client.get(f"/users/{user_id}", headers={"X-API-TOKEN": token})
    # 発行されたトークンで認証が通り、ユーザー情報を取得できること
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["email"] == "deadpool@example.com"
    assert data["id"] == user_id
    # GET レスポンスには api_token が含まれないこと（作成時のみ返す）
    assert "api_token" not in data


@pytest.mark.usefixtures("test_db")
def test_unauthorized(client: TestClient) -> None:
    dummy_id = 99999

    response = client.get("/users")
    # X-API-TOKEN ヘッダーなしでは一覧取得が拒否されること
    assert response.status_code == 401, response.text

    response = client.get(f"/users/{dummy_id}")
    # X-API-TOKEN ヘッダーなしではユーザー取得が拒否されること
    assert response.status_code == 401, response.text

    response = client.post(
        f"/users/{dummy_id}/items",
        json={"title": "Test Item", "description": "This is test item"},
    )
    # X-API-TOKEN ヘッダーなしではアイテム作成が拒否されること
    assert response.status_code == 401, response.text

    response = client.get("/items")
    # X-API-TOKEN ヘッダーなしではアイテム一覧取得が拒否されること
    assert response.status_code == 401, response.text


@pytest.mark.usefixtures("test_db")
def test_invalid_token(client: TestClient) -> None:
    response = client.get("/users", headers={"X-API-TOKEN": "invalid-token"})
    # DB に存在しないトークンでは認証が拒否されること
    assert response.status_code == 401, response.text


@pytest.mark.usefixtures("test_db")
def test_health_check_no_auth(client: TestClient) -> None:
    response = client.get("/health-check")
    # ヘルスチェックは認証不要で 200 を返すこと
    assert response.status_code == 200, response.text


@pytest.mark.usefixtures("test_db")
def test_get_items_for_user(client: TestClient, db_session: Session) -> None:
    # ---- セットアップ: 2ユーザーとそれぞれのアイテムを作成 ----
    res = client.post("/users", json={"email": "user1@example.com", "password": "pass1"})
    user1 = res.json()
    user_id1, token1 = user1["id"], user1["api_token"]

    res = client.post("/users", json={"email": "user2@example.com", "password": "pass2"})
    user2 = res.json()
    user_id2, token2 = user2["id"], user2["api_token"]

    res = client.post(
        f"/users/{user_id1}/items",
        headers={"X-API-TOKEN": token1},
        json={"title": "Old Item", "description": "desc"},
    )
    item_old_id = res.json()["id"]
    _set_created_at(db_session, item_old_id, datetime(2023, 1, 1))

    res = client.post(
        f"/users/{user_id1}/items",
        headers={"X-API-TOKEN": token1},
        json={"title": "New Item", "description": "desc"},
    )
    item_new_id = res.json()["id"]
    _set_created_at(db_session, item_new_id, datetime(2023, 1, 3))

    res = client.post(
        f"/users/{user_id2}/items",
        headers={"X-API-TOKEN": token2},
        json={"title": "User2 Item", "description": "desc"},
    )
    item_user2_id = res.json()["id"]

    # フィルタなし: created_at 降順で user1 のアイテムのみ返ること
    res = client.get(f"/users/{user_id1}/items", headers={"X-API-TOKEN": token1})
    assert res.status_code == 200, res.text
    ids = [d["id"] for d in res.json()]
    assert ids == [item_new_id, item_old_id]
    # user2 のアイテムが含まれないこと（owner_id スコープ）
    assert item_user2_id not in ids

    # done=False で未完了のみ返ること
    client.patch(
        f"/users/{user_id1}/items/{item_new_id}",
        headers={"X-API-TOKEN": token1},
        json={"done": True},
    )
    res = client.get(
        f"/users/{user_id1}/items",
        headers={"X-API-TOKEN": token1},
        params={"done": "False"},
    )
    assert res.status_code == 200, res.text
    assert [d["id"] for d in res.json()] == [item_old_id]

    # done=True で完了済みのみ返ること
    res = client.get(
        f"/users/{user_id1}/items",
        headers={"X-API-TOKEN": token1},
        params={"done": "True"},
    )
    assert res.status_code == 200, res.text
    assert [d["id"] for d in res.json()] == [item_new_id]

    # date=20230103 で 2023-01-03 の JST 日付範囲のアイテムのみ返ること
    res = client.get(
        f"/users/{user_id1}/items",
        headers={"X-API-TOKEN": token1},
        params={"date": "20230103"},
    )
    assert res.status_code == 200, res.text
    assert [d["id"] for d in res.json()] == [item_new_id]

    # date + done の組み合わせフィルタが機能すること
    res = client.get(
        f"/users/{user_id1}/items",
        headers={"X-API-TOKEN": token1},
        params={"date": "20230103", "done": "False"},
    )
    assert res.status_code == 200, res.text
    # item_new は done=True なので、done=False で絞ると 0 件
    assert res.json() == []

    # 不正な date フォーマットは 400 を返すこと
    res = client.get(
        f"/users/{user_id1}/items",
        headers={"X-API-TOKEN": token1},
        params={"date": "2023-01-03"},
    )
    assert res.status_code == 400, res.text

    # 認証なしでは 401 を返すこと
    res = client.get(f"/users/{user_id1}/items")
    assert res.status_code == 401, res.text


def _set_created_at(db: Session, item_id: int, created_at: datetime) -> None:
    item = db.query(Item).filter(Item.id == item_id).first()
    assert item is not None
    item.created_at = created_at
    db.commit()


@pytest.mark.usefixtures("test_db")
def test_delete_user(client: TestClient, db_session: Session) -> None:
    # ---- セットアップ: 2ユーザーとアイテムを作成 ----
    res = client.post("/users", json={"email": "user1@example.com", "password": "pass1"})
    user1 = res.json()
    user_id1, token1 = user1["id"], user1["api_token"]

    res = client.post("/users", json={"email": "user2@example.com", "password": "pass2"})
    user2 = res.json()
    user_id2, token2 = user2["id"], user2["api_token"]

    res = client.post(
        f"/users/{user_id2}/items",
        headers={"X-API-TOKEN": token2},
        json={"title": "user2 item", "description": "desc"},
    )
    item_id = res.json()["id"]

    # user2 を削除すると 204 が返ること
    res = client.delete(f"/users/{user_id2}", headers={"X-API-TOKEN": token1})
    assert res.status_code == 204, res.text

    # 削除後に GET すると 404 が返ること（論理削除で非活性になっているため）
    res = client.get(f"/users/{user_id2}", headers={"X-API-TOKEN": token1})
    assert res.status_code == 404, res.text

    # 削除済みユーザーのトークンでは認証できないこと
    res = client.get("/users", headers={"X-API-TOKEN": token2})
    assert res.status_code == 401, res.text

    # item の所有者が有効ユーザーの最小 id（user1）へ移っていること
    items = client.get(f"/users/{user_id1}/items", headers={"X-API-TOKEN": token1}).json()
    assert any(d["id"] == item_id for d in items)

    # DB で is_active が False になっていること
    user = db_session.query(User).filter(User.id == user_id2).first()
    assert user is not None
    assert user.is_active is False


@pytest.mark.usefixtures("test_db")
def test_delete_user_not_found(client: TestClient) -> None:
    res = client.post("/users", json={"email": "user1@example.com", "password": "pass1"})
    token = res.json()["api_token"]

    res = client.delete("/users/99999", headers={"X-API-TOKEN": token})
    # 存在しないユーザーを削除しようとすると 404 が返ること
    assert res.status_code == 404, res.text


@pytest.mark.usefixtures("test_db")
def test_delete_user_no_transfer_target(client: TestClient, db_session: Session) -> None:
    # 自分しかいない状態でも削除が成功すること（移管先なし）
    res = client.post("/users", json={"email": "user1@example.com", "password": "pass1"})
    user1 = res.json()
    user_id1, token1 = user1["id"], user1["api_token"]

    res = client.post(
        f"/users/{user_id1}/items",
        headers={"X-API-TOKEN": token1},
        json={"title": "item", "description": "desc"},
    )
    item_id = res.json()["id"]

    res = client.delete(f"/users/{user_id1}", headers={"X-API-TOKEN": token1})
    # 移管先がいなくても削除は成功すること
    assert res.status_code == 204, res.text

    # 移管先がいない場合、item の owner_id は変わらないこと
    item = db_session.query(Item).filter(Item.id == item_id).first()
    assert item is not None
    assert item.owner_id == user_id1


@pytest.mark.usefixtures("test_db")
def test_delete_user_requires_auth(client: TestClient) -> None:
    res = client.delete("/users/1")
    # 認証なしで削除を試みると 401 が返ること
    assert res.status_code == 401, res.text


@pytest.mark.usefixtures("test_db")
def test_duplicate_email(client: TestClient) -> None:
    client.post(
        "/users",
        json={"email": "deadpool@example.com", "password": "chimichangas4life"},
    )
    response = client.post(
        "/users",
        json={"email": "deadpool@example.com", "password": "anotherpassword"},
    )
    # 同一メールアドレスで2回登録すると 400 が返ること
    assert response.status_code == 400, response.text
