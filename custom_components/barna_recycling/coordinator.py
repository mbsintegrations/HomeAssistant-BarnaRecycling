"""One bounded six-hour refresh and private last-good snapshot per account."""
from datetime import timedelta
import logging

import aiohttp
from homeassistant.core import callback
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.aiohttp_client import async_create_clientsession
from homeassistant.helpers.event import async_track_time_change
from homeassistant.helpers.storage import Store
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .const import DOMAIN, UPDATE_HOURS
from .portal import AuthenticationError, BarnaPortal, OTPRequired, PortalError
from .model import validate_snapshot

LOGGER = logging.getLogger(__name__)


class BarnaCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, entry):
        super().__init__(hass, LOGGER, config_entry=entry, name=DOMAIN,
                         update_interval=timedelta(hours=UPDATE_HOURS))
        self.entry = entry
        self.account_id = entry.unique_id
        self.cached = None
        self.stale = True
        self.error = None
        self.store = Store(hass, 1, f"{DOMAIN}_{entry.entry_id}", private=True, atomic_writes=True)
        session = async_create_clientsession(hass, cookie_jar=aiohttp.CookieJar(),
                                             timeout=aiohttp.ClientTimeout(total=30))
        self.portal = BarnaPortal(session, entry.data["username"], entry.data["password"], hass.async_add_executor_job)
        entry.async_on_unload(async_track_time_change(hass, self._midnight, hour=0, minute=0, second=0))

    @callback
    def _midnight(self, now):
        self.async_update_listeners()

    async def async_load_cache(self):
        try:
            raw = await self.store.async_load()
            if raw and raw.get("account_id") == self.account_id and validate_snapshot(raw.get("data")):
                self.cached = raw["data"]
        except (OSError, ValueError, TypeError, AttributeError):
            LOGGER.warning("Barna saved data could not be restored")

    async def _async_update_data(self):
        try:
            data = await self.portal.fetch()
            data["last_successful_sync"] = dt_util.utcnow().isoformat()
            if not validate_snapshot(data):
                raise PortalError("Portal returned an invalid snapshot")
            self.cached = data
            self.stale, self.error = False, None
            try:
                await self.store.async_save({"account_id": self.account_id, "data": data})
            except OSError:
                LOGGER.warning("Barna latest readings could not be saved")
            return data
        except AuthenticationError as err:
            if self.cached is None:
                raise ConfigEntryAuthFailed("Re-enter the Barna account number and PIN") from err
            self.entry.async_start_reauth(self.hass)
            self.error = "authentication_required"
        except OTPRequired:
            self.error = "otp_required"
        except PortalError:
            self.error = "portal_changed"
        except (aiohttp.ClientError, TimeoutError):
            self.error = "cannot_connect"
        self.stale = True
        if self.cached is None:
            raise UpdateFailed(self.error)
        return dict(self.cached)
