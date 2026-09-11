from fastapi import HTTPException, status


class LocationNotFoundError(HTTPException):
    def __init__(self, location_id: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Location with id '{location_id}' not found",
        )


class LocationAlreadyExistsError(HTTPException):
    def __init__(self, location_id: str):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Location with id '{location_id}' already exists",
        )



class SessionHeaderMissingError(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Header 'X-Session-ID' is required for progress and passport operations",
        )


class S3ServiceError(HTTPException):
    def __init__(self, message: str):
        super().__init__(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"S3 Object Storage error: {message}",
        )


class LLMServiceError(HTTPException):
    def __init__(self, message: str):
        super().__init__(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Yandex LLM service error: {message}",
        )
