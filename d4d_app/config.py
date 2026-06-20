from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./d4d_crm.db")
    nominatim_base_url: str = os.getenv("NOMINATIM_BASE_URL", "https://nominatim.openstreetmap.org")
    nominatim_user_agent: str = os.getenv("NOMINATIM_USER_AGENT", "D4DListGenTool/1.0")
    leon_property_search_url: str = os.getenv("LEON_PROPERTY_SEARCH_URL", "")


settings = Settings()
