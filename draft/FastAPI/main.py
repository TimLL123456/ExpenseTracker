# Run main.py
# cd "draft\FastAPI"; uv run uvicorn main:app --reload

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

app = FastAPI()

# --- Pydantic ---
class Item(BaseModel):
    text: str = None
    is_done: bool = False


# --- Declare Variables ---
favicon_path = "favicon.ico"
items = []


# --- Build API Endpoints ---
@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    return FileResponse(favicon_path)

@app.get("/")
def root():
    return {"message": "Welcome to FastAPI!"}

@app.get("/items", response_model=list[Item])
def read_item():
    return items

# With Pydantic BaseModel
# curl -X POST -H "Content-Type: application/json" -d '{"text":"apple"}' 'http://127.0.0.1:8000/items'
# Invoke-WebRequest -Uri 'http://127.0.0.1:8000/items' -Method POST -Headers @{ "Content-Type" = "application/json" } -Body '{"text":"apple"}'

# Without Pydantic BaseModel
# curl -X POST -H "Content-Type: application/json" 'http://127.0.0.1:8000/items?item=apple'
@app.post("/items")
def create_item(item: Item) -> list:
    items.append(item)
    return item

# curl -X GET -H "Content-Type: application/json" 'http://127.0.0.1:8000/items/0'
# Invoke-WebRequest -Uri 'http://127.0.0.1:8000/items/0' -Method GET -Headers @{ "Content-Type" = "application/json" }
@app.get("/items/{item_id}", response_model=Item)
def get_item(item_id: int) -> Item:
    if item_id < len(items):
        return items[item_id]
    else:
        raise HTTPException(status_code=404, detail="Item not found")