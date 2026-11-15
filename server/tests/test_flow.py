from tests.conftest import as_user

NEWBIE, ADMIN = 500, 1
APP = {"direction": "msg", "age_group": "25–34", "hours": "4–6 часов", "experience": "Немного", "goal": "Заработок", "adult_and_rules": True}


async def onboard(client):
    h = as_user(NEWBIE)
    free = (await client.get("/api/onboarding/free-lessons", headers=h)).json()
    assert len(free) == 3
    assert (await client.post(f"/api/onboarding/free-lessons/{free[0]['id']}/seen", headers=h)).json() == {"ok": True}
    res = (await client.post("/api/onboarding/role-test", json={"answers": [1, 1, 0, 1, 1, 1, 2, 1, 2, 2]}, headers=h)).json()
    assert res["top"] == "msg"
    r = await client.post("/api/onboarding/application", json=APP, headers=h)
    assert r.status_code == 201, r.text
    return r.json()["id"]


async def test_application_rules(client):
    h = as_user(NEWBIE)
    r = await client.post("/api/onboarding/application", json=APP, headers=h)
    assert r.status_code == 422 and "тест" in r.json()["detail"]  # без теста на роль нельзя
    await client.post("/api/onboarding/role-test", json={"answers": [0] * 10}, headers=h)
    r = await client.post("/api/onboarding/application", json={**APP, "adult_and_rules": False}, headers=h)
    assert r.status_code == 422
    assert (await client.post("/api/onboarding/application", json=APP, headers=h)).status_code == 201
    assert (await client.post("/api/onboarding/application", json=APP, headers=h)).status_code == 409  # дубль


async def test_guest_cannot_open_academy_or_admin(client):
    h = as_user(NEWBIE)
    assert (await client.get("/api/academy/modules", headers=h)).status_code == 403
    assert (await client.get("/api/admin/applications", headers=h)).status_code == 403


async def test_reject_blocks_reapply_for_30_days(client):
    app_id = await onboard(client)
    r = await client.post(f"/api/admin/applications/{app_id}/decision", json={"decision": "rejected"}, headers=as_user(ADMIN))
    assert r.json()["status"] == "rejected"
    r = await client.post("/api/onboarding/application", json=APP, headers=as_user(NEWBIE))
    assert r.status_code == 409 and "Повторно" in r.json()["detail"]


async def test_full_path(client, db):
    app_id = await onboard(client)
    apps = (await client.get("/api/admin/applications", headers=as_user(ADMIN))).json()
    assert apps[0]["role_test"]["top"] == "msg"
    r = await client.post(f"/api/admin/applications/{app_id}/decision", json={"decision": "approved"}, headers=as_user(ADMIN))
    assert r.json()["status"] == "approved"
    assert db and db[-1][0] == NEWBIE and "одобрена" in db[-1][1]  # бот прислал ответ

    h = as_user(NEWBIE)
    me = (await client.get("/api/me", headers=h)).json()
    assert me["user"]["role"] == "student" and me["user"]["direction"] == "msg" and me["application"]["status"] == "approved"

    mods = (await client.get("/api/academy/modules", headers=h)).json()
    assert [m["title"] for m in mods] == ["Общий блок", "Переписка"]
    first, second = mods[0]["lessons"][0], mods[0]["lessons"][1]
    assert first["status"] == "current" and second["status"] == "locked"
    assert (await client.get(f"/api/academy/lessons/{second['id']}", headers=h)).status_code == 403

    lesson = (await client.get(f"/api/academy/lessons/{first['id']}", headers=h)).json()
    assert "correct" not in str(lesson["quiz"])  # ответы не уходят на клиент
    wrong = (await client.post(f"/api/academy/lessons/{first['id']}/quiz", json={"answers": [0]}, headers=h)).json()
    assert wrong["passed"] is False and wrong["results"][0]["correct"] == 1
    again = await client.post(f"/api/academy/lessons/{first['id']}/quiz", json={"answers": [1]}, headers=h)
    assert again.status_code == 429  # пересдача только через час

    # заметки: свои видны, чужие недоступны
    n = (await client.post(f"/api/academy/lessons/{first['id']}/notes", json={"text": "забрать фразу", "t_sec": 48}, headers=h)).json()
    assert (await client.get(f"/api/academy/lessons/{first['id']}/notes", headers=h)).json()[0]["t_sec"] == 48
    assert (await client.delete(f"/api/academy/notes/{n['id']}", headers=as_user(ADMIN))).status_code == 404
    assert (await client.delete(f"/api/academy/notes/{n['id']}", headers=h)).status_code == 204


