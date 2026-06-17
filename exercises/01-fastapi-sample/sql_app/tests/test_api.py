import pytest
from fastapi.testclient import TestClient


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
