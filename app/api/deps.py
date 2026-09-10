from typing import AsyncGenerator, Optional
from fastapi import Header
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.exceptions import SessionHeaderMissingError


async def get_session_id(
    x_session_id: Optional[str] = Header(None, alias="X-Session-ID")
) -> str:
    """
    Extract and validate the required X-Session-ID header.
    Generated on device by the frontend as a UUID.
    """
    if not x_session_id or not x_session_id.strip():
        raise SessionHeaderMissingError()
    return x_session_id.strip()
