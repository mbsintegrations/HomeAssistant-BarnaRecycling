import asyncio
from collections import Counter
import threading
import unittest
from unittest.mock import patch
from common import account_html, lift_html
from custom_components.barna_recycling import portal
from custom_components.barna_recycling.portal import (
    AuthenticationError, BarnaPortal, OTPRequired, PortalError,
    parse_page, parse_account, parse_lifts, parse_calendar_links, safe_url, parse_date, number,
)


class ParserTests(unittest.TestCase):
    def test_debit_and_credit(self):
        self.assertEqual(parse_page(account_html(), parse_account)['balance'], 42.5)
        self.assertEqual(parse_page(account_html('1,234.56','CR'), parse_account)['balance'], -1234.56)
        self.assertEqual(len(parse_page(account_html(), parse_account)['alerts']), 1)

    def test_ambiguous_balance_rejected(self):
        for value in ('Current balance: € 2.50','Current balance: € NaN (DR)'):
            with self.assertRaises(PortalError): parse_page('<h3>'+value+'</h3>', parse_account)

    def test_lifts_and_coverage(self):
        data = parse_page(lift_html(), parse_lifts)
        self.assertEqual(data['history_from'], '2026-01-01')
        self.assertEqual(data['lifts'][0], {'date':'2026-01-08','vehicle':'DEMO-VEHICLE','description':'240 Waste EWC200301','stream':'waste','weight':12.5,'bin_litres':240,'ewc':'200301'})

    def test_empty_and_unknown_stream(self):
        self.assertEqual(parse_page(lift_html([]), parse_lifts)['lifts'], [])
        row=parse_page(lift_html([('2nd Jan 2026','DEMO','Glass','0')]), parse_lifts)['lifts'][0]
        self.assertEqual(row['stream'],'other')
        self.assertIsNone(row['ewc'])

    def test_bad_rows_fail_whole_history(self):
        for row in [('bad','DEMO','Glass','2'),('2 Jan 2026','DEMO','Glass','-1'),('2 Jan 2026','DEMO','Glass','NaN'),('missing',)]:
            with self.assertRaises(PortalError): parse_page(lift_html([row]), parse_lifts)

    def test_duplicate_lifts_are_not_silently_dropped(self):
        row=('2 Jan 2026','DEMO','240 Waste EWC200301','1')
        self.assertEqual(len(parse_page(lift_html([row,row]), parse_lifts)['lifts']),2)

    def test_challenges(self):
        for parser in (parse_account,parse_lifts,parse_calendar_links):
            with self.assertRaises(OTPRequired): parse_page('<h3>App Authentication</h3>', parser)
            with self.assertRaises(AuthenticationError): parse_page('<input name="Password" type="password">', parser)

    def test_download_origin_and_path(self):
        self.assertEqual(len(parse_page('<a href="/api/calendars/2026/DEMO_2026.pdf">Download</a>', parse_calendar_links)),1)
        upgraded=parse_page('<a href="http://cportal.barnarecycling.com/api/calendars/2026/DEMO.pdf">Download</a>', parse_calendar_links)
        self.assertEqual(upgraded,['https://cportal.barnarecycling.com/api/calendars/2026/DEMO.pdf'])
        for url in ('https://evil.example/a.pdf','http://cportal.barnarecycling.com/a.pdf','https://cportal.barnarecycling.com@evil.example/a.pdf','https://cportal.barnarecycling.com:444/api/calendars/2026/DEMO.pdf','/index.php?id=7','/api/calendars/2026/DEMO.pdf?account=1'):
            with self.assertRaises(PortalError): safe_url(url,pdf=True)

    def test_dates_and_numbers(self):
        self.assertEqual(parse_date('29th February 2028'),'2028-02-29')
        for value in ('29 Feb 2027','tomorrow'):
            with self.assertRaises(PortalError): parse_date(value)
        for value in ('nan','inf','1,23','2 EUR'):
            with self.assertRaises(PortalError): number(value)


class Response:
    def __init__(self, body='', status=200, headers=None):
        self.body=body.encode() if isinstance(body,str) else body
        self.status=status; self.headers=headers or {}; self.content=self
    async def __aenter__(self): return self
    async def __aexit__(self,*args): pass
    async def iter_chunked(self,n):
        for start in range(0,len(self.body),n): yield self.body[start:start+n]


