from fastapi import APIRouter, Depends

from backend.models.schemas import UserSettings
from backend.routers.deps import get_supabase_service
from backend.services.supabase_service import SupabaseService


router = APIRouter(prefix="/api/settings", tags=["settings"])


@router.get("", response_model=UserSettings)
def read_settings(service: SupabaseService = Depends(get_supabase_service)):
    return service.get_settings()


@router.put("", response_model=UserSettings)
def update_settings(
    payload: UserSettings,
    service: SupabaseService = Depends(get_supabase_service),
):
    return service.update_settings(payload)
