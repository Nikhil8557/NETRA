# backend/app/external_api.py
import asyncio
import logging
import time
import hashlib
import hmac
import httpx
from app.config import settings
from ksp_netra_ingestion.models import VahanPayload

logger = logging.getLogger("ksp_netra.external_api")

class VahanClient:
    def __init__(self):
        self.endpoint = settings.VAHAN_API_ENDPOINT
        self.client_id = settings.VAHAN_CLIENT_ID
        self.secret = settings.VAHAN_API_SECRET
        self.timeout = 5.0

    def _generate_hmac_signature(self, timestamp: str, payload_body: str) -> str:
        """
        Calculates HMAC-SHA256 authorization signatures required for MoRTH gateway integration.
        """
        message = f"{self.client_id}|{timestamp}|{payload_body}"
        return hmac.new(
            self.secret.encode("utf-8"),
            message.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()

    async def fetch_vehicle_details(self, registration_number: str) -> VahanPayload:
        max_retries = 3
        backoff = 1.5
        clean_reg = registration_number.replace("-", "").replace(" ", "").upper()
        
        timestamp = str(int(time.time()))
        payload_body = f'{{"reg_no": "{clean_reg}"}}'
        signature = self._generate_hmac_signature(timestamp, payload_body)
        
        headers = {
            "X-Client-ID": self.client_id,
            "X-Timestamp": timestamp,
            "X-Signature": signature,
            "Content-Type": "application/json"
        }
        
        for attempt in range(1, max_retries + 1):
            try:
                # Standard endpoint queries
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(self.endpoint, headers=headers, data=payload_body)
                    response.raise_for_status()
                    payload = response.json()
                    
                    return VahanPayload(
                        registration_number=registration_number,
                        owner_name=payload.get("owner_name"),
                        make_model=payload.get("make_model"),
                        blacklist_status=payload.get("blacklist_status", False),
                        sync_status="SYNCED"
                    )
            except Exception as err:
                logger.warning(f"VAHAN endpoint failure (Attempt {attempt}/{max_retries}): {err}")
                if attempt == max_retries:
                    break
                await asyncio.sleep(backoff ** attempt)
                
        logger.error(f"VAHAN synchronization failed for vehicle: {registration_number}")
        return VahanPayload(
            registration_number=registration_number,
            owner_name="PENDING_SYNC_OWNER",
            make_model="PENDING_SYNC_MODEL",
            blacklist_status=False,
            sync_status="PENDING_VAHAN_SYNC"
        )
