import asyncio
from fastapi.testclient import TestClient
from server import app


def test_run_two_tasks():
    client = TestClient(app)
    r1 = client.post('/run', json={'input_text': '项目名称: demo-a\nA 需求'})
    r2 = client.post('/run', json={'input_text': '项目名称: demo-b\nB 需求'})
    t1 = r1.json()['task_id']
    t2 = r2.json()['task_id']
    for _ in range(240):
        s1 = client.get(f'/status/{t1}').json()
        s2 = client.get(f'/status/{t2}').json()
        if s1.get('status') == 'completed' and s2.get('status') == 'completed':
            return
        asyncio.sleep(0.5)
    assert False, 'two tasks did not complete in time'

