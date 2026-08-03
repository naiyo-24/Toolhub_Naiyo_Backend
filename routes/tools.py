from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from schemas.tool import ToolCreate, ToolResponse
from crud import tool as crud_tool
from db import get_db

router = APIRouter(
    prefix="/tools",
    tags=["tools"]
)

@router.post("/", response_model=ToolResponse)
def create_tool(tool: ToolCreate, db: Session = Depends(get_db)):
    return crud_tool.create_tool(db=db, tool=tool)

@router.get("/", response_model=List[ToolResponse])
def read_tools(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud_tool.get_tools(db=db, skip=skip, limit=limit)

@router.get("/search", response_model=List[ToolResponse])
def search_tools(q: str, limit: int = 100, db: Session = Depends(get_db)):
    if not q:
        return []
    return crud_tool.search_tools(db=db, query=q, limit=limit)

@router.get("/{tool_id}", response_model=ToolResponse)
def read_tool(tool_id: int, db: Session = Depends(get_db)):
    db_tool = crud_tool.get_tool(db=db, tool_id=tool_id)
    if db_tool is None:
        raise HTTPException(status_code=404, detail="Tool not found")
    return db_tool
