from sqlalchemy.orm import Session
from models.tool import Tool
from schemas.tool import ToolCreate

def get_tool(db: Session, tool_id: int):
    return db.query(Tool).filter(Tool.id == tool_id).first()

def get_tools(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Tool).offset(skip).limit(limit).all()

def create_tool(db: Session, tool: ToolCreate):
    db_tool = Tool(**tool.model_dump())
    db.add(db_tool)
    db.commit()
    db.refresh(db_tool)
    return db_tool

def search_tools(db: Session, query: str, limit: int = 100):
    search_term = f"%{query}%"
    return db.query(Tool).filter(
        Tool.name.ilike(search_term) | Tool.description.ilike(search_term)
    ).limit(limit).all()
