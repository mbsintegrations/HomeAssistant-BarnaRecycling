"""Execute real integration methods with small HA interface adapters.

These are unit tests, not a substitute for loading the integration in HA.
"""
import copy
from datetime import date, datetime, time, timedelta, timezone
from hashlib import sha256
import importlib
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import AsyncMock
from zoneinfo import ZoneInfo
import common

NOW = datetime(2026, 10, 25, 12, tzinfo=timezone.utc)
RAW = dict(balance=42.5, balance_status="debit", history_from="2026-01-01",
           last_successful_sync=NOW.isoformat(), calendar_status="ok",
           lifts=[dict(date="2026-10-15",stream="waste",weight=12.5,vehicle="DEMO",
                       description="240 Waste",bin_litres=240,ewc="200301")],
           collections=[dict(date="2026-10-25",streams=["waste","recycling","compost"]),
                        dict(date="2026-11-08",streams=["waste"])],
           alerts=[],calendar_advisories=[],calendar_sources=[],calendar_years=[2026])

class AbortFlow(Exception): pass
class Flow:
    def __init_subclass__(cls, **kwargs): super().__init_subclass__()
    async def async_set_unique_id(self,value): self.unique_id=value
    def _abort_if_unique_id_configured(self):
        if getattr(self,"duplicate",False): raise AbortFlow("already_configured")
    def _abort_if_unique_id_mismatch(self):
        if self.unique_id != self.entry.unique_id: raise AbortFlow("unique_id_mismatch")
    def _get_reauth_entry(self): return self.entry
    def _get_reconfigure_entry(self): return self.entry
    def async_update_reload_and_abort(self,entry,data_updates): return dict(type="abort",data=data_updates)
    def async_create_entry(self,**kw): return dict(type="create_entry",**kw)
    def async_show_form(self,**kw): return dict(type="form",**kw)

class Store:
    def __init__(self,hass,version,key,**kw): self.hass,self.key,self.options=hass,key,kw
    async def async_load(self): return copy.deepcopy(self.hass.storage.get(self.key))
    async def async_save(self,value):
        if self.hass.fail_save: raise OSError("demo disk error")
        self.hass.storage[self.key]=copy.deepcopy(value)
    async def async_remove(self): self.hass.storage.pop(self.key,None)

class Coordinator:
    def __init__(self,hass,logger,**kw): self.hass,self.data,self.options=hass,None,kw
    async def async_config_entry_first_refresh(self): self.data=await self._async_update_data()
    def async_update_listeners(self): self.notified=True
class Entity:
    def __init__(self,coordinator): self.coordinator=coordinator
class Event:
    def __init__(self,**kw): self.__dict__.update(kw)
class Schema:
    def __init__(self,schema): self.schema=schema
class Selector:
    def __init__(self,config): self.config=config

