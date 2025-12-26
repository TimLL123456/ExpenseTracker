import os
import json
import datetime
from typing import List, Optional, Dict, Any

import requests
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from sqlalchemy import create_engine, Column, Integer, String, Float, Date, func, case
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.sql import and_


load_dotenv()

app = FastAPI(title="Expense Tracker API")

# Allow Streamlit to call this API (dev-friendly; restrict in production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# SQLite + FastAPI: allow usage across threads
DATABASE_URL = "sqlite:///./expenses.db"
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, nullable=False)
    type = Column(String, nullable=False)  # 'income' or 'expense'
    category = Column(String, nullable=False)
    description = Column(String, nullable=False)
    price = Column(Float, nullable=False)

class AssetTransaction(Base):
    __tablename__ = "asset_transactions"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, nullable=False)
    asset_type = Column(String, nullable=False)  # 'stock' or 'crypto'
    symbol = Column(String, nullable=False)
    name = Column(String)
    quantity = Column(Float, nullable=False)
    price = Column(Float, nullable=False)
    action = Column(String, nullable=False)  # 'buy' or 'sell'
    remarks = Column(String)

Base.metadata.create_all(bind=engine)


class InputText(BaseModel):
    text: str


class TransactionOut(BaseModel):
    id: int
    date: str  # YYYY-MM-DD
    type: str
    category: str
    description: str
    price: float

class AssetTransactionIn(BaseModel):
    date: str  # YYYY-MM-DD
    asset_type: str
    symbol: str
    name: Optional[str] = None
    quantity: float
    price: float
    action: str
    remarks: Optional[str] = None

class AssetTransactionOut(BaseModel):
    id: int
    date: str
    asset_type: str
    symbol: str
    name: Optional[str]
    quantity: float
    price: float
    action: str
    remarks: Optional[str]

class AssetHoldingOut(BaseModel):
    asset_type: str
    symbol: str
    name: Optional[str]
    net_quantity: float
    avg_buy_price: float


def extract_with_llm(text: str) -> Dict[str, Any]:
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        raise ValueError("DEEPSEEK_API_KEY not set")

    system_prompt = (
        "You are a transaction extractor. Respond ONLY with a valid JSON object. "
        "Do not include any explanations, markdown, or additional text."
    )

    today = datetime.date.today().strftime("%Y-%m-%d")
    user_prompt = f"""
Extract transaction details from this sentence: "{text}"

Use these keys: date (YYYY-MM-DD), type (income or expense), category, description, price (float).
If date is missing, use today's date: {today}.
"""

    r = requests.post(
        "https://api.deepseek.com/v1/chat/completions",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.2,
        },
        timeout=30,
    )

    if r.status_code != 200:
        raise ValueError("LLM API error: " + r.text)

    api_response = r.json()
    content = api_response["choices"][0]["message"]["content"]

    try:
        extracted = json.loads(content)
    except json.JSONDecodeError:
        raise ValueError(f"Invalid JSON from LLM: {content}")

    extracted.setdefault("date", today)

    if extracted.get("type") not in {"income", "expense"}:
        raise ValueError(f"Invalid type: {extracted.get('type')}")

    for k in ["date", "type", "category", "description", "price"]:
        if k not in extracted:
            raise ValueError(f"Missing key from LLM output: {k}")

    extracted["price"] = float(extracted["price"])
    return extracted


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/process")
def process_input(input: InputText):
    try:
        extracted = extract_with_llm(input.text)
        date_obj = datetime.datetime.strptime(extracted["date"], "%Y-%m-%d").date()

        db = SessionLocal()
        try:
            t = Transaction(
                date=date_obj,
                type=extracted["type"],
                category=extracted["category"],
                description=extracted["description"],
                price=float(extracted["price"]),
            )
            db.add(t)
            db.commit()
            db.refresh(t)
        finally:
            db.close()

        return {"status": "success", "id": t.id, "extracted": extracted}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/transactions", response_model=List[TransactionOut])
