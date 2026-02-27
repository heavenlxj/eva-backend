from services.storage import StorageService
from core.config.settings import settings

def get_storage_service() -> StorageService:
    return StorageService(base_url=settings.external.WHALE_URL)
