import os
import unittest
import time
import psycopg
from fastapi.testclient import TestClient
from dotenv import load_dotenv

load_dotenv()
import main


class TestAccountIsolation(unittest.TestCase):
    """
    Automated regression tests for Account Data Isolation (Bug 1).
    Verifies that:
    1. Account creation and login establishes correct identity.
    2. User B cannot see User A's profile data.
    3. User B updating profile does not overwrite User A's data.
    4. Client-supplied user_id parameters are ignored; identity is derived solely from JWT.
    5. Unauthenticated requests are rejected with HTTP 401.
    6. Non-completed profiles return clean empty state without leaking existing records.
    """

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(main.app)
        cls.timestamp = int(time.time() * 1000)
        cls.user_a_email = f"alice_{cls.timestamp}@test-isolation.com"
        cls.user_b_email = f"bob_{cls.timestamp}@test-isolation.com"
        cls.officer_email = f"officer_{cls.timestamp}@test-isolation.com"
        cls.password = "TestPass123!"

        # Register User A (student)
        res_a = cls.client.post("/register", json={
            "email": cls.user_a_email,
            "password": cls.password,
            "role": "student"
        })
        assert res_a.status_code == 200, f"Registration A failed: {res_a.text}"

        # Register User B (student)
        res_b = cls.client.post("/register", json={
            "email": cls.user_b_email,
            "password": cls.password,
            "role": "student"
        })
        assert res_b.status_code == 200, f"Registration B failed: {res_b.text}"

        # Register Officer
        res_off = cls.client.post("/register", json={
            "email": cls.officer_email,
            "password": cls.password,
            "role": "officer"
        })
        assert res_off.status_code == 200, f"Registration Officer failed: {res_off.text}"

        # Login User A
        login_a = cls.client.post("/login", data={"username": cls.user_a_email, "password": cls.password})
        assert login_a.status_code == 200, f"Login A failed: {login_a.text}"
        cls.token_a = login_a.json()["access_token"]
        cls.headers_a = {"Authorization": f"Bearer {cls.token_a}"}

        # Login User B
        login_b = cls.client.post("/login", data={"username": cls.user_b_email, "password": cls.password})
        assert login_b.status_code == 200, f"Login B failed: {login_b.text}"
        cls.token_b = login_b.json()["access_token"]
        cls.headers_b = {"Authorization": f"Bearer {cls.token_b}"}

        # Login Officer
        login_off = cls.client.post("/login", data={"username": cls.officer_email, "password": cls.password})
        assert login_off.status_code == 200, f"Login Officer failed: {login_off.text}"
        cls.token_off = login_off.json()["access_token"]
        cls.headers_off = {"Authorization": f"Bearer {cls.token_off}"}

    @classmethod
    def tearDownClass(cls):
        # Clean up test accounts from database
        try:
            conn_gen = main.get_db_connection()
            conn = next(conn_gen)
            with conn.cursor() as cur:
                cur.execute("DELETE FROM users WHERE email LIKE %s", ("%@test-isolation.com",))
            conn.commit()
            try:
                next(conn_gen)
            except StopIteration:
                pass
        except Exception as e:
            print(f"Notice: Failed to clean up test users: {e}")

    def test_01_new_account_has_uncompleted_profile_and_no_data_leakage(self):
        """User A has not saved a profile yet. Verify clean empty profile state."""
        response = self.client.get("/profile/me", headers=self.headers_a)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["email"], self.user_a_email)
        self.assertFalse(data["profile_completed"])
        self.assertIsNone(data["full_name"])
        self.assertIsNone(data["course"])
        self.assertIsNone(data["cgpa"])
        self.assertIsNone(data["skills"])

    def test_02_user_a_creates_profile(self):
        """User A saves their profile details."""
        profile_data = {
            "full_name": "Alice Wonderland",
            "course": "B.Tech Computer Science",
            "tenth_percentage": 94.5,
            "twelfth_percentage": 92.0,
            "current_year": 4,
            "cgpa": 9.45,
            "skills": ["Python", "FastAPI", "PostgreSQL", "Docker"],
            "projects": "AI Placement System",
            "achievements": "Hackathon Winner 2025",
            "linkedin_url": "https://linkedin.com/in/alicew"
        }
        res_update = self.client.post("/profile/update", headers=self.headers_a, json=profile_data)
        self.assertEqual(res_update.status_code, 200)

        # Verify User A's profile is saved
        res_get = self.client.get("/profile/me", headers=self.headers_a)
        self.assertEqual(res_get.status_code, 200)
        profile_a = res_get.json()
        self.assertTrue(profile_a["profile_completed"])
        self.assertEqual(profile_a["full_name"], "Alice Wonderland")
        self.assertEqual(profile_a["course"], "B.Tech Computer Science")
        self.assertEqual(profile_a["cgpa"], 9.45)
        self.assertEqual(profile_a["skills"], ["Python", "FastAPI", "PostgreSQL", "Docker"])

    def test_03_user_b_does_not_see_user_a_profile(self):
        """User B accesses their profile. Must NOT receive User A's profile data."""
        res_b = self.client.get("/profile/me", headers=self.headers_b)
        self.assertEqual(res_b.status_code, 200)
        profile_b = res_b.json()
        self.assertEqual(profile_b["email"], self.user_b_email)
        self.assertFalse(profile_b["profile_completed"])
        # Ensure User A's details are NOT leaked to User B
        self.assertIsNone(profile_b["full_name"])
        self.assertNotEqual(profile_b["full_name"], "Alice Wonderland")
        self.assertIsNone(profile_b["course"])
        self.assertIsNone(profile_b["cgpa"])
        self.assertIsNone(profile_b["skills"])

    def test_04_user_b_updates_profile_without_affecting_user_a(self):
        """User B updates their profile. User A's profile must remain completely unchanged."""
        profile_b_data = {
            "full_name": "Bob Builder",
            "course": "B.Tech Mechanical Engineering",
            "tenth_percentage": 85.0,
            "twelfth_percentage": 88.0,
            "current_year": 3,
            "cgpa": 7.85,
            "skills": ["AutoCAD", "SolidWorks", "Python"],
            "projects": "Robotic Arm Design",
            "achievements": "Best Project Award",
            "linkedin_url": "https://linkedin.com/in/bobbuilder"
        }
        res_update_b = self.client.post("/profile/update", headers=self.headers_b, json=profile_b_data)
        self.assertEqual(res_update_b.status_code, 200)

        # Check User B's profile
        res_b = self.client.get("/profile/me", headers=self.headers_b)
        self.assertEqual(res_b.status_code, 200)
        profile_b = res_b.json()
        self.assertTrue(profile_b["profile_completed"])
        self.assertEqual(profile_b["full_name"], "Bob Builder")
        self.assertEqual(profile_b["course"], "B.Tech Mechanical Engineering")
        self.assertEqual(profile_b["cgpa"], 7.85)

        # Check User A's profile - must be untouched
        res_a = self.client.get("/profile/me", headers=self.headers_a)
        self.assertEqual(res_a.status_code, 200)
        profile_a = res_a.json()
        self.assertEqual(profile_a["email"], self.user_a_email)
        self.assertEqual(profile_a["full_name"], "Alice Wonderland")
        self.assertEqual(profile_a["course"], "B.Tech Computer Science")
        self.assertEqual(profile_a["cgpa"], 9.45)
        self.assertEqual(profile_a["skills"], ["Python", "FastAPI", "PostgreSQL", "Docker"])

    def test_05_client_supplied_user_id_is_strictly_ignored(self):
        """Attempting to spoof user_id query parameters does not grant access to another profile."""
        # User B queries /profile/me with user_id parameter aiming for User A
        res = self.client.get("/profile/me?user_id=1", headers=self.headers_b)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        # Identity must remain User B
        self.assertEqual(data["email"], self.user_b_email)
        self.assertEqual(data["full_name"], "Bob Builder")

        res_alias = self.client.get("/profile?user_id=1", headers=self.headers_b)
        self.assertEqual(res_alias.status_code, 200)
        data_alias = res_alias.json()
        self.assertEqual(data_alias["email"], self.user_b_email)

    def test_06_unauthenticated_request_is_rejected(self):
        """Calling /profile/me without a valid token must return HTTP 401."""
        res_no_auth = self.client.get("/profile/me")
        self.assertEqual(res_no_auth.status_code, 401)

        res_bad_token = self.client.get("/profile/me", headers={"Authorization": "Bearer invalid_token_12345"})
        self.assertEqual(res_bad_token.status_code, 401)

    def test_07_officer_cannot_update_student_profile(self):
        """Placement officers cannot create or overwrite student profiles."""
        res = self.client.post("/profile/update", headers=self.headers_off, json={
            "full_name": "Officer Smith"
        })
        self.assertEqual(res.status_code, 403)
        self.assertIn("Only students can create a profile", res.json()["detail"])


if __name__ == "__main__":
    unittest.main()
