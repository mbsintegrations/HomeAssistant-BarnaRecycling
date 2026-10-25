"""Render original SVG brand artwork; optional build dependency: PyMuPDF."""
from pathlib import Path
import pymupdf as fitz
import re

ROOT=Path(__file__).resolve().parents[1]
source=(ROOT/'assets/icon.svg').read_text()
# Expand reusable bin shapes for renderers with incomplete currentColor/use support.
shape=re.search(r'<g id="bin">(.*?)</g>',source,re.S)
if shape:
    source='<svg xmlns="http://www.w3.org/2000/svg" width="512" height="512" viewBox="0 0 512 512">'+''.join(
        f'<g transform="translate({x} 92)">'+shape[1].replace('currentColor',colour)+'</g>'
        for x,colour in ((20,'#292f33'),(180,'#087fc4'),(340,'#965018')))+'</svg>'
brand=ROOT/'custom_components/barna_recycling/brand'
brand.mkdir(exist_ok=True)
(ROOT/'custom_components/barna_recycling/frontend/bins.svg').write_text(source.replace('viewBox="0 0 512 512"','viewBox="0 85 512 345"'))
for size,name in ((256,'icon.png'),(512,'icon@2x.png')):
    svg=fitz.open(stream=source.encode(),filetype='svg')
    pdf=fitz.open(stream=svg.convert_to_pdf(),filetype='pdf')
    pdf[0].get_pixmap(matrix=fitz.Matrix(size/pdf[0].rect.width,size/pdf[0].rect.height),alpha=True).save(brand/name)
for dark in (False,True):
    colour='#eff4f7' if dark else '#17252b'
    inner=source[source.index('>')+1:source.rindex('</svg>')]
    svg=f'<svg xmlns="http://www.w3.org/2000/svg" width="512" height="128" viewBox="0 0 512 128"><g transform="translate(4 -4) scale(.25)">{inner}</g><text x="145" y="67" font-family="Arial,sans-serif" font-size="34" font-weight="bold" fill="{colour}">Barna Recycling</text><text x="147" y="93" font-family="Arial,sans-serif" font-size="15" fill="{colour}">MBS Integrations</text></svg>'
    name='dark_logo' if dark else 'logo'
    (ROOT/f'assets/{name}.svg').write_text(svg)
    doc=fitz.open(stream=svg.encode(),filetype='svg');pdf=fitz.open(stream=doc.convert_to_pdf(),filetype='pdf')
    for scale,suffix in ((1,''),(2,'@2x')):
        pdf[0].get_pixmap(matrix=fitz.Matrix(scale,scale),alpha=True).save(brand/f'{name}{suffix}.png')
