from fastapi import APIRouter, HTTPException, Depends
from typing import List
from models import TodoCreate, TodoUpdate, TodoResponse
import database
from security import get_current_user

router = APIRouter(prefix="/todos", tags=["Todos"])


@router.post("/", status_code=201, response_model=TodoResponse)
async def create_todo(todo: TodoCreate, current_user: dict = Depends(get_current_user)):
    result = database.create_todo(todo.title, todo.description, todo.completed or False)
    return result


@router.get("/", response_model=List[TodoResponse])
async def get_all_todos(current_user: dict = Depends(get_current_user)):
    return database.get_all_todos()


@router.get("/{todo_id}", response_model=TodoResponse)
async def get_todo(todo_id: int, current_user: dict = Depends(get_current_user)):
    todo = database.get_todo_by_id(todo_id)
    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found")
    return todo


@router.put("/{todo_id}", response_model=TodoResponse)
async def update_todo(todo_id: int, todo: TodoUpdate, current_user: dict = Depends(get_current_user)):
    result = database.update_todo(todo_id, todo.title, todo.description, todo.completed)
    if not result:
        raise HTTPException(status_code=404, detail="Todo not found")
    return result


@router.delete("/{todo_id}")
async def delete_todo(todo_id: int, current_user: dict = Depends(get_current_user)):
    success = database.delete_todo(todo_id)
    if not success:
        raise HTTPException(status_code=404, detail="Todo not found")
    return {"message": "Deleted"}
