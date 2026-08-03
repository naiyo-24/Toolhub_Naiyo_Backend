from fastapi import APIRouter, Request

router = APIRouter()

# Dummy GET endpoints so fetchList doesn't crash
@router.get("/{endpoint:path}")
async def get_productivity_items(endpoint: str):
    return []

# Dummy POST endpoints to accept submissions without saving to DB
@router.post("/{endpoint:path}")
async def post_productivity_items(endpoint: str, request: Request):
    data = await request.json()
    return {
        "Message": f"Successfully processed {endpoint}.",
        "Data": data
    }
