from app.core.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends


def get_database(db: AsyncSession = Depends(get_db)) -> AsyncSession:
    return db