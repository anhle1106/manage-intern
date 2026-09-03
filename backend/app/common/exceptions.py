from fastapi import HTTPException, status


class NotFoundError(HTTPException):
    def __init__(self, resource: str = "Resource"):
        super().__init__(status.HTTP_404_NOT_FOUND, f"{resource} not found")


class ForbiddenError(HTTPException):
    def __init__(self, message: str = "Access denied"):
        super().__init__(status.HTTP_403_FORBIDDEN, message)


class BadRequestError(HTTPException):
    def __init__(self, message: str = "Bad request"):
        super().__init__(status.HTTP_400_BAD_REQUEST, message)


class UnauthorizedError(HTTPException):
    def __init__(self, message: str = "Unauthorized"):
        super().__init__(status.HTTP_401_UNAUTHORIZED, message)
