"""Load the client without importing Home Assistant's integration entry point."""
from pathlib import Path
import sys
import types

ROOT = Path(__file__).resolve().parents[1]
name = "custom_components.barna_recycling"
if name not in sys.modules:
    parent = types.ModuleType("custom_components")
    parent.__path__ = [str(ROOT / "custom_components")]
    sys.modules["custom_components"] = parent
    package = types.ModuleType(name)
    package.__path__ = [str(ROOT / "custom_components/barna_recycling")]
    sys.modules[name] = package


def account_html(amount="42.50", status="DR"):
    return f'<a href="index.php?id=99">Logout</a><h3><strong>Current balance:</strong> € {amount} Outstanding ({status})</h3><div class="alerts"><h5>Example notice</h5><p>Read the customer portal.</p></div>'


def lift_html(rows=None):
    rows = rows if rows is not None else [('8th Jan 2026','DEMO-VEHICLE','240 Waste EWC200301','12.50')]
    return '<h4>Lift Service From 1st Jan 2026</h4><table id="datatable"><thead><tr><td>Lift Date</td><td>Vehicle Reg</td><td>Bin Type</td><td>Weight (KG)</td></tr></thead><tbody>' + ''.join('<tr>'+''.join('<td>'+x+'</td>' for x in row)+'</tr>' for row in rows) + '</tbody></table>'
