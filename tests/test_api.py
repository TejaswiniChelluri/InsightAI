from fastapi.testclient import TestClient
from main import app

def test_api_valid(monkeypatch):
    monkeypatch.delenv('GROQ_API_KEY',raising=False)
    with TestClient(app) as client:
        response=client.post('/ask',json={'question':'What is the total revenue?'})
        assert response.status_code==200
        assert response.json()['data'][0]['revenue']==1439200

def test_api_unsupported(monkeypatch):
    monkeypatch.delenv('GROQ_API_KEY',raising=False)
    with TestClient(app) as client:
        assert client.post('/ask',json={'question':'What is the weather?'}).status_code==422

def test_api_empty():
    with TestClient(app) as client:
        assert client.post('/ask',json={'question':''}).status_code==422
