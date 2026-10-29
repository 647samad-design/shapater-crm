from cryptography.fernet import Fernet
from sqlalchemy import text

from app.core import crypto
from app.core.config import settings
from app.core.db import SessionLocal, set_tenant
from tests.conftest import register

SECRET = "sk_test_51Abc123DEF456ghiZ789"
B = "/api/v1/integrations/keys"


def test_crypto_roundtrip_and_rotation():
    old = settings.encryption_keys
    k1, k2 = Fernet.generate_key().decode(), Fernet.generate_key().decode()
    try:
        settings.encryption_keys = k1
        token = crypto.encrypt("hello-secret")
        assert "hello-secret" not in token and crypto.decrypt(token) == "hello-secret"
        settings.encryption_keys = f"{k2},{k1}"  # rotation: new key first, old still decrypts
        assert crypto.decrypt(token) == "hello-secret"
        settings.encryption_keys = k2  # old key removed -> cannot decrypt
        try:
            crypto.decrypt(token)
            raise AssertionError("should have failed")
        except ValueError:
            pass
    finally:
        settings.encryption_keys = old


async def test_key_lifecycle_never_leaks_plaintext(client):
    h = await register(client, "keys@owner.com", "Keys Co")
    me = (await client.get("/api/v1/me", headers=h)).json()

    r = await client.post(B, headers=h, json={"provider": "stripe", "label": "Live secret", "value": SECRET, "notes": "billing"})
    assert r.status_code == 201 and r.json()["warning"] is None
    kid = r.json()["id"]
    assert SECRET not in r.text and r.json()["masked"] == "••••••••Z789"

    lst = await client.get(B, headers=h)
    assert SECRET not in lst.text and lst.json()[0]["masked"].endswith("Z789")

    rv = await client.post(f"{B}/{kid}/reveal", headers=h)
    assert rv.json()["value"] == SECRET and rv.headers["cache-control"] == "no-store"

    # stored value is ciphertext, and the audit trail never contains the secret
    async with SessionLocal() as s:
        await set_tenant(s, me["agency_id"])
        stored = (await s.execute(text("SELECT encrypted_value FROM api_keys"))).scalar_one()
        audits = str((await s.execute(text("SELECT changes FROM audit_logs WHERE entity='api_key'"))).all())
    assert SECRET not in stored and stored.startswith("gAAAA")
    assert SECRET not in audits

    up = await client.patch(f"{B}/{kid}", headers=h, json={"value": "sk_test_NEWVALUE0000", "label": "Live key"})
    assert up.json()["masked"].endswith("0000") and up.json()["label"] == "Live key"
    assert (await client.post(f"{B}/{kid}/reveal", headers=h)).json()["value"] == "sk_test_NEWVALUE0000"

    await client.post(B, headers=h, json={"provider": "stripe", "label": "Webhook", "value": "whsec_abcdefgh1234"})
    dup = await client.patch(f"{B}/{kid}", headers=h, json={"label": "Webhook"})
    assert dup.status_code == 409
    assert (await client.post(B, headers=h, json={"provider": "stripe", "label": "Webhook", "value": "whsec_zzzzzzzz9999"})).status_code == 409

    assert (await client.delete(f"{B}/{kid}", headers=h)).status_code == 204
    assert len((await client.get(B, headers=h)).json()) == 1


async def test_soft_warning_and_validation(client):
    h = await register(client, "warn@owner.com", "Warn Co")
    r = await client.post(B, headers=h, json={"provider": "stripe", "label": "odd", "value": "notastripekey123"})
    assert r.status_code == 201 and "does not look like" in r.json()["warning"]
    assert (await client.post(B, headers=h, json={"provider": "nope", "label": "x", "value": "12345678"})).status_code == 422
    assert (await client.post(B, headers=h, json={"provider": "custom", "label": "x", "value": "short"})).status_code == 422


async def test_only_owner_and_tenant_isolation(client):
    owner = await register(client, "o1@keys.com", "Agency A")
    other = await register(client, "o2@keys.com", "Agency B")
    kid = (await client.post(B, headers=owner, json={"provider": "openai", "label": "main", "value": "sk-abcdefgh1234"})).json()["id"]

    await client.post("/api/v1/users", headers=owner, json={"full_name": "Ag", "email": "ag@keys.com", "password": "agentpass123", "role": "agent"})
    tok = (await client.post("/api/v1/auth/login", json={"email": "ag@keys.com", "password": "agentpass123"})).json()["access_token"]
    agent = {"Authorization": f"Bearer {tok}"}
    for method, url in (("get", B), ("post", f"{B}/{kid}/reveal"), ("delete", f"{B}/{kid}")):
        assert (await getattr(client, method)(url, headers=agent)).status_code == 403
    assert (await client.get(B)).status_code == 401

    assert (await client.get(B, headers=other)).json() == []
    assert (await client.post(f"{B}/{kid}/reveal", headers=other)).status_code == 404
    assert (await client.delete(f"{B}/{kid}", headers=other)).status_code == 404


def test_any_random_string_works_as_encryption_key():
    old = settings.encryption_keys
    try:
        settings.encryption_keys = "kJ8f2Qx9LmN3pR7sT1vW5yZ0aB4cD6eG8hI2jK4lM6n="  # not necessarily a Fernet key
        assert crypto.decrypt(crypto.encrypt("abc12345")) == "abc12345"
        settings.encryption_keys = "plain-long-random-passphrase-from-render-generate"
        assert crypto.decrypt(crypto.encrypt("abc12345")) == "abc12345"
    finally:
        settings.encryption_keys = old
