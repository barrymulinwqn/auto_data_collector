# data conversion utilities for backend
from backend.schemas.data import PaginationInfo, TaskInfo


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
    raw: dict = response.get("data", {}).get("data", {}).get("pagination", {})

    return PaginationInfo(
        total_items=raw.get("total", 0),
        current_page=raw.get("page", 1),
        page_step=raw.get("page_size", 10),
        total_pages=raw.get("total_pages", 1),
    )
