import param
import numpy as np
import panel as pn
import holoviews as hv
from alerce.core import Alerce

hv.extension("bokeh")
hv.opts.defaults(
    hv.opts.ErrorBars(
        width=300,
        height=200,
        lower_head=None,
        upper_head=None,
        xrotation=35,
        invert_yaxis=True,
        xlim=(0, 1),
    )
)

client = Alerce()
oids = client.query_objects(
    class_name="RRL", classifier="lc_classifier", probability=0.9, page_size=27
)["oid"]
lcs = {oid: client.query_detections(oid, format="pandas") for oid in oids}
periods = {
    oid: client.query_feature(oid, "Multiband_period")[0]["value"] for oid in oids
}


def plot_lc(oid):
    lc, period = lcs[oid], periods[oid]
    plot_bands = []
    for fid, c in zip([1, 2], ["green", "red"]):
        mjd, mag, err = (
            lc.loc[lc["fid"] == fid][["mjd", "magpsf_corr", "sigmapsf"]]
            .dropna()
            .values.T
        )
        phase = np.mod(mjd, period) / period
        plot_bands.append(
            hv.ErrorBars(
                (phase, mag, err),
                label=oid,
                kdims="Phase",
                vdims=["Magnitude", "Delta mag"],
            ).opts(line_color=c)
        )
    return hv.Overlay(plot_bands).opts(shared_axes=False, framewise=True)


class LightCurveExplorer(param.Parameterized):
    page = param.Integer(default=0, bounds=(0, 2))
    lc_per_page = 9

    @param.depends("page")
    def create_grid(self, lc_per_page=9):
        selection = oids[self.page * lc_per_page : (self.page + 1) * lc_per_page]
        return (
            hv.Layout([plot_lc(oid) for oid in selection])
            .cols(lc_per_page // 3)
            .opts(framewise=True, shared_axes=False)
        )

    def view(self):
        return hv.DynamicMap(self.create_grid).opts(shared_axes=False, framewise=True)


explorer = LightCurveExplorer()
app = pn.Column(explorer.view, explorer.param)
# If on jupyter you can run app to display the dashboard
app.save("docs/index.html", embed=True)
