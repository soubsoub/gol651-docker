import marimo

__generated_with = "0.25.1"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    import numpy as np
    import pandas as pd
    import plotly.express as px

    return mo, np, pd, px


@app.cell
def _(mo):
    mo.md(r"""
    # GOL651 – Marimo : quantité économique de commande
    *GOL651 – Marimo: economic order quantity*

    Marimo est **réactif** : déplacez un curseur, et toutes les cellules qui
    en dépendent sont recalculées automatiquement.
    *Marimo is reactive: move a slider and every dependent cell re-runs.*

    $$Q^{*} = \sqrt{\frac{2\,D\,S}{H}}$$
    """)
    return


@app.cell
def _(mo):
    demand = mo.ui.slider(500, 10_000, step=500, value=4_000,
                          label="Demande annuelle D / annual demand (units)")
    order_cost = mo.ui.slider(10, 200, step=5, value=45,
                              label="Coût par commande S / cost per order ($)")
    holding = mo.ui.slider(0.5, 10.0, step=0.1, value=2.2,
                           label="Coût de stockage H / holding cost ($/unit/year)")
    mo.vstack([demand, order_cost, holding])
    return demand, holding, order_cost


@app.cell
def _(demand, holding, mo, np, order_cost):
    D, S, H = demand.value, order_cost.value, holding.value
    q_star = float(np.sqrt(2 * D * S / H))
    cost_star = D / q_star * S + q_star / 2 * H
    mo.md(
        f"**Q\\* = {q_star:,.0f} units** · {D / q_star:.1f} orders/year · "
        f"minimum yearly cost **{cost_star:,.2f} $**"
    )
    return D, H, S, q_star


@app.cell
def _(D, H, S, np, pd, px, q_star):
    _q = np.linspace(max(q_star * 0.2, 1.0), q_star * 3, 120)
    _curve = pd.DataFrame({"Q": _q, "ordering": D / _q * S, "holding": _q / 2 * H})
    _curve["total"] = _curve["ordering"] + _curve["holding"]
    _fig = px.line(_curve, x="Q", y=["ordering", "holding", "total"],
                   labels={"value": "Cost ($/year)", "variable": "Cost"},
                   title="Costs vs order quantity")
    _fig.add_vline(x=q_star, line_dash="dash")
    _fig
    return


@app.cell
def _(mo):
    mo.md("""
    ## Expéditions / *Shipments* (`data/datasets/shipments.csv`)
    Choisissez un transporteur : le tableau et le résumé se mettent à jour.
    *Pick a carrier: the table and the summary update.*
    """)
    return


@app.cell
def _(mo, pd):
    shipments = pd.read_csv(mo.notebook_dir().parent / "data" / "datasets" / "shipments.csv")
    carrier = mo.ui.dropdown(options=sorted(shipments["carrier"].unique()),
                             value="Purolator", label="Transporteur / carrier")
    carrier
    return carrier, shipments


@app.cell
def _(carrier, mo, shipments):
    _subset = shipments[shipments["carrier"] == carrier.value]
    mo.vstack([
        mo.md(f"**{len(_subset)}** shipments · average cost "
              f"**{_subset['cost_cad'].mean():,.2f} $** · total weight "
              f"**{_subset['weight_kg'].sum():,.0f} kg**"),
        mo.ui.table(_subset, selection=None),
    ])
    return


if __name__ == "__main__":
    app.run()
