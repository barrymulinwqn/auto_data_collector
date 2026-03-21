from fastapi import APIRouter, HTTPException
from backend.schemas.data import DataItem, DataItemCreate

router = APIRouter()

# In-memory store (replace with a real DB later)
_store: list[DataItem] = []
_id_counter = 1


@router.get("/", response_model=list[DataItem])
def list_data():
    return _store


@router.post("/", response_model=DataItem, status_code=201)
def create_data(item: DataItemCreate):
    global _id_counter
    new_item = DataItem(id=_id_counter, **item.model_dump())
    _store.append(new_item)
    _id_counter += 1
    return new_item


@router.get("/{item_id}", response_model=DataItem)
def get_data(item_id: int):
    for item in _store:
        if item.id == item_id:
            return item
    raise HTTPException(status_code=404, detail="Item not found")


@router.delete("/{item_id}", status_code=204)
def delete_data(item_id: int):
    global _store
    original_len = len(_store)
    _store = [item for item in _store if item.id != item_id]
    if len(_store) == original_len:
        raise HTTPException(status_code=404, detail="Item not found")
