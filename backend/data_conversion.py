# data conversion utilities for backend
from backend.schemas.data import CompanyInfo, PaginationInfo, TaskInfo, URLInfo


def convert_task_list_response(response: dict) -> list[TaskInfo]:
    """Convert the /init-task-list API response to a list of TaskInfo objects.

    Expected response structure:
        {
            "success": True,
            "data": {
                "data": {
                    "list": [ { task fields ... }, ... ]
                }
            }
        }
    """
    raw_list: list[dict] = response.get("data", {}).get("list", [])

    tasks: list[TaskInfo] = []
    for item in raw_list:
        task = TaskInfo(
            id=item["id"],
            task_name=item.get("task_name", ""),
            status=item.get("status", ""),
            priority=item.get("priority", ""),
            deadline=item.get("deadline", ""),
            total_companies=item.get("total_companies", 0),
            completed_companies=item.get("completed_companies", 0),
            task_type=item.get("task_type", ""),
            progress=item.get("progress", 0.0),
            # task_description is not provided by the task-list endpoint
            task_description=item.get("task_description", ""),
            # company details are not loaded at the list level
            companyInfos=[],
        )
        tasks.append(task)

    return tasks


def convert_pagination_response(response: dict) -> PaginationInfo:
    """Extract pagination info from the /init-task-list API response.

    Source pagination structure:
        response["data"]["data"]["pagination"] = {
            "total": 45,
            "page": 1,
            "page_size": 10,
            "total_pages": 5
        }
    """
    raw: dict = response.get("data", {}).get("pagination", {})

    return PaginationInfo(
        total_items=raw.get("total", 0),
        current_page=raw.get("page", 1),
        page_step=raw.get("page_size", 10),
        total_pages=raw.get("total_pages", 1),
    )


def convert_task_details(task: TaskInfo, response: dict) -> TaskInfo:
    """Convert task detail API response into a fully updated TaskInfo.

    Expected detail structure:
        {
            "data": {
                "id": 1969,
                "companies": [
                    {
                        "notes": "...",
                        "status": "...",
                        "entity_name": "...",
                        "completed_at": "...",
                        "current_step": "...",
                        "missing_reports": [],
                        "orbit_entity_id": "...",
                        "review_rejection_reason": "...",
                        "shared_notes": "...",
                        "name": "...",
                        "source_pages": [
                            {
                                "id": 1,
                                "page_url": "https://...",
                                "page_type": "REPORT",
                                "comment": "..."
                            }
                        ]
                    }
                ]
            }
        }
    """
    payload: dict = response.get("data", {})
    task_id = payload.get("id", task.id)
    task_description = payload.get("task_description", task.task_description)

    raw_companies: list[dict] = payload.get("companies", [])

    companies: list[CompanyInfo] = []
    for company in raw_companies:
        websites = company.get("website") or []
        website_pages = company.get("website_pages") or []
        raw_pages: list[dict] = company.get("source_pages", [])
        url_infos: list[URLInfo] = []

        if isinstance(websites, str):
            websites = [websites]
        if isinstance(website_pages, str):
            website_pages = [website_pages]

        for website in websites:
            url_infos.append(
                URLInfo(
                    id=None,
                    url=website,
                    type="WEBSITE",
                    comment=None,
                )
            )

        for website_page in website_pages:
            url_infos.append(
                URLInfo(
                    id=None,
                    url=website_page,
                    type="WEBSITE_PAGES",
                    comment=None,
                )
            )

        for page in raw_pages:
            page_url = page.get("page_url")
            page_type = page.get("page_type")
            if not page_url or not page_type:
                continue

            url_infos.append(
                URLInfo(
                    id=page.get("id"),
                    url=page_url,
                    type=page_type,
                    comment=page.get("comment") or None,
                )
            )

        companies.append(
            CompanyInfo(
                task_id=task_id,
                notes=company.get("notes", ""),
                status=company.get("status", ""),
                entity_name=company.get("entity_name", ""),
                completed_at=company.get("completed_at", ""),
                current_step=company.get("current_step", ""),
                missing_reports=company.get("missing_reports", []),
                orbit_entity_id=company.get("orbit_entity_id", ""),
                review_rejection_reason=company.get("review_rejection_reason") or "",
                shared_notes=company.get("shared_notes", ""),
                name=company.get("name", ""),
                urlInfos=url_infos,
            )
        )

    return task.model_copy(
        update={
            "task_description": task_description,
            "companyInfos": companies,
        }
    )
