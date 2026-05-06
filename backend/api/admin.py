from fastapi import APIRouter, Depends, HTTPException, Query

from backend.api.deps import (
    get_admin_service,
    get_current_user,
    is_admin_user,
    require_admin_user,
)
from backend.admin.metrics import AdminService
from backend.models.api.admin import AdminOverview, AdminTablePage, AdminTableSummary, CurrentUserCapabilities
from backend.models.api.auth import AuthenticatedUser


router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/capabilities", response_model=CurrentUserCapabilities)
def read_admin_capabilities(user: AuthenticatedUser = Depends(get_current_user)):
    return CurrentUserCapabilities(is_admin=is_admin_user(user))


@router.get("/overview", response_model=AdminOverview)
def read_admin_overview(
    _: AuthenticatedUser = Depends(require_admin_user),
    service: AdminService = Depends(get_admin_service),
):
    return service.get_overview()


@router.get("/tables", response_model=list[AdminTableSummary])
def list_admin_tables(
    _: AuthenticatedUser = Depends(require_admin_user),
    service: AdminService = Depends(get_admin_service),
):
    return service.list_tables()


@router.get("/tables/{table_name}", response_model=AdminTablePage)
def read_admin_table(
    table_name: str,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=200),
    _: AuthenticatedUser = Depends(require_admin_user),
    service: AdminService = Depends(get_admin_service),
):
    try:
        return service.read_table(table_name, page=page, page_size=page_size)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Admin table not found") from exc
