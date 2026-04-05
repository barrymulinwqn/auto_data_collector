from pydantic import BaseModel


class DataItemCreate(BaseModel):
    name: str
    source: str
    value: str | None = None


class DataItem(DataItemCreate):
    id: int

    model_config = {"from_attributes": True}


class URLInfo(BaseModel):
    id: int | None = None
    url: str
    type: str
    comment: str | None = None


class CompanyInfo(BaseModel):
    task_id: int
    notes: str
    status: str
    entity_name: str
    completed_at: str
    current_step: str
    missing_reports: list
    orbit_entity_id: str
    review_rejection_reason: str
    shared_notes: str
    name: str
    urlInfos: list[URLInfo]


class TaskInfo(BaseModel):
    id: int
    task_name: str
    status: str
    priority: str
    deadline: str
    total_companies: int
    completed_companies: int
    task_type: str
    progress: float
    task_description: str
    companyInfos: list[CompanyInfo]


class PaginationInfo(BaseModel):
    total_items: int
    current_page: int
    page_step: int
    total_pages: int
