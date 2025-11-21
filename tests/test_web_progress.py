import asyncio
from fastapi.testclient import TestClient
from server import app


def test_run_and_poll_status():
    client = TestClient(app)
    r = client.post('/run', json={'input_text': '项目名称: demo\n测试端到端运行'})
    assert r.status_code == 200
    for _ in range(120):
        s = client.get('/status').json()
        if s.get('status') == 'completed':
            assert s['steps']['requirement_analysis']['status'] in ['completed','pending']
            assert s['steps']['development_execution']['status'] in ['completed','pending']
            return
        asyncio.sleep(0.5)
    assert False, 'workflow did not complete in time'