async def test_quiz_pass_unlocks_next(client):
    app_id = await onboard(client)
    await client.post(f"/api/admin/applications/{app_id}/decision", json={"decision": "approved"}, headers=as_user(ADMIN))
    h = as_user(NEWBIE)
    mods = (await client.get("/api/academy/modules", headers=h)).json()
    first = mods[0]["lessons"][0]
    r = (await client.post(f"/api/academy/lessons/{first['id']}/quiz", json={"answers": [1]}, headers=h)).json()
    assert r["passed"] and r["xp"] == 100
    mods = (await client.get("/api/academy/modules", headers=h)).json()
    assert [l["status"] for l in mods[0]["lessons"]] == ["done", "current", "locked"]


async def test_orders_flow(client):
    h = as_user(NEWBIE)
    await client.get("/api/me", headers=h)
    people = (await client.get("/api/admin/people", headers=as_user(ADMIN))).json()
    uid = next(p["id"] for p in people if p["tg_id"] == NEWBIE)
    assert (await client.get("/api/orders", headers=h)).status_code == 403  # гость не видит биржу
    await client.post(f"/api/admin/people/{uid}/role", json={"role": "member"}, headers=as_user(ADMIN))
    orders = (await client.get("/api/orders", headers=h)).json()
    oid = orders[0]["id"]
    assert (await client.post(f"/api/orders/{oid}/take", headers=h)).json() == {"status": "requested"}
    assert (await client.post(f"/api/orders/{oid}/take", headers=h)).status_code == 409
    assert (await client.post(f"/api/orders/{oid}/reports", json={"numbers": {"invited": 52}}, headers=h)).status_code == 403
    from sqlalchemy import select
    from app.db import SessionLocal
    from app.models import OrderMember
    async with SessionLocal() as s:
        mid = await s.scalar(select(OrderMember.id))
    await client.post(f"/api/admin/order-members/{mid}/confirm", headers=as_user(ADMIN))
    r = await client.post(f"/api/orders/{oid}/reports", json={"numbers": {"invited": 52}, "comment": "чаты новостроек"}, headers=h)
    assert r.status_code == 201


async def test_lesson_editor_validation(client):
    a = as_user(ADMIN)
    mods = (await client.get("/api/academy/modules", headers=a)).json()
    mid = mods[1]["id"]
    base = {"module_id": mid, "title": "Переход к оплате", "youtube": "https://youtu.be/aB3dE5fG7hJ"}
    r = await client.post("/api/admin/lessons", json={**base, "published": True}, headers=a)
    assert r.status_code == 422 and "Не хватает" in r.json()["detail"]
    r = await client.post("/api/admin/lessons", json={**base, "youtube": "https://example.com/x"}, headers=a)
    assert r.status_code == 422
    q = {"text": "Вопрос", "options": ["Да", "Нет"], "correct": 1}
    full = {**base, "published": True, "chapters": [[60, "Пример"], [0, "Вступление"]], "summary_md": "Показываем пользу и только потом называем цену. " * 2,
            "questions": [q, q, q], "pass_score": 2}
    r = await client.post("/api/admin/lessons", json=full, headers=a)
    assert r.status_code == 201 and r.json()["youtube_id"] == "aB3dE5fG7hJ"
    bad_q = {**full, "questions": [{"text": "x", "options": ["a", "b"], "correct": 5}]}
    assert (await client.post("/api/admin/lessons", json=bad_q, headers=a)).status_code == 422
