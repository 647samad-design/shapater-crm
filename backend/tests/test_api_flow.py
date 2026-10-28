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


async def test_csv_import_and_parse_endpoint(client):
    h = await register(client, "imp@x.com", "Import Co")
    csv_clients = "Name,Mobile,Source\nAli,0300-1111111,whatsapp\nAli Dup,+92 300 1111111,whatsapp\n,0321,x\n"
    r = await client.post("/api/v1/import/clients", headers=h, files={"file": ("c.csv", csv_clients, "text/csv")})
    assert r.json()["created"] == 1 and r.json()["duplicates_skipped"] == 1 and len(r.json()["errors"]) == 1

    csv_props = "Title,Demand,Beds,Area,City,Size,Unit\nHouse A,2.5,4,DHA,Lahore,10,marla\nHouse B,25000000,3,DHA,Lahore,5,marla\n"
    r = await client.post("/api/v1/import/properties", headers=h, files={"file": ("p.csv", csv_props, "text/csv")})
    assert r.json()["created"] == 2 and r.json()["errors"] == []

    p = await client.post("/api/v1/ai/parse-message", headers=h, json={"text": "5 marla house DHA Phase 6 Lahore, 2.5 crore"})
    assert p.json()["kind"] == "property" and p.json()["data"]["price"] == 25000000


async def test_detailed_matches_join(client):
    h = await register(client, "det@x.com", "Detail Co")
    c = await client.post("/api/v1/clients", headers=h, json={"name": "Sara", "phone": "0311-2223333"})
    await client.post("/api/v1/properties", headers=h, json=PROP)
    await client.post("/api/v1/requirements", headers=h, json={
        "client_id": c.json()["id"], "purpose": "sale", "currency": "PKR", "budget_max": 30000000,
        "city": "Lahore", "preferred_areas": ["DHA Phase 6"]})
    d = (await client.get("/api/v1/matches/detailed", headers=h)).json()
    assert len(d) == 1 and d[0]["client"]["name"] == "Sara" and d[0]["property"]["area_name"] == "DHA Phase 6"
