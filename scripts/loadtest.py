"""Locust 压测脚本 — 模拟 100 并发学生答题。

使用：
1. 先跑 python scripts/loadtest_seed.py
2. 启动 server: uvicorn app.main:app --port 8000 --workers 4
3. 跑压测：
   locust -f scripts/loadtest.py --users 100 --spawn-rate 10 --run-time 2m --headless --host http://localhost:8000
"""
import os
import random
from locust import HttpUser, task, between
from locust.exception import StopUser


CLASS_ID_ENV = "FUSHUA_STRESS_CLASS_ID"


class StudentUser(HttpUser):
    wait_time = between(0.5, 2.0)
    token = None
    class_id = None
    question_ids = []

    def on_start(self):
        idx = random.randint(0, 99)
        username = f"s_{idx}"
        r = self.client.post("/api/v1/auth/login", json={
            "username": username, "password": "stresspass",
        }, name="POST /auth/login")
        if r.status_code != 200:
            raise StopUser()
        self.token = r.json()["data"]["token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}

        cid = os.environ.get(CLASS_ID_ENV)
        if not cid:
            print(f"请先设置 {CLASS_ID_ENV} 环境变量为 loadtest_seed 输出的 class_id")
            raise StopUser()
        self.class_id = int(cid)

        r = self.client.get(
            f"/api/v1/questions?class_id={self.class_id}&limit=50",
            headers=self.headers, name="GET /questions"
        )
        if r.status_code == 200:
            self.question_ids = [q["id"] for q in r.json()["data"]]

    @task(5)
    def list_questions(self):
        self.client.get(
            f"/api/v1/questions?class_id={self.class_id}&limit=20",
            headers=self.headers, name="GET /questions"
        )

    @task(3)
    def submit_record(self):
        if not self.question_ids:
            return
        qid = random.choice(self.question_ids)
        self.client.post(
            "/api/v1/practice-records",
            headers=self.headers,
            json={
                "question_id": qid,
                "user_answer": random.choice(["A", "B", "C", "D"]),
                "is_correct": random.choice([True, False]),
            },
            name="POST /practice-records",
        )

    @task(2)
    def mistakes(self):
        self.client.get("/api/v1/practice-records/mistakes", headers=self.headers, name="GET /mistakes")

    @task(1)
    def me(self):
        self.client.get("/api/v1/users/me", headers=self.headers, name="GET /users/me")