class Jar:
    def clear(self): pass


class Session:
    def __init__(self,responses): self.responses=iter(responses);self.calls=[];self.cookie_jar=Jar()
    def request(self,method,url,**kwargs):
        self.calls.append((method,url,kwargs))
        return next(self.responses)


class ClientTests(unittest.IsolatedAsyncioTestCase):
    async def test_each_html_response_parsed_once_off_event_loop(self):
        # Exercise the actual fallback and HA-style injected executor paths.
        for executor in (None, asyncio.to_thread):
            with self.subTest(injected_executor=executor is not None):
                bodies = [account_html(), account_html(), lift_html(), '<h1>Calendar</h1>']
                session = Session([Response(body) for body in bodies])
                client = BarnaPortal(session, 'DEMO', 'PIN', executor)
                loop_thread = threading.get_ident()
                parsed = []
                original = portal.Document

                def document(html):
                    self.assertNotEqual(threading.get_ident(), loop_thread)
                    parsed.append(html)
                    return original(html)

                with patch.object(portal, 'Document', side_effect=document):
                    data = await client.fetch()
                self.assertEqual(Counter(parsed), Counter(bodies))
                self.assertEqual(data['balance'], 42.5)
                self.assertEqual(len(data['lifts']), 1)

    async def test_all_dom_validation_and_extraction_stays_in_worker(self):
        loop_thread = threading.get_ident()
        original_text, original_find = portal.Node.text, portal.Node.find

        def text(node):
            self.assertNotEqual(threading.get_ident(), loop_thread)
            return original_text.fget(node)

        def find(node, *args, **kwargs):
            self.assertNotEqual(threading.get_ident(), loop_thread)
            return original_find(node, *args, **kwargs)

        responses = [Response(account_html()), Response(account_html()),
                     Response(lift_html()), Response('<h1>Calendar</h1>')]
        with patch.object(portal.Node, 'text', property(text)), patch.object(portal.Node, 'find', find):
            await BarnaPortal(Session(responses), 'DEMO', 'PIN').fetch()
            for html, error in [('<input name="Password">', AuthenticationError),
                                ('<p>one-time passcode</p>', OTPRequired),
                                ('<h1>Account changed</h1>', AuthenticationError)]:
                with self.assertRaises(error):
                    await BarnaPortal(Session([Response(html)]), 'DEMO', 'PIN').login()

    async def test_event_loop_progresses_while_large_page_is_parsed(self):
        # Close to the 2 MB response limit, with the maximum 2000 lift records.
        html = lift_html([('8 Jan 2026', 'DEMO', '240 Waste EWC200301', '12.50')] * 2000)
        html += '<p>' + 'x' * (1_999_000 - len(html.encode()) - 7) + '</p>'
        entered, release = threading.Event(), threading.Event()
        loop_thread = threading.get_ident()
        original = portal.Document

        def document(value):
            self.assertNotEqual(threading.get_ident(), loop_thread)
            entered.set()
            if not release.wait(5):
                raise AssertionError('Event loop did not release the parser worker')
            return original(value)

        client = BarnaPortal(Session([Response(html)]), 'DEMO', 'PIN')
        with patch.object(portal, 'Document', side_effect=document):
            task = asyncio.create_task(client.page('index.php?id=4', parse_lifts))
            try:
                async with asyncio.timeout(5):
                    while not entered.is_set() and not task.done():
                        await asyncio.sleep(0.001)
                    if task.done():
                        await task
                    # A queued loop callback must run while the worker is held.
                    tick = asyncio.get_running_loop().create_future()
                    asyncio.get_running_loop().call_soon(tick.set_result, True)
                    self.assertTrue(await tick)
                    self.assertFalse(task.done())
            finally:
                release.set()
                data = await task
        self.assertEqual(len(data['lifts']), 2000)

    async def test_session_retry_parses_each_response_once(self):
        bodies = ['<input name="Password">', account_html(), account_html()]
        client = BarnaPortal(Session([Response(x) for x in bodies]), 'DEMO', 'PIN')
        client.authenticated = True
        original = portal.Document
        with patch.object(portal, 'Document', wraps=original) as document:
            data = await client.page('index.php', parse_account)
        self.assertEqual(document.call_count, 3)
        self.assertEqual(data['balance'], 42.5)

    async def test_persistent_expired_session_retries_only_once(self):
        client = BarnaPortal(Session([Response('<input name="Password">'),
            Response(account_html()), Response('<input name="Password">')]), 'DEMO', 'PIN')
        client.authenticated = True
        with self.assertRaises(AuthenticationError):
            await client.page('index.php', parse_account)
        self.assertFalse(client.authenticated)
        self.assertEqual(len(client.session.calls), 3)

    async def test_page_challenges_and_layout_errors_do_not_relogin(self):
        for html, error in [('<p>one-time passcode</p><input name="Password">', OTPRequired),
                            ('<h1>Account changed</h1>', PortalError)]:
            client = BarnaPortal(Session([Response(html)]), 'DEMO', 'PIN')
            client.authenticated = True
            with self.assertRaises(error):
                await client.page('index.php', parse_account)
            self.assertEqual(len(client.session.calls), 1)

    async def test_failed_login_clears_authenticated_state(self):
        client = BarnaPortal(Session([Response('<input name="Password">')]), 'DEMO', 'PIN')
        client.authenticated = True
        with self.assertRaises(AuthenticationError):
            await client.login()
        self.assertFalse(client.authenticated)

    async def test_unsupported_calendar_still_preserves_account_and_lifts(self):
        client = BarnaPortal(Session([Response(account_html()), Response(account_html()),
            Response(lift_html()), Response('<a href="https://evil.example/a.pdf">PDF</a>')]), 'DEMO', 'PIN')
        data = await client.fetch()
        self.assertEqual(data['calendar_status'], 'unsupported')
        self.assertEqual(data['collections'], [])
        self.assertEqual(data['balance'], 42.5)
        self.assertEqual(len(data['lifts']), 1)

    async def test_readonly_fetch_without_calendar(self):
        session=Session([Response(account_html()),Response(account_html()),Response(lift_html()),Response('<h1>Collection calendar</h1>')])
        data=await BarnaPortal(session,'DEMO','PIN').fetch()
        self.assertEqual(data['calendar_status'],'missing')
        self.assertEqual(len(session.calls),4)
        self.assertEqual(session.calls[0][0],'POST')
        self.assertTrue(all(c[0]=='GET' for c in session.calls[1:]))
        self.assertIn('last12month',session.calls[2][1])

    async def test_expired_session_reauth_once(self):
        session=Session([Response('<input name="Password">'),Response(account_html()),Response(account_html())])
        client=BarnaPortal(session,'DEMO','PIN');client.authenticated=True
        self.assertEqual((await client.page('index.php', parse_account))['balance'],42.5)
        self.assertEqual([x[0] for x in session.calls],['GET','POST','GET'])

    async def test_login_redirect_drops_post_body(self):
        session=Session([Response(status=302,headers={'Location':'index.php'}),Response(account_html())])
        await BarnaPortal(session,'DEMO','PIN').login()
        self.assertIsNone(session.calls[1][2]['data'])

    async def test_cross_origin_redirect_never_followed(self):
        session=Session([Response(status=302,headers={'Location':'https://evil.example/'})])
        with self.assertRaises(PortalError): await BarnaPortal(session,'DEMO','PIN').login()
        self.assertEqual(len(session.calls),1)

    async def test_otp_not_submitted(self):
        session=Session([Response('<h3>App Authentication</h3>')])
        with self.assertRaises(OTPRequired): await BarnaPortal(session,'DEMO','PIN').login()
        self.assertEqual(len(session.calls),1)

    async def test_limits_and_redirect_loop(self):
        for responses in ([Response('x'*2000001)], [Response(status=302,headers={'Location':'index.php'}) for _ in range(5)]):
            with self.assertRaises(PortalError): await BarnaPortal(Session(responses),'DEMO','PIN')._request('index.php')

    async def test_non_pdf_rejected(self):
        with self.assertRaises(PortalError):
            await BarnaPortal(Session([Response('<html>login</html>')]),'DEMO','PIN')._request('/api/calendars/2026/DEMO.pdf',pdf=True)
