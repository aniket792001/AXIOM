"""Comprehensive End-to-End Verification for Customer Database Persistence & SCORE Engine."""

import json
import time
import urllib.request

BASE = "http://127.0.0.1:8000"


def post_json(path, data):
    req = urllib.request.Request(
        f"{BASE}{path}",
        data=json.dumps(data).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))


def get_json(path):
    req = urllib.request.Request(f"{BASE}{path}")
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))


def main():
    print("=== 1. VERIFYING AUTH LOGIN PERSISTENCE ===")
    test_user_email = f"customer_{int(time.time())}@enterprise.com"
    login_res = post_json("/api/v1/auth/login", {"email": test_user_email, "role": "analyst"})
    print("Login successful for:", login_res["user"]["email"], "| Token:", login_res["token"][:16])

    users_res = get_json("/api/v1/auth/users")
    print("Database Total Users:", users_res["total"])
    assert any(u["email"] == test_user_email for u in users_res["users"]), "User not persisted to DB!"
    print("[OK] Customer account successfully persisted to SQLite database (users table)!")

    print("\n=== 2. VERIFYING DOCUMENT INGESTION INTO SQLITE & VECTOR STORE ===")
    boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
    parts = [
        f"--{boundary}\r\nContent-Disposition: form-data; name=\"tenant_id\"\r\n\r\ndefault_tenant\r\n",
        f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"candidate_profile.txt\"\r\nContent-Type: text/plain\r\n\r\nAlex Morgan - Senior Cloud & AI Engineer\nTechnical Skills: Python, TypeScript, Go, Kubernetes, AWS, FastAPI, React, SQL\nExperience: 5 years building resilient microservices and production RAG pipelines.\r\n",
        f"--{boundary}--\r\n",
    ]
    body = "".join(parts).encode("utf-8")

    req_upload = urllib.request.Request(
        f"{BASE}/api/v1/ingest/file",
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
    )
    with urllib.request.urlopen(req_upload) as resp:
        upload_res = json.loads(resp.read().decode("utf-8"))
    print("Upload Result:", upload_res)
    assert upload_res["status"] == "success"
    print("[OK] Document parsed and indexed!")

    print("\n=== 3. VERIFYING STREAMING QUERY & NON-EMPTY GENERATION ===")
    stream_session = f"session_e2e_{int(time.time())}"
    query_payload = {
        "query": "Check skills and experience in candidate_profile.txt",
        "tenant_id": "default_tenant",
        "session_id": stream_session,
        "user_id": test_user_email,
    }

    req_stream = urllib.request.Request(
        f"{BASE}/api/v1/query/stream",
        data=json.dumps(query_payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )

    events = []
    with urllib.request.urlopen(req_stream) as resp:
        raw_stream = resp.read().decode("utf-8")
        for block in raw_stream.split("\n\n"):
            if not block.strip():
                continue
            ev = "message"
            dt = ""
            for line in block.split("\n"):
                if line.startswith("event:"):
                    ev = line.replace("event:", "").strip()
                elif line.startswith("data:"):
                    dt = line.replace("data:", "").strip()
            if dt:
                events.append((ev, dt))

    event_types = set(e[0] for e in events)
    print("Received SSE Event Types:", event_types)
    tokens = [json.loads(e[1])["token"] for e in events if e[0] == "token"]
    print(f"Streamed {len(tokens)} token words")

    done_event = next((e for e in events if e[0] == "done"), None)
    assert done_event is not None, "Missing SSE 'done' event!"
    final_gen = json.loads(done_event[1]).get("final_generation", "")
    print("Final Generation Preview:\n", final_gen)
    assert len(final_gen) > 10, "Generation was empty!"
    assert any(k in final_gen.lower() for k in ["python", "skills", "cloud", "engineer", "verified"]), "Key skills missing!"
    print("[OK] SCORE Engine produced verified, non-empty answer!")

    print("\n=== 4. VERIFYING DATABASE THREAD & QUERY PERSISTENCE ===")
    threads = get_json("/api/v1/sessions?tenant_id=default_tenant")
    matching_thread = next((t for t in threads if t["id"] == stream_session), None)
    assert matching_thread is not None, f"Session thread {stream_session} not found in database!"
    print("Found thread in DB:", matching_thread)

    history = get_json(f"/api/v1/sessions/{stream_session}/history")
    print(f"Session History has {len(history)} record(s)")
    assert len(history) >= 1, "History record not saved!"
    latest_rec = history[0]
    print("Latest Query in DB:", latest_rec["query"])
    print("Latest Generation in DB:", latest_rec["generation"][:120])
    print("Citations Count in DB:", len(latest_rec["citations"]))
    print("Hallucination Status in DB:", latest_rec["hallucination_status"])

    print("\n=== 5. VERIFYING AUDIT LOG ENDPOINT ===")
    audit_log = get_json("/api/v1/history/audit?tenant_id=default_tenant")
    print("Audit Log Total Records in DB:", audit_log["total"])
    assert audit_log["total"] >= 1, "No audit records returned!"

    print("\n>>> ALL 5 END-TO-END PERSISTENCE & GENERATION CHECKS PASSED WITH 100% SUCCESS! <<<")


if __name__ == "__main__":
    main()
