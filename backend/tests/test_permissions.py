from app.core.ratelimit import login_limiter
from tests.conftest import register

PROP = {"title": "House", "purpose": "sale", "property_type": "house", "price": 25000000, "currency": "PKR",
        "bedrooms": 4, "city": "Lahore", "area_name": "DHA Phase 6"}


async def _agent(client, owner, email):
    r = await client.post("/api/v1/users", headers=owner, json={"full_name": email, "email": email, "password": "agentpass123", "role": "agent"})
    tok = (await client.post("/api/v1/auth/login", json={"email": email, "password": "agentpass123"})).json()["access_token"]
    return r.json()["id"], {"Authorization": f"Bearer {tok}"}


async def test_agents_only_see_their_own_clients_leads_and_matches(client):
    owner = await register(client, "own@perm.com", "Perm Co")
    a1_id, a1 = await _agent(client, owner, "a1@perm.com")
    a2_id, a2 = await _agent(client, owner, "a2@perm.com")
    await client.post("/api/v1/properties", headers=owner, json=PROP)

    # agent 1 creates a client + requirement + lead; agent 2 creates a different client
    c1 = (await client.post("/api/v1/clients", headers=a1, json={"name": "C1", "phone": "0300-1000001"})).json()
    c2 = (await client.post("/api/v1/clients", headers=a2, json={"name": "C2", "phone": "0300-1000002"})).json()
    assert c1["assigned_to"] == a1_id
    r1 = (await client.post("/api/v1/requirements", headers=a1, json={"client_id": c1["id"], "purpose": "sale", "currency": "PKR", "budget_max": 30000000, "city": "Lahore"})).json()
    await client.post("/api/v1/requirements", headers=a2, json={"client_id": c2["id"], "purpose": "sale", "currency": "PKR", "budget_max": 30000000, "city": "Lahore"})
    lead1 = (await client.post("/api/v1/leads", headers=a1, json={"client_id": c1["id"], "source": "whatsapp"})).json()

    # visibility
    assert [c["name"] for c in (await client.get("/api/v1/clients", headers=a1)).json()] == ["C1"]
    assert [c["name"] for c in (await client.get("/api/v1/clients", headers=a2)).json()] == ["C2"]
    assert len((await client.get("/api/v1/clients", headers=owner)).json()) == 2
    assert (await client.get(f"/api/v1/clients/{c1['id']}", headers=a2)).status_code == 404
    assert (await client.patch(f"/api/v1/leads/{lead1['id']}", headers=a2, json={"stage": "won"})).status_code == 404
    assert (await client.post("/api/v1/requirements", headers=a2, json={"client_id": c1["id"], "purpose": "sale", "currency": "PKR"})).status_code == 404
    assert (await client.get("/api/v1/leads", headers=a2)).json() == []

    # matches: each agent only sees matches for their own clients
    m1 = (await client.get("/api/v1/matches/detailed", headers=a1)).json()
    assert len(m1) == 1 and m1[0]["client"]["name"] == "C1"
    assert len((await client.get("/api/v1/matches/detailed", headers=owner)).json()) == 2
    mid = (await client.get("/api/v1/matches", headers=a1)).json()[0]["id"]
    assert (await client.get(f"/api/v1/matches/{mid}/whatsapp", headers=a2)).status_code == 404
    assert (await client.patch(f"/api/v1/matches/{mid}", headers=a2, json={"status": "sent"})).status_code == 404

    # dashboard is scoped too
    assert (await client.get("/api/v1/dashboard/summary", headers=a2)).json()["clients"] == 1
    assert (await client.get("/api/v1/dashboard/summary", headers=owner)).json()["clients"] == 2

    # agents cannot reassign; owner can, and then the agent sees it
    assert (await client.patch(f"/api/v1/clients/{c2['id']}", headers=a2, json={"assigned_to": a1_id})).status_code == 403
    assert (await client.patch(f"/api/v1/clients/{c2['id']}", headers=owner, json={"assigned_to": a1_id})).status_code == 200
    assert len((await client.get("/api/v1/clients", headers=a1)).json()) == 2

    # a duplicate of a colleague's client does not leak its id
    dup = await client.post("/api/v1/clients", headers=a2, json={"name": "x", "phone": "0300-1000001"})
    assert dup.status_code == 409 and "client_id" not in dup.json()["detail"]


async def test_login_rate_limit(client):
    login_limiter.clear()
    await register(client, "brute@perm.com", "Brute Co")
    for _ in range(5):
        assert (await client.post("/api/v1/auth/login", json={"email": "brute@perm.com", "password": "wrongpass"})).status_code == 401
    blocked = await client.post("/api/v1/auth/login", json={"email": "brute@perm.com", "password": "supersecret1"})
    assert blocked.status_code == 429 and "Retry-After" in blocked.headers  # even the right password is refused while locked
    login_limiter.clear()
    assert (await client.post("/api/v1/auth/login", json={"email": "brute@perm.com", "password": "supersecret1"})).status_code == 200
