import param
import panel as pn
import holoviews as hv
from alerce.core import Alerce

hv.extension('bokeh')
hv.opts.defaults(hv.opts.ErrorBars(width=300, height=200, lower_head=None, 
                                   upper_head=None, xrotation=35))

client = Alerce()
cols = ['mjd', 'fid', 'magpsf', 'sigmapsf']
oids = client.query_objects(class_name='RRL', page_size=27)['oid']
lcs = {oid: client.query_detections(oid, format='pandas')[cols] for oid in oids}                                   


def plot_lc(lc):
    plot_bands = []
    for fid, c in zip([1, 2], ['green', 'red']):
        data = lc.loc[lc['fid']==fid].drop('fid', axis=1)
        plot_bands.append(hv.ErrorBars((data['mjd'], data['magpsf'], data['sigmapsf']),
                                       kdims='MJD', vdims=['Magnitude', 'Delta mag']).opts(line_color=c))
    return hv.Overlay(plot_bands).opts(shared_axes=False, framewise=True)

class LightCurveExplorer(param.Parameterized):
    page = param.Integer(default=0, bounds=(0, 2))
    lc_per_page = 9
    
    @param.depends('page')
    def create_grid(self, lc_per_page=9):
        selection = oids[self.page*lc_per_page:(self.page+1)*lc_per_page]
        return hv.Layout([plot_lc(lcs[oid]) for oid in selection ]).cols(lc_per_page//3).opts(framewise=True, shared_axes=False)
        
    def view(self):
        return hv.DynamicMap(self.create_grid).opts(shared_axes=False, framewise=True)
    
explorer = LightCurveExplorer()
app = pn.Column(explorer.view, explorer.param)
# If on jupyter you can run app to display the dashboard
app.save("dashboard.html", embed=True)