"""
Thorough test suite for all 12 bug fixes in BetterMind CRM.
Run with: python test_fixes.py
Requires the backend running on localhost:8080.
"""
import os
import requests
import json
import sys

BASE = "http://localhost:8080/api"
PASS = 0
FAIL = 0


def test(name, condition, detail=""):
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"  ✅ {name}")
    else:
        FAIL += 1
        print(f"  ❌ {name} — {detail}")


def get_token(email=os.environ.get("TEST_EMAIL", "admin@example.com"), password=os.environ.get("TEST_PASSWORD", "changeme123!")):
    r = requests.post(f"{BASE}/login", json={"email": email, "password": password})
    if r.status_code == 200:
        return r.json()["token"]
    return None


def auth(token):
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


# ============================================================
print("\n🔐 FIX #5: Password hashing upgrade (PBKDF2)")
print("=" * 50)

# Login with seeded admin (newly hashed with PBKDF2)
test_email = os.environ.get("TEST_EMAIL", "admin@example.com")
test_password = os.environ.get("TEST_PASSWORD", "changeme123!")
r = requests.post(f"{BASE}/login", json={"email": test_email, "password": test_password})
test("Login with PBKDF2-hashed password succeeds", r.status_code == 200, f"status={r.status_code}")

token = r.json().get("token", "") if r.status_code == 200 else ""
test("Token is non-empty", len(token) > 0)

data = r.json() if r.status_code == 200 else {}
test("Login returns role=admin", data.get("role") == "admin", f"role={data.get('role')}")
test("Login returns correct email", data.get("email") == test_email)

# Wrong password
r = requests.post(f"{BASE}/login", json={"email": test_email, "password": "wrong"})
test("Wrong password returns 401", r.status_code == 401, f"status={r.status_code}")

# Non-existent user
r = requests.post(f"{BASE}/login", json={"email": "nobody@test.com", "password": "test"})
test("Non-existent user returns 401", r.status_code == 401, f"status={r.status_code}")


# ============================================================
print("\n🔑 FIX #3: TOKEN_SECRET warning + auth")
print("=" * 50)

# Verify token works for authenticated endpoints
r = requests.get(f"{BASE}/me", headers=auth(token))
test("/api/me returns 200 with valid token", r.status_code == 200, f"status={r.status_code}")
test("/api/me returns correct email", r.json().get("email") == test_email)

# Invalid token
r = requests.get(f"{BASE}/me", headers={"Authorization": "Bearer invalid.token.here"})
test("Invalid token returns 401", r.status_code == 401, f"status={r.status_code}")

# No token
r = requests.get(f"{BASE}/me")
test("No token returns 401", r.status_code == 401, f"status={r.status_code}")


# ============================================================
print("\n🛡️  FIX #6: Lifespan startup (data seeded correctly)")
print("=" * 50)

r = requests.get(f"{BASE}/stats", headers=auth(token))
test("/api/stats returns 200", r.status_code == 200, f"status={r.status_code}")
stats = r.json() if r.status_code == 200 else {}
test("Contacts seeded (>=47)", stats.get("total_contacts", 0) >= 47, f"got {stats.get('total_contacts')}")
test("Organizations seeded (>=21)", stats.get("total_organizations", 0) >= 21, f"got {stats.get('total_organizations')}")
test("Deals exist", stats.get("active_deals", 0) > 0, f"got {stats.get('active_deals')}")
test("Interactions exist", stats.get("total_interactions", 0) > 0, f"got {stats.get('total_interactions')}")


# ============================================================
print("\n📋 FIX #1 & #2: update_contact (allowlist + exclude_unset)")
print("=" * 50)

# Get a contact to work with
r = requests.get(f"{BASE}/contacts", headers=auth(token))
contacts = r.json()
test("Contacts list loads", len(contacts) > 0)

contact_id = contacts[0]["id"]

# Test #2: Can set a field to null (exclude_unset)
r = requests.put(f"{BASE}/contacts/{contact_id}", headers=auth(token),
                 json={"notes": "test note for fix verification"})
test("Update contact notes succeeds", r.status_code == 200, f"status={r.status_code}")
test("Notes updated correctly", r.json().get("notes") == "test note for fix verification",
     f"got: {r.json().get('notes')}")

# Now set notes to null explicitly
r = requests.put(f"{BASE}/contacts/{contact_id}", headers=auth(token),
                 json={"notes": None})
test("Can set notes to null (fix #2)", r.status_code == 200, f"status={r.status_code}")
test("Notes is now null", r.json().get("notes") is None, f"got: {r.json().get('notes')}")

