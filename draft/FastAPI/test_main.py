from fastapi.testclient import TestClient

from .main import app

client = TestClient(app)

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to FastAPI!"}

def test_create_item_apple():
    data = {"text": "apple"}
    response = client.post("/items", json=data)
    assert response.status_code == 200
    assert response.json() == [['text', "apple"], ['is_done', False]]

def test_create_item_banana():
    data = {"text": "banana"}
    response = client.post("/items", json=data)
    assert response.status_code == 200
    assert response.json() == [['text', "banana"], ['is_done', False]]

def test_read_item():
    response = client.get("/items")
    assert response.status_code == 200
    assert response.json() == [{'text': "apple", 'is_done': False}, {'text': "banana", 'is_done': False}]

def test_read_first_item():
    response = client.get("/items/0")
    assert response.status_code == 200
    assert response.json() == {'text': "apple", 'is_done': False}

def test_read_last_item():
    response = client.get("/items/-1")
    assert response.status_code == 200
    assert response.json() == {'text': "banana", 'is_done': False}

