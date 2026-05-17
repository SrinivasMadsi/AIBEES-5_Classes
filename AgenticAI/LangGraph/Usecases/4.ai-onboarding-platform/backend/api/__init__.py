from api.routes_submissions import router as submissions_router
from api.routes_validate import router as validate_router
from api.routes_review import router as review_router
from api.routes_data import router as data_router

__all__ = [
    "submissions_router",
    "validate_router",
    "review_router",
    "data_router",
]
