"""Native setup with masked PIN, reauthentication and account identity checks."""
from hashlib import sha256
import re
import aiohttp
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.helpers.aiohttp_client import async_create_clientsession
from homeassistant.helpers.selector import TextSelector, TextSelectorConfig, TextSelectorType

from .const import DOMAIN
from .portal import AuthenticationError, BarnaPortal, OTPRequired, PortalError


class BarnaConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        return await self._credentials("user", user_input)

    async def async_step_reauth(self, entry_data):
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(self, user_input=None):
        return await self._credentials("reauth_confirm", user_input)

    async def async_step_reconfigure(self, user_input=None):
        return await self._credentials("reconfigure", user_input)

    async def _credentials(self, step, user_input):
        errors = {}
        if user_input is not None:
            username = user_input[CONF_USERNAME].strip()
            password = user_input[CONF_PASSWORD]
            session = async_create_clientsession(self.hass, auto_cleanup=False, cookie_jar=aiohttp.CookieJar(),
                                                 timeout=aiohttp.ClientTimeout(total=30))
            try:
                if not re.fullmatch(r"[^\s\x00-\x1f]{1,64}", username) or not password:
                    raise AuthenticationError("Invalid account credentials")
                await BarnaPortal(session, username, password, self.hass.async_add_executor_job).fetch()
                await self.async_set_unique_id(sha256(username.encode()).hexdigest())
                data = {CONF_USERNAME: username, CONF_PASSWORD: password}
                if step != "user":
                    self._abort_if_unique_id_mismatch()
                    entry = self._get_reauth_entry() if step == "reauth_confirm" else self._get_reconfigure_entry()
                    return self.async_update_reload_and_abort(entry, data_updates=data)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(title="Barna Recycling", data=data)
            except AuthenticationError:
                errors["base"] = "invalid_auth"
            except OTPRequired:
                errors["base"] = "otp_required"
            except PortalError:
                errors["base"] = "portal_changed"
            except (aiohttp.ClientError, TimeoutError):
                errors["base"] = "cannot_connect"
            finally:
                session.detach()
        return self.async_show_form(step_id=step, data_schema=vol.Schema({
            vol.Required(CONF_USERNAME): TextSelector(TextSelectorConfig(type=TextSelectorType.TEXT)),
            vol.Required(CONF_PASSWORD): TextSelector(TextSelectorConfig(type=TextSelectorType.PASSWORD)),
        }), errors=errors)
