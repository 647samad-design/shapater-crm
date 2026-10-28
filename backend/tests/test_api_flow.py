from tests.conftest import register

PROP = {"title": "5 Marla House DHA Phase 6", "purpose": "sale", "property_type": "house", "price": 25000000,
        "currency": "PKR", "area_value": 10, "area_unit": "marla", "bedrooms": 4, "city": "Lahore",
        "area_name": "DHA Phase 6", "features": ["parking"]}


async def test_full_flow_and_automatic_matching(client):
    h = await register(client, "a@agency1.com", "Agency One")

    # client + duplicate detection (different phone formats, same number)
    c = await client.post("/api/v1/clients", headers=h, json={"name": "Ahmed", "phone": "0300-1234567"})
    assert c.status_code == 201
    dup = await client.post("/api/v1/clients", headers=h, json={"name": "Ahmed 2", "phone": "+92 300 1234567"})
    assert dup.status_code == 409

    # requirement first, property later -> property creation triggers matching
    r = await client.post("/api/v1/requirements", headers=h, json={
        "client_id": c.json()["id"], "purpose": "sale", "property_types": ["house"], "budget_min": 20000000,
        "budget_max": 30000000, "currency": "PKR", "city": "Lahore", "preferred_areas": ["DHA Phase 6"],
        "bedrooms_min": 3, "bedrooms_max": 5})
    assert r.status_code == 201

    p = await client.post("/api/v1/properties", headers=h, json=PROP)
    assert p.status_code == 201
    assert p.json()["area_sqft"] == 2722.5

    m = await client.get("/api/v1/matches", headers=h)
    assert len(m.json()) == 1 and m.json()[0]["score"] >= 90

    wa = await client.get(f"/api/v1/matches/{m.json()[0]['id']}/whatsapp", headers=h)
    assert "wa.me/923001234567" in wa.json()["wa_link"]

    # pipeline
    lead = await client.post("/api/v1/leads", headers=h, json={"client_id": c.json()["id"], "source": "whatsapp"})
    up = await client.patch(f"/api/v1/leads/{lead.json()['id']}", headers=h, json={"stage": "won"})
    assert up.json()["stage"] == "won"
    s = await client.get("/api/v1/dashboard/summary", headers=h)
    assert s.json()["conversion_rate"] == 100.0 and s.json()["new_matches"] == 1


async def test_tenant_isolation(client):
    h1 = await register(client, "o@one.com", "One")
    h2 = await register(client, "o@two.com", "Two")
    p = await client.post("/api/v1/properties", headers=h1, json=PROP)
    pid = p.json()["id"]
    assert (await client.get(f"/api/v1/properties/{pid}", headers=h2)).status_code == 404
    assert (await client.get("/api/v1/properties", headers=h2)).json() == []


async def test_auth_and_roles(client):
    h = await register(client, "boss@x.com", "X Agency")
    assert (await client.get("/api/v1/properties")).status_code == 401
    a = await client.post("/api/v1/users", headers=h, json={
        "full_name": "Agent", "email": "agent@x.com", "password": "agentpass123", "role": "agent"})
    assert a.status_code == 201
    login = await client.post("/api/v1/auth/login", json={"email": "agent@x.com", "password": "agentpass123"})
    ah = {"Authorization": f"Bearer {login.json()['access_token']}"}
    p = await client.post("/api/v1/properties", headers=ah, json=PROP)
    assert (await client.delete(f"/api/v1/properties/{p.json()['id']}", headers=ah)).status_code == 403  # agents can't delete
    assert (await client.delete(f"/api/v1/properties/{p.json()['id']}", headers=h)).status_code == 204
    assert (await client.post("/api/v1/auth/login", json={"email": "agent@x.com", "password": "wrong"})).status_code == 401