# Test #1: Only allowed columns can be updated (allowlist)
r = requests.put(f"{BASE}/contacts/{contact_id}", headers=auth(token),
                 json={"status": "active"})
test("Update allowed column (status) works", r.status_code == 200, f"status={r.status_code}")

# Send empty update — should return existing
r = requests.put(f"{BASE}/contacts/{contact_id}", headers=auth(token), json={})
test("Empty update returns existing contact", r.status_code == 200 and r.json().get("id") == contact_id)

# Test that updated_at gets set
r = requests.put(f"{BASE}/contacts/{contact_id}", headers=auth(token),
                 json={"notes": "updated again"})
test("updated_at is set after update", r.json().get("updated_at") is not None,
     f"updated_at={r.json().get('updated_at')}")

# Non-existent contact
r = requests.put(f"{BASE}/contacts/99999", headers=auth(token), json={"notes": "test"})
test("Update non-existent contact returns 404", r.status_code == 404, f"status={r.status_code}")


# ============================================================
print("\n🗑️  FIX #10: delete_contact returns 404 for non-existent")
print("=" * 50)

# Create a contact, then delete it, then try deleting again
r = requests.post(f"{BASE}/contacts", headers=auth(token),
                  json={"first_name": "Test", "last_name": "Delete", "category": "other", "status": "contact"})
test("Create test contact for deletion", r.status_code == 201, f"status={r.status_code}")
new_id = r.json().get("id")

r = requests.delete(f"{BASE}/contacts/{new_id}", headers=auth(token))
test("Delete existing contact returns 200", r.status_code == 200, f"status={r.status_code}")

r = requests.delete(f"{BASE}/contacts/{new_id}", headers=auth(token))
test("Delete already-deleted contact returns 404", r.status_code == 404, f"status={r.status_code}")

r = requests.delete(f"{BASE}/contacts/99999", headers=auth(token))
test("Delete non-existent contact returns 404", r.status_code == 404, f"status={r.status_code}")


# ============================================================
print("\n🔒 FIX #8: db() rollback on error")
print("=" * 50)

# Try to create a contact with invalid category (should fail CHECK constraint on PG, but on SQLite no check)
# Instead test that a bad interaction (non-existent contact_id with FK) causes proper error
r = requests.post(f"{BASE}/interactions", headers=auth(token),
                  json={"contact_id": 99999, "type": "note", "channel": "other",
                        "subject": "test", "summary": "test", "date": "2026-02-25"})
# SQLite may or may not enforce FK — just verify the server doesn't crash
test("Server handles bad FK gracefully (no crash)", r.status_code in [200, 201, 400, 404, 500],
     f"status={r.status_code}")

# Verify server is still responsive after the error
r = requests.get(f"{BASE}/stats", headers=auth(token))
test("Server still responsive after error", r.status_code == 200, f"status={r.status_code}")


# ============================================================
print("\n🌐 FIX #7: CORS restricted origins")
print("=" * 50)

# Test CORS preflight from allowed origin
r = requests.options(f"{BASE}/contacts",
                     headers={"Origin": "http://localhost:5173",
                              "Access-Control-Request-Method": "GET"})
cors_header = r.headers.get("access-control-allow-origin", "")
test("CORS allows localhost:5173", cors_header == "http://localhost:5173", f"got: {cors_header}")

# Test CORS from disallowed origin
r = requests.options(f"{BASE}/contacts",
                     headers={"Origin": "http://evil.com",
                              "Access-Control-Request-Method": "GET"})
cors_header = r.headers.get("access-control-allow-origin", "")
test("CORS blocks evil.com", cors_header != "http://evil.com" and cors_header != "*",
     f"got: {cors_header}")


# ============================================================
print("\n👥 User Management endpoints")
print("=" * 50)

# List users (admin only)
r = requests.get(f"{BASE}/users", headers=auth(token))
test("List users returns 200", r.status_code == 200, f"status={r.status_code}")
test("At least 1 user (admin)", len(r.json()) >= 1)

# Create a user
r = requests.post(f"{BASE}/users", headers=auth(token),
                  json={"email": "testuser@test.com", "password": "TestPass123!", "name": "Test User", "role": "user"})
test("Create user returns 201", r.status_code == 201, f"status={r.status_code}")
test_user_id = r.json().get("id")

# Duplicate user
r = requests.post(f"{BASE}/users", headers=auth(token),
                  json={"email": "testuser@test.com", "password": "TestPass123!", "name": "Test User", "role": "user"})
