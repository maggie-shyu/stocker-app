from fastapi import APIRouter, Depends

from backend.models.schemas import CommissionSettings
from backend.routers.deps import get_supabase_service
from backend.services.supabase_service import SupabaseService


router = APIRouter(prefix="/api/settings", tags=["settings"])


@router.get("", response_model=CommissionSettings)
def read_settings(service: SupabaseService = Depends(get_supabase_service)):
    return CommissionSettings(
        commission_discount_rate=service.get_commission_discount_rate()
    )


@router.put("", response_model=CommissionSettings)
def update_settings(
    payload: CommissionSettings,
    service: SupabaseService = Depends(get_supabase_service),
):
    return CommissionSettings(
        commission_discount_rate=service.set_commission_discount_rate(
            payload.commission_discount_rate
        )
    )
