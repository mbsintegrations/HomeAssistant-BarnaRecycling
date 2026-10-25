import calendar
from io import BytesIO
import unittest
from reportlab.pdfgen import canvas
import common
from custom_components.barna_recycling.pdf_calendar import parse_calendar_pdf
from custom_components.barna_recycling.portal import PortalError


def synthetic_pdf(year=2026, second_colour=False, wrong_legend=False):
    """New synthetic artwork; no Barna PDF, customer route or customer data."""
    buf=BytesIO(); c=canvas.Canvas(buf,pagesize=(841.89,595.28)); c.setFont('Helvetica',10)
    c.drawString(600,500,str(year))
    orange=(.898,.365,.145)
    for month in range(1,13):
        col=(month-1)%3; row=(month-1)//3; x0=40+col*140; top=35+row*140
        c.setFillColorRGB(0,0,0); c.drawCentredString(x0+60,595.28-top,calendar.month_name[month])
        for week,days in enumerate(calendar.monthcalendar(year,month)):
            for weekday,day in enumerate(days):
                if not day: continue
                x=x0+weekday*18; y=595.28-top-25-week*18
                colour=(0,0,1) if second_colour and day==16 else orange
                c.setFillColorRGB(*(colour if day in (2,16) else (1,1,1)))
                c.rect(x-8,y-5,17,17,stroke=0,fill=1)
                c.setFillColorRGB(0,0,0);c.drawCentredString(x,y,str(day))
    c.setFillColorRGB(*orange);c.rect(500,260,17,17,stroke=0,fill=1)
    c.setFillColorRGB(0,0,0)
    c.drawString(540,205,'Waste');c.drawString(600,205,'Recyc');c.drawString(660,205,'Other' if wrong_legend else 'Compost')
    c.drawString(520,40,'Christmas collections have yet to be confirmed')
    c.save();return buf.getvalue()


class PDFTests(unittest.TestCase):
    def test_combined_calendar(self):
        result=parse_calendar_pdf(synthetic_pdf())
        self.assertEqual(result['year'],2026)
        self.assertEqual(len(result['collections']),24)
        self.assertEqual(result['collections'][0],{'date':'2026-01-02','streams':['waste','recycling','compost']})
        self.assertIn('Christmas collections have yet to be confirmed',result['advisories'])

    def test_leap_year_and_year_rollover(self):
        for year in (2027,2028):
            result=parse_calendar_pdf(synthetic_pdf(year))
            self.assertEqual(result['collections'][-1]['date'],f'{year}-12-16')

    def test_unsupported_legends_or_multiple_colours_fail_closed(self):
        for payload in (synthetic_pdf(second_colour=True),synthetic_pdf(wrong_legend=True),b'%PDF-broken'):
            with self.assertRaises(PortalError): parse_calendar_pdf(payload)