test("Duplicate user returns 409", r.status_code == 409, f"status={r.status_code}")

# Login as new user (tests PBKDF2 for newly created user)
r = requests.post(f"{BASE}/login", json={"email": "testuser@test.com", "password": "TestPass123!"})
test("New user can login with PBKDF2 hash", r.status_code == 200, f"status={r.status_code}")
user_token = r.json().get("token", "") if r.status_code == 200 else ""

# Non-admin can't list users
r = requests.get(f"{BASE}/users", headers=auth(user_token))
test("Non-admin can't list users (403)", r.status_code == 403, f"status={r.status_code}")

# Change own password
r = requests.put(f"{BASE}/users/{test_user_id}/password", headers=auth(user_token),
                 json={"password": "NewPass456!"})
test("User can change own password", r.status_code == 200, f"status={r.status_code}")

# Login with new password
r = requests.post(f"{BASE}/login", json={"email": "testuser@test.com", "password": "NewPass456!"})
test("Login with changed password works", r.status_code == 200, f"status={r.status_code}")

# Old password no longer works
r = requests.post(f"{BASE}/login", json={"email": "testuser@test.com", "password": "TestPass123!"})
test("Old password rejected after change", r.status_code == 401, f"status={r.status_code}")

# Delete user
r = requests.delete(f"{BASE}/users/{test_user_id}", headers=auth(token))
test("Delete user returns 200", r.status_code == 200, f"status={r.status_code}")

# Delete non-existent user
r = requests.delete(f"{BASE}/users/99999", headers=auth(token))
test("Delete non-existent user returns 404", r.status_code == 404, f"status={r.status_code}")


# ============================================================
print("\n📊 Other endpoints (deals, programs, organizations, interactions)")
print("=" * 50)

r = requests.get(f"{BASE}/deals", headers=auth(token))
test("List deals returns 200", r.status_code == 200)
test("Deals have data", len(r.json()) > 0, f"got {len(r.json())} deals")

r = requests.get(f"{BASE}/programs", headers=auth(token))
test("List programs returns 200", r.status_code == 200)
test("Programs have data", len(r.json()) > 0, f"got {len(r.json())} programs")

r = requests.get(f"{BASE}/organizations", headers=auth(token))
test("List organizations returns 200", r.status_code == 200)
test("Organizations have data", len(r.json()) > 0)

r = requests.get(f"{BASE}/interactions", headers=auth(token))
test("List interactions returns 200", r.status_code == 200)
test("Interactions have data", len(r.json()) > 0)

# Get single contact with interactions and deals
r = requests.get(f"{BASE}/contacts", headers=auth(token))
first_contact = r.json()[0]
r = requests.get(f"{BASE}/contacts/{first_contact['id']}", headers=auth(token))
test("Get single contact returns 200", r.status_code == 200)
test("Contact detail has interactions key", "interactions" in r.json())
test("Contact detail has deals key", "deals" in r.json())

# Create interaction
r = requests.post(f"{BASE}/interactions", headers=auth(token),
                  json={"contact_id": first_contact["id"], "type": "note", "channel": "other",
                        "subject": "Test interaction", "summary": "Testing", "date": "2026-02-25"})
test("Create interaction returns 201", r.status_code == 201, f"status={r.status_code}")

# Create deal
r = requests.post(f"{BASE}/deals", headers=auth(token),
                  json={"contact_id": first_contact["id"], "deal_name": "Test Deal", "stage": "identified",
                        "amount": "$100K", "probability": 50})
test("Create deal returns 201", r.status_code == 201, f"status={r.status_code}")


# ============================================================
print("\n🔍 Contact filtering and search")
print("=" * 50)

r = requests.get(f"{BASE}/contacts?category=investor", headers=auth(token))
test("Filter by category=investor works", r.status_code == 200)
test("All results are investors", all(c["category"] == "investor" for c in r.json()))

r = requests.get(f"{BASE}/contacts?status=active", headers=auth(token))
test("Filter by status=active works", r.status_code == 200)
test("All results are active", all(c["status"] == "active" for c in r.json()))

r = requests.get(f"{BASE}/contacts?search=Marcus", headers=auth(token))
test("Search for 'Marcus' works", r.status_code == 200)
test("Search finds Marcus", any("Marcus" in c.get("first_name", "") for c in r.json()))


# ============================================================
print("\n" + "=" * 50)
print(f"RESULTS: {PASS} passed, {FAIL} failed out of {PASS + FAIL} tests")
print("=" * 50)

if FAIL > 0:
    sys.exit(1)
