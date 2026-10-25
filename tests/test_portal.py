import unittest
from common import account_html, lift_html
from custom_components.barna_recycling.portal import (
    AuthenticationError, BarnaPortal, OTPRequired, PortalError,
    parse_account, parse_lifts, parse_calendar_links, safe_url, parse_date, number,
)


class ParserTests(unittest.TestCase):
    def test_debit_and_credit(self):
        self.assertEqual(parse_account(account_html())['balance'], 42.5)
        self.assertEqual(parse_account(account_html('1,234.56','CR'))['balance'], -1234.56)
        self.assertEqual(len(parse_account(account_html())['alerts']), 1)

    def test_ambiguous_balance_rejected(self):
        for value in ('Current balance: € 2.50','Current balance: € NaN (DR)'):
            with self.assertRaises(PortalError): parse_account('<h3>'+value+'</h3>')

    def test_lifts_and_coverage(self):
        data = parse_lifts(lift_html())
        self.assertEqual(data['history_from'], '2026-01-01')
        self.assertEqual(data['lifts'][0], {'date':'2026-01-08','vehicle':'DEMO-VEHICLE','description':'240 Waste EWC200301','stream':'waste','weight':12.5,'bin_litres':240,'ewc':'200301'})

    def test_empty_and_unknown_stream(self):
        self.assertEqual(parse_lifts(lift_html([]))['lifts'], [])
        row=parse_lifts(lift_html([('2nd Jan 2026','DEMO','Glass','0')]))['lifts'][0]
        self.assertEqual(row['stream'],'other')
        self.assertIsNone(row['ewc'])

    def test_bad_rows_fail_whole_history(self):
        for row in [('bad','DEMO','Glass','2'),('2 Jan 2026','DEMO','Glass','-1'),('2 Jan 2026','DEMO','Glass','NaN'),('missing',)]:
            with self.assertRaises(PortalError): parse_lifts(lift_html([row]))

    def test_duplicate_lifts_are_not_silently_dropped(self):
        row=('2 Jan 2026','DEMO','240 Waste EWC200301','1')
        self.assertEqual(len(parse_lifts(lift_html([row,row]))['lifts']),2)

    def test_challenges(self):
        for parser in (parse_account,parse_lifts,parse_calendar_links):
            with self.assertRaises(OTPRequired): parser('<h3>App Authentication</h3>')
            with self.assertRaises(AuthenticationError): parser('<input name="Password" type="password">')

    def test_download_origin_and_path(self):
        self.assertEqual(len(parse_calendar_links('<a href="/api/calendars/2026/DEMO_2026.pdf">Download</a>')),1)
        upgraded=parse_calendar_links('<a href="http://cportal.barnarecycling.com/api/calendars/2026/DEMO.pdf">Download</a>')
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
        self.assertEqual(parse_account(await client.page('index.php'))['balance'],42.5)
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
