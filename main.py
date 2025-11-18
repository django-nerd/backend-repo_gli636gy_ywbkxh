import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from bson import ObjectId

from database import db, create_document, get_documents
from schemas import Product

app = FastAPI(title="Pet Pantry API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {"message": "Pet Pantry Backend is running"}


# Helper to convert Mongo docs
class ProductOut(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    price: float
    category: str
    in_stock: bool
    image_url: Optional[str] = None
    rating: Optional[float] = 4.5
    brand: Optional[str] = None
    weight: Optional[str] = None


@app.get("/api/products", response_model=List[ProductOut])
def list_products():
    try:
        docs = get_documents("product")
        items = []
        for d in docs:
            d_id = str(d.get("_id")) if d.get("_id") else None
            items.append(
                ProductOut(
                    id=d_id,
                    title=d.get("title"),
                    description=d.get("description"),
                    price=float(d.get("price", 0)),
                    category=d.get("category", "Food"),
                    in_stock=bool(d.get("in_stock", True)),
                    image_url=d.get("image_url"),
                    rating=float(d.get("rating", 4.5)) if d.get("rating") is not None else 4.5,
                    brand=d.get("brand"),
                    weight=d.get("weight"),
                )
            )
        # Seed some demo items if empty
        if not items:
            seed = [
                {
                    "title": "Premium Dry Dog Food - Chicken",
                    "description": "High-protein kibble with vitamins and minerals.",
                    "price": 29.99,
                    "category": "Dog",
                    "in_stock": True,
                    "image_url": "https://images.unsplash.com/photo-1543466835-00a7907e9de1?w=800&q=80&auto=format&fit=crop",
                    "rating": 4.7,
                    "brand": "Pawsome",
                    "weight": "5 lb",
                },
                {
                    "title": "Wet Cat Food - Salmon",
                    "description": "Grain-free recipe with real salmon.",
                    "price": 19.49,
                    "category": "Cat",
                    "in_stock": True,
                    "image_url": "https://images.unsplash.com/photo-1596495578065-8a35f2a88f1b?w=800&q=80&auto=format&fit=crop",
                    "rating": 4.6,
                    "brand": "WhiskerDelight",
                    "weight": "12 x 3 oz",
                },
                {
                    "title": "Puppy Starter Pack",
                    "description": "Balanced nutrition for growing pups.",
                    "price": 34.99,
                    "category": "Dog",
                    "in_stock": True,
                    "image_url": "https://images.unsplash.com/photo-1558944351-c0a92c12f44e?w=800&q=80&auto=format&fit=crop",
                    "rating": 4.8,
                    "brand": "HappyTails",
                    "weight": "8 lb",
                },
                {
                    "title": "Adult Cat Kibble - Turkey",
                    "description": "Complete nutrition for adult cats.",
                    "price": 22.99,
                    "category": "Cat",
                    "in_stock": True,
                    "image_url": "https://images.unsplash.com/photo-1592194996308-7b43878e84a9?w=800&q=80&auto=format&fit=crop",
                    "rating": 4.4,
                    "brand": "MeowMunch",
                    "weight": "4 lb",
                },
            ]
            for s in seed:
                create_document("product", s)
            docs = get_documents("product")
            items = []
            for d in docs:
                items.append(
                    ProductOut(
                        id=str(d.get("_id")),
                        title=d.get("title"),
                        description=d.get("description"),
                        price=float(d.get("price", 0)),
                        category=d.get("category", "Food"),
                        in_stock=bool(d.get("in_stock", True)),
                        image_url=d.get("image_url"),
                        rating=float(d.get("rating", 4.5)) if d.get("rating") is not None else 4.5,
                        brand=d.get("brand"),
                        weight=d.get("weight"),
                    )
                )
        return items
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class CartItem(BaseModel):
    product_id: str
    quantity: int = 1


@app.post("/api/checkout")
def checkout(items: List[CartItem]):
    if not items:
        raise HTTPException(status_code=400, detail="Cart is empty")
    # Dummy success response (payment integration can be added later)
    total = 0.0
    # We don't trust client-sent prices; we re-fetch from DB
    id_to_qty = {i.product_id: i.quantity for i in items}
    docs = get_documents("product", {"_id": {"$in": [ObjectId(pid) for pid in id_to_qty.keys()]}})
    for d in docs:
        qty = id_to_qty.get(str(d.get("_id")), 1)
        total += float(d.get("price", 0)) * qty
    return {"status": "success", "total": round(total, 2)}


@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }

    try:
        from database import db as _db
        if _db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = _db.name if hasattr(_db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                collections = _db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    import os as _os
    response["database_url"] = "✅ Set" if _os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if _os.getenv("DATABASE_NAME") else "❌ Not Set"
    return response


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
