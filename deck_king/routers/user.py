from fastapi import APIRouter, Depends

# See: https://fastapi.tiangolo.com/tutorial/bigger-applications/

router = APIRouter(
  prefix="/users",
  tags=["users"],
  dependencies=[],
  responses={404: {"description": "Not found"}},
)

# TODO