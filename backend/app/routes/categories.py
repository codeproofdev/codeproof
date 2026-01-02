"""
Categories routes
Handles category and subcategory retrieval
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.database import get_db
from app.models import Category, Subcategory
from app.schemas import CategoryDetail, CategoryOut

router = APIRouter()


@router.get("", response_model=List[CategoryDetail])
async def get_categories(
    db: AsyncSession = Depends(get_db)
):
    """
    Get all categories with their subcategories

    **Returns:**
    - List of categories with nested subcategories

    **Note:**
    - Public endpoint (no authentication required)
    - Ordered by category order
    - Subcategories ordered by subcategory order
    """
    # Fetch all categories ordered by order field
    result = await db.execute(
        select(Category).order_by(Category.order)
    )
    categories = result.scalars().all()

    # For each category, fetch its subcategories
    category_details = []
    for category in categories:
        # Fetch subcategories for this category
        result = await db.execute(
            select(Subcategory)
            .where(Subcategory.category_id == category.id)
            .order_by(Subcategory.order)
        )
        subcategories = result.scalars().all()

        # Build response
        category_dict = {
            "id": category.id,
            "code": category.code,
            "name_en": category.name_en,
            "name_es": category.name_es,
            "description_en": category.description_en,
            "description_es": category.description_es,
            "icon": category.icon,
            "order": category.order,
            "problem_range_start": category.problem_range_start,
            "problem_range_end": category.problem_range_end,
            "subcategories": subcategories
        }
        category_details.append(category_dict)

    return category_details


@router.get("/{category_id}", response_model=CategoryDetail)
async def get_category(
    category_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get single category with its subcategories

    **Path Parameters:**
    - category_id: Category ID

    **Returns:**
    - Category with nested subcategories

    **Errors:**
    - 404: Category not found
    """
    # Fetch category
    result = await db.execute(
        select(Category).where(Category.id == category_id)
    )
    category = result.scalar_one_or_none()

    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )

    # Fetch subcategories
    result = await db.execute(
        select(Subcategory)
        .where(Subcategory.category_id == category.id)
        .order_by(Subcategory.order)
    )
    subcategories = result.scalars().all()

    # Build response
    category_dict = {
        "id": category.id,
        "code": category.code,
        "name_en": category.name_en,
        "name_es": category.name_es,
        "description_en": category.description_en,
        "description_es": category.description_es,
        "icon": category.icon,
        "order": category.order,
        "problem_range_start": category.problem_range_start,
        "problem_range_end": category.problem_range_end,
        "subcategories": subcategories
    }

    return category_dict
