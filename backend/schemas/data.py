from pydantic import BaseModel


class DataItemCreate(BaseModel):
    name: str
    source: str
    value: str | None = None


class DataItem(DataItemCreate):
    id: int

    model_config = {"from_attributes": True}
