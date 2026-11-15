import time

import pytest

from app.telegram_auth import InitDataError, sign_init_data, validate_init_data

TOKEN = "123456:TEST"


def test_valid_init_data():
    s = sign_init_data({"auth_date": int(time.time()), "query_id": "q", "user": {"id": 42, "first_name": "Никита"}}, TOKEN)
    data = validate_init_data(s, TOKEN)
    assert data["user"]["id"] == 42


def test_tampered_init_data():
    s = sign_init_data({"auth_date": int(time.time()), "user": {"id": 42}}, TOKEN)
    with pytest.raises(InitDataError):
        validate_init_data(s.replace("42", "43"), TOKEN)


def test_wrong_token():
    s = sign_init_data({"auth_date": int(time.time()), "user": {"id": 42}}, TOKEN)
    with pytest.raises(InitDataError):
        validate_init_data(s, "999:OTHER")


def test_expired():
    s = sign_init_data({"auth_date": int(time.time()) - 90000, "user": {"id": 42}}, TOKEN)
    with pytest.raises(InitDataError):
        validate_init_data(s, TOKEN, ttl=86400)


async def test_api_accepts_signed_init_data(client):
    s = sign_init_data({"auth_date": int(time.time()), "user": {"id": 77, "first_name": "Аня", "username": "anya"}}, TOKEN)
    r = await client.get("/api/me", headers={"Authorization": f"tma {s}"})
    assert r.status_code == 200
    body = r.json()
    assert body["user"]["username"] == "anya" and body["user"]["role"] == "guest"
    assert body["ref_link"].startswith("https://t.me/elis_team_bot?start=ELS")


async def test_api_rejects_without_auth(client):
    assert (await client.get("/api/me")).status_code == 401
