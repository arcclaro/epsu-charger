"""
Battery Test Bench - Recipe Management API
Version: 1.0.1

Changelog:
v1.0.1 (2026-02-12): Initial recipe management endpoints
"""

from fastapi import APIRouter, HTTPException
from typing import List
from models.recipe import Recipe, RecipeCreate, RecipeUpdate
import aiosqlite
from config import settings
import json
from datetime import datetime

router = APIRouter()


@router.get("/", response_model=List[Recipe])
async def get_all_recipes():
    """Get all recipes"""
    async with aiosqlite.connect(settings.SQLITE_DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM recipes ORDER BY name") as cursor:
            rows = await cursor.fetchall()
            recipes = []
            for row in rows:
                recipes.append(Recipe(
                    id=row['id'],
                    name=row['name'],
                    description=row['description'],
                    steps=json.loads(row['steps']),
                    created_at=datetime.fromisoformat(row['created_at']),
                    updated_at=datetime.fromisoformat(row['updated_at'])
                ))
            return recipes


@router.get("/{recipe_id}", response_model=Recipe)
async def get_recipe(recipe_id: int):
    """Get a specific recipe"""
    async with aiosqlite.connect(settings.SQLITE_DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM recipes WHERE id = ?", (recipe_id,)) as cursor:
            row = await cursor.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail=f"Recipe {recipe_id} not found")

            return Recipe(
                id=row['id'],
                name=row['name'],
                description=row['description'],
                steps=json.loads(row['steps']),
                created_at=datetime.fromisoformat(row['created_at']),
                updated_at=datetime.fromisoformat(row['updated_at'])
            )


@router.post("/", response_model=Recipe)
async def create_recipe(recipe: RecipeCreate):
    """Create a new recipe"""
    async with aiosqlite.connect(settings.SQLITE_DB_PATH) as db:
        # Check for duplicate name
        async with db.execute("SELECT id FROM recipes WHERE name = ?", (recipe.name,)) as cursor:
            if await cursor.fetchone():
                raise HTTPException(status_code=400, detail=f"Recipe '{recipe.name}' already exists")

        # Insert new recipe
        steps_json = json.dumps([step.model_dump() for step in recipe.steps])
        cursor = await db.execute(
            "INSERT INTO recipes (name, description, steps) VALUES (?, ?, ?)",
            (recipe.name, recipe.description, steps_json)
        )
        await db.commit()

        recipe_id = cursor.lastrowid

        # Fetch and return the created recipe
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM recipes WHERE id = ?", (recipe_id,)) as cursor:
            row = await cursor.fetchone()
            return Recipe(
                id=row['id'],
                name=row['name'],
                description=row['description'],
                steps=json.loads(row['steps']),
                created_at=datetime.fromisoformat(row['created_at']),
                updated_at=datetime.fromisoformat(row['updated_at'])
            )


@router.put("/{recipe_id}", response_model=Recipe)
async def update_recipe(recipe_id: int, recipe: RecipeUpdate):
    """Update an existing recipe"""
    async with aiosqlite.connect(settings.SQLITE_DB_PATH) as db:
        # Check if recipe exists
        async with db.execute("SELECT id FROM recipes WHERE id = ?", (recipe_id,)) as cursor:
            if not await cursor.fetchone():
                raise HTTPException(status_code=404, detail=f"Recipe {recipe_id} not found")

        # Build update query
        updates = []
        params = []

        if recipe.name is not None:
            updates.append("name = ?")
            params.append(recipe.name)

        if recipe.description is not None:
            updates.append("description = ?")
            params.append(recipe.description)

        if recipe.steps is not None:
            updates.append("steps = ?")
            params.append(json.dumps([step.model_dump() for step in recipe.steps]))

        if not updates:
            raise HTTPException(status_code=400, detail="No fields to update")

        updates.append("updated_at = CURRENT_TIMESTAMP")
        params.append(recipe_id)

        await db.execute(
            f"UPDATE recipes SET {', '.join(updates)} WHERE id = ?",
            params
        )
        await db.commit()

        # Fetch and return updated recipe
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM recipes WHERE id = ?", (recipe_id,)) as cursor:
            row = await cursor.fetchone()
            return Recipe(
                id=row['id'],
                name=row['name'],
                description=row['description'],
                steps=json.loads(row['steps']),
                created_at=datetime.fromisoformat(row['created_at']),
                updated_at=datetime.fromisoformat(row['updated_at'])
            )


@router.delete("/{recipe_id}")
async def delete_recipe(recipe_id: int):
    """Delete a recipe"""
    async with aiosqlite.connect(settings.SQLITE_DB_PATH) as db:
        # Check if recipe is in use
        async with db.execute(
            "SELECT COUNT(*) FROM sessions WHERE recipe_id = ? AND status = 'running'",
            (recipe_id,)
        ) as cursor:
            count = (await cursor.fetchone())[0]
            if count > 0:
                raise HTTPException(
                    status_code=400,
                    detail=f"Cannot delete recipe: {count} active session(s) using it"
                )

        # Delete recipe
        cursor = await db.execute("DELETE FROM recipes WHERE id = ?", (recipe_id,))
        await db.commit()

        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail=f"Recipe {recipe_id} not found")

        return {"success": True, "message": f"Recipe {recipe_id} deleted"}