def load():
    modules={}
    def mod(name,**kw):
        result=types.ModuleType(name);result.__dict__.update(kw);modules[name]=result
        return result
    for name in ["homeassistant","homeassistant.helpers","homeassistant.components","homeassistant.util"]:
        mod(name).__path__=[]
    mod("homeassistant.core",callback=lambda f:f,SupportsResponse=types.SimpleNamespace(ONLY="only"))
    mod("homeassistant.exceptions",ConfigEntryAuthFailed=type("ConfigEntryAuthFailed",(Exception,),{}),
        HomeAssistantError=type("HomeAssistantError",(Exception,),{}))
    mod("homeassistant.config_entries",ConfigFlow=Flow)
    mod("homeassistant.const",CONF_USERNAME="username",CONF_PASSWORD="password",
        Platform=types.SimpleNamespace(SENSOR="sensor",BINARY_SENSOR="binary_sensor",CALENDAR="calendar"),
        EntityCategory=types.SimpleNamespace(DIAGNOSTIC="diagnostic"),
        UnitOfMass=types.SimpleNamespace(KILOGRAMS="kg"))
    mod("homeassistant.helpers.aiohttp_client",async_create_clientsession=lambda *a,**kw:types.SimpleNamespace(detach=lambda:None))
    mod("homeassistant.helpers.storage",Store=Store)
    mod("homeassistant.helpers.event",async_track_time_change=lambda *a,**kw:lambda:None)
    mod("homeassistant.helpers.update_coordinator",DataUpdateCoordinator=Coordinator,CoordinatorEntity=Entity,
        UpdateFailed=type("UpdateFailed",(Exception,),{}))
    mod("homeassistant.helpers.entity",DeviceInfo=lambda **kw:kw)
    mod("homeassistant.helpers.config_validation",entity_id=str)
    mod("homeassistant.helpers.entity_registry",async_get=lambda hass:hass.registry)
    mod("homeassistant.helpers.selector",TextSelector=Selector,TextSelectorConfig=lambda **kw:kw,
        TextSelectorType=types.SimpleNamespace(TEXT="text",PASSWORD="password"))
    mod("homeassistant.util.dt",utcnow=lambda:NOW,now=lambda:NOW,
        start_of_local_day=lambda d:datetime.combine(d,time(),ZoneInfo("Europe/Dublin")))
    mod("homeassistant.components.sensor",SensorEntity=type("SensorEntity",(),{}),
        SensorDeviceClass=types.SimpleNamespace(DATE="date",TIMESTAMP="timestamp",MONETARY="monetary",WEIGHT="weight"))
    mod("homeassistant.components.calendar",CalendarEntity=type("CalendarEntity",(),{}),CalendarEvent=Event)
    mod("homeassistant.components.binary_sensor",BinarySensorEntity=type("BinarySensorEntity",(),{}),
        BinarySensorDeviceClass=types.SimpleNamespace(PROBLEM="problem"))
    mod("voluptuous",Schema=Schema,Required=lambda x:x)
    previous={k:sys.modules.get(k) for k in modules}
    sys.modules.update(modules)
    package=types.ModuleType("barna_runtime")
    package.__path__=[str(common.ROOT/"custom_components/barna_recycling")]
    sys.modules["barna_runtime"]=package
    try:
        loaded={n:importlib.import_module("barna_runtime."+n) for n in
                ["coordinator","config_flow","sensor","calendar","binary_sensor","diagnostics"]}
        setup=types.ModuleType("barna_runtime.setup");setup.__package__="barna_runtime"
        exec(compile((Path(package.__path__[0])/"__init__.py").read_text(), "__init__.py","exec"),setup.__dict__)
        loaded["setup"]=setup
        return types.SimpleNamespace(**loaded)
    finally:
        for k,v in previous.items():
            if v is None: sys.modules.pop(k,None)
            else: sys.modules[k]=v

runtime=load()

class RuntimeTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.entry=types.SimpleNamespace(entry_id="demo-entry",unique_id=sha256(b"DEMO").hexdigest(),
            data={"username":"DEMO","password":"synthetic-test-pin"},async_on_unload=lambda f:None,
            async_start_reauth=lambda h:setattr(self,"reauth",True))
        self.hass=types.SimpleNamespace(storage={},fail_save=False,async_add_executor_job=AsyncMock())
        self.c=runtime.coordinator.BarnaCoordinator(self.hass,self.entry)
        self.c.portal.fetch=AsyncMock(return_value=copy.deepcopy(RAW))
        self.reauth=False
    async def test_success_private_cache_and_six_hour_interval(self):
        self.c.data=await self.c._async_update_data()
        self.assertFalse(self.c.stale)
        self.assertEqual(self.c.options["update_interval"],timedelta(hours=6))
        self.assertTrue(self.c.store.options["private"])
        self.assertEqual(self.hass.storage[self.c.store.key]["account_id"],self.entry.unique_id)
    async def test_restore_rejects_other_account_and_corrupt_data(self):
        for account,data in [("other",RAW),(self.entry.unique_id,dict(RAW,lifts="bad"))]:
            self.hass.storage[self.c.store.key]=dict(account_id=account,data=data)
            await self.c.async_load_cache()
            self.assertIsNone(self.c.cached)
        self.hass.storage[self.c.store.key]=dict(account_id=self.entry.unique_id,data=RAW)
        await self.c.async_load_cache()
        self.assertEqual(self.c.cached,RAW)
        self.assertTrue(self.c.stale)
    async def test_network_failure_retains_snapshot_then_recovers(self):
        await self.c._async_update_data()
        self.c.portal.fetch.side_effect=TimeoutError()
        data=await self.c._async_update_data()
        self.assertEqual(data,RAW);self.assertTrue(self.c.stale)
        self.assertEqual(self.c.error,"cannot_connect")
        self.c.portal.fetch.side_effect=None
        await self.c._async_update_data()
        self.assertFalse(self.c.stale);self.assertIsNone(self.c.error)
    async def test_failure_without_cache_retries(self):
        self.c.portal.fetch.side_effect=TimeoutError()
        with self.assertRaises(runtime.coordinator.UpdateFailed): await self.c._async_update_data()
    async def test_auth_with_and_without_cache(self):
        self.c.portal.fetch.side_effect=runtime.coordinator.AuthenticationError()
        with self.assertRaises(runtime.coordinator.ConfigEntryAuthFailed): await self.c._async_update_data()
        self.c.cached=copy.deepcopy(RAW)
        self.assertEqual(await self.c._async_update_data(),RAW)
        self.assertTrue(self.reauth);self.assertEqual(self.c.error,"authentication_required")
    async def test_otp_and_portal_change_keep_saved_data(self):
        self.c.cached=copy.deepcopy(RAW)
        for error,category in [(runtime.coordinator.OTPRequired(),"otp_required"),(runtime.coordinator.PortalError(),"portal_changed")]:
            self.c.portal.fetch.side_effect=error
            self.assertEqual(await self.c._async_update_data(),RAW)
            self.assertEqual(self.c.error,category)
    async def test_failed_disk_save_does_not_hide_fresh_data(self):
        self.hass.fail_save=True
        self.assertEqual(await self.c._async_update_data(),RAW)
        self.assertFalse(self.c.stale)
    async def test_midnight_notifies_without_fetching(self):
        self.c._midnight(NOW)
        self.assertTrue(self.c.notified);self.c.portal.fetch.assert_not_called()
    async def test_calendar_exclusive_end_and_dst_overlap(self):
        self.c.data=copy.deepcopy(RAW)
        cal=runtime.calendar.BarnaCalendar(self.c,None)
        events=list(cal.events())
        self.assertEqual(events[0].end,date(2026,10,26))
        # Irish autumn transition gives the all-day event 25 hours.
        values=await cal.async_get_events(self.hass,datetime(2026,10,24,23,tzinfo=timezone.utc),datetime(2026,10,26,tzinfo=timezone.utc))
        self.assertEqual(len(values),1)
        values=await cal.async_get_events(self.hass,datetime(2026,10,26,tzinfo=timezone.utc),datetime(2026,10,27,tzinfo=timezone.utc))
        self.assertEqual(values,[])
        self.assertEqual(len(list(runtime.calendar.BarnaCalendar(self.c,"compost").events())),1)
    async def test_sensors_counts_defaults_and_exhausted(self):
        self.c.data=copy.deepcopy(RAW);self.entry.runtime_data=self.c
        entities=[]
        await runtime.sensor.async_setup_entry(self.hass,self.entry,entities.extend)
        self.assertEqual(len(entities),22)
        self.assertEqual(sum(getattr(e,"_attr_entity_registry_enabled_default",True) is False for e in entities),7)
        summary=next(e for e in entities if e.key=="summary")
        self.assertEqual(summary.extra_state_attributes["collections"],RAW["collections"])
        self.c.data["collections"]=[]
        self.assertEqual(next(e for e in entities if e.key=="calendar_status").native_value,"exhausted")
    async def test_diagnostics_are_allowlisted(self):
        self.c.data=copy.deepcopy(RAW);self.entry.runtime_data=self.c
        data=await runtime.diagnostics.async_get_config_entry_diagnostics(self.hass,self.entry)
        self.assertEqual(set(data),{"version","data_stale","error","calendar_status","calendar_years","lift_record_count","collection_count"})
        self.assertNotIn("DEMO",str(data));self.assertNotIn("42.5",str(data))
    async def test_setup_unload_remove_and_history_service(self):
        self.hass.config_entries=types.SimpleNamespace(async_forward_entry_setups=AsyncMock(),
            async_unload_platforms=AsyncMock(return_value=True),async_get_entry=lambda id:self.entry)
        original=runtime.setup.BarnaCoordinator
        runtime.setup.BarnaCoordinator=lambda *a:self.c
        runtime.setup.async_setup_frontend=AsyncMock()
        try: self.assertTrue(await runtime.setup.async_setup_entry(self.hass,self.entry))
        finally: runtime.setup.BarnaCoordinator=original
        self.assertIs(self.entry.runtime_data,self.c)
        captured={}
        self.hass.services=types.SimpleNamespace(async_register=lambda domain,name,handler,**kw:captured.update(handler=handler,**kw))
        self.hass.registry=types.SimpleNamespace(async_get=lambda id:types.SimpleNamespace(config_entry_id="demo-entry",platform="barna_recycling"))
        await runtime.setup.async_setup(self.hass,{})
        result=await captured["handler"](types.SimpleNamespace(data={"entity_id":"sensor.demo"}))
        self.assertEqual(result["records"],RAW["lifts"]);self.assertEqual(captured["supports_response"],"only")
        self.hass.registry.async_get=lambda id:None
        with self.assertRaises(runtime.setup.HomeAssistantError):
            await captured["handler"](types.SimpleNamespace(data={"entity_id":"sensor.other"}))
        self.assertTrue(await runtime.setup.async_unload_entry(self.hass,self.entry))
        await runtime.setup.async_remove_entry(self.hass,self.entry)
        self.assertNotIn(self.c.store.key,self.hass.storage)

class FlowTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.f=runtime.config_flow.BarnaConfigFlow()
        self.f.hass=types.SimpleNamespace(async_add_executor_job=AsyncMock())
        self.f.entry=types.SimpleNamespace(unique_id=sha256(b"DEMO").hexdigest())
        self.session=types.SimpleNamespace(detach=lambda:setattr(self,"detached",True))
        self.detached=False
        runtime.config_flow.async_create_clientsession=lambda *a,**kw:self.session
        self.fetch=AsyncMock(return_value=RAW)
        runtime.config_flow.BarnaPortal=lambda *a,**kw:types.SimpleNamespace(fetch=self.fetch)
        self.login={"username":" DEMO ","password":"synthetic-test-pin"}
    async def test_masked_form(self):
        result=await self.f.async_step_user()
        self.assertEqual(result["data_schema"].schema["password"].config["type"],"password")
    async def test_success_trims_account_and_detaches_session(self):
        result=await self.f.async_step_user(self.login)
        self.assertEqual(result["type"],"create_entry");self.assertEqual(result["data"]["username"],"DEMO")
        self.assertTrue(self.detached)
    async def test_invalid_input_does_not_contact_portal(self):
        result=await self.f.async_step_user(dict(self.login,password=""))
        self.assertEqual(result["errors"]["base"],"invalid_auth");self.fetch.assert_not_called()
    async def test_duplicate_aborts(self):
        self.f.duplicate=True
        with self.assertRaisesRegex(AbortFlow,"already_configured"): await self.f.async_step_user(self.login)
        self.assertTrue(self.detached)
    async def test_reauth_and_reconfigure_preserve_identity(self):
        for method in [self.f.async_step_reauth_confirm,self.f.async_step_reconfigure]:
            self.assertEqual((await method(self.login))["type"],"abort")
        with self.assertRaisesRegex(AbortFlow,"unique_id_mismatch"):
            await self.f.async_step_reauth_confirm(dict(self.login,username="OTHER"))
    async def test_error_categories_do_not_include_provider_details(self):
        for error,category in [(runtime.config_flow.AuthenticationError("private"),"invalid_auth"),
                              (runtime.config_flow.OTPRequired("private"),"otp_required"),
                              (runtime.config_flow.PortalError("private"),"portal_changed"),
                              (TimeoutError("private"),"cannot_connect")]:
            self.fetch.side_effect=error
            result=await self.f.async_step_user(self.login)
            self.assertEqual(result["errors"]["base"],category)
            self.assertNotIn("private",str(result));self.assertTrue(self.detached)