def get_transactions(
    type: Optional[str] = Query(None, description="Filter by type: income or expense"),
    category: Optional[str] = Query(None, description="Filter by category (partial match)"),
    date_from: Optional[str] = Query(None, description="Filter from date (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="Filter to date (YYYY-MM-DD)"),
):
    db = SessionLocal()
    try:
        query = db.query(Transaction)
        filters = []

        if type:
            filters.append(Transaction.type == type)
        if category:
            filters.append(Transaction.category.ilike(f"%{category}%"))
        if date_from:
            dfrom = datetime.datetime.strptime(date_from, "%Y-%m-%d").date()
            filters.append(Transaction.date >= dfrom)
        if date_to:
            dto = datetime.datetime.strptime(date_to, "%Y-%m-%d").date()
            filters.append(Transaction.date <= dto)

        if filters:
            query = query.filter(and_(*filters))

        rows = query.order_by(Transaction.date.desc(), Transaction.id.desc()).all()

        return [
            TransactionOut(
                id=r.id,
                date=r.date.strftime("%Y-%m-%d"),
                type=r.type,
                category=r.category,
                description=r.description,
                price=r.price,
            )
            for r in rows
        ]
    finally:
        db.close()

@app.post("/asset_transactions")
def add_asset_transaction(entry: AssetTransactionIn):
    try:
        date_obj = datetime.datetime.strptime(entry.date, "%Y-%m-%d").date()
        db = SessionLocal()
        t = AssetTransaction(
            date=date_obj,
            asset_type=entry.asset_type,
            symbol=entry.symbol.upper(),
            name=entry.name,
            quantity=entry.quantity,
            price=entry.price,
            action=entry.action,
            remarks=entry.remarks,
        )
        db.add(t)
        db.commit()
        db.refresh(t)
        return {"status": "success", "id": t.id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@app.get("/asset_transactions", response_model=List[AssetTransactionOut])
def get_asset_transactions(asset_type: Optional[str] = Query(None)):
    db = SessionLocal()
    try:
        query = db.query(AssetTransaction)
        if asset_type:
            query = query.filter(AssetTransaction.asset_type == asset_type)
        rows = query.order_by(AssetTransaction.date.desc(), AssetTransaction.id.desc()).all()
        return [
            AssetTransactionOut(
                id=r.id,
                date=r.date.strftime("%Y-%m-%d"),
                asset_type=r.asset_type,
                symbol=r.symbol,
                name=r.name,
                quantity=r.quantity,
                price=r.price,
                action=r.action,
                remarks=r.remarks,
            )
            for r in rows
        ]
    finally:
        db.close()

@app.get("/asset_holdings")
def get_asset_holdings(asset_type: Optional[str] = Query(None)):
    db = SessionLocal()
    try:
        query = db.query(
            AssetTransaction.asset_type,
            AssetTransaction.symbol,
            func.max(AssetTransaction.name).label('name'),
            func.sum(case((AssetTransaction.action == 'buy', AssetTransaction.quantity), else_=-AssetTransaction.quantity)).label('net_quantity'),
            func.sum(case((AssetTransaction.action == 'buy', AssetTransaction.quantity * AssetTransaction.price), else_=0)).label('total_buy_cost'),
            func.sum(case((AssetTransaction.action == 'buy', AssetTransaction.quantity), else_=0)).label('total_buy_qty')
        ).group_by(AssetTransaction.asset_type, AssetTransaction.symbol)
        if asset_type:
            query = query.filter(AssetTransaction.asset_type == asset_type)
        query = query.having(func.sum(case((AssetTransaction.action == 'buy', AssetTransaction.quantity), else_=-AssetTransaction.quantity)) > 0)
        rows = query.all()
        return [
            {
                'asset_type': r.asset_type,
                'symbol': r.symbol,
                'name': r.name,
                'net_quantity': r.net_quantity,
                'avg_buy_price': r.total_buy_cost / r.total_buy_qty if r.total_buy_qty > 0 else 0.0
            }
            for r in rows
        ]
    finally:
        db.close()