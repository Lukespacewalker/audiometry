import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc
from apps import trend, niosh, osha, overview, refer

from app import app

# import all pages in the app

# building the navigation bar
# https://github.com/facultyai/dash-bootstrap-components/blob/master/examples/advanced-component-usage/Navbars.py
dropdown = dbc.DropdownMenu(
    children=[
        dbc.DropdownMenuItem("Overview", href="/"),
        dbc.DropdownMenuItem("NIOSH", href="/niosh"),
        dbc.DropdownMenuItem("OSHA", href="/osha"),
        dbc.DropdownMenuItem("Refer", href="/refer"),
        dbc.DropdownMenuItem("Trend", href="/trend"),
    ],
    nav=True,
    in_navbar=True,
    label="Menu",
)

navbar = dbc.Navbar(
    dbc.Container(
        [
            html.A(
                # Use row and col to control vertical alignment of logo / brand
                children=[dbc.Row(
                    [
                        dbc.Col(html.Img(src="/assets/audiowav.svg", height="30px")),
                        dbc.Col(dbc.NavbarBrand("Audiometry", className="ml-2")),
                    ],
                    align="center",
                    no_gutters=True,
                ),
                    dbc.Row(
                        [dbc.Col(children="Beta (Powered by DASH + Python)", style={"color": "white"})]
                    )
                ],
                href="/home",
            ),
            dbc.NavbarToggler(id="navbar-toggler2"),
            dbc.Collapse(
                dbc.Nav(
                    # right align dropdown menu with ml-auto className
                    [dropdown], className="ml-auto", navbar=True
                ),
                id="navbar-collapse2",
                navbar=True,
            ),
        ]
    ),
    color="dark",
    dark=True,
    className="mb-4",
)


def toggle_navbar_collapse(n, is_open):
    if n:
        return not is_open
    return is_open


for i in [2]:
    app.callback(
        Output(f"navbar-collapse{i}", "is_open"),
        [Input(f"navbar-toggler{i}", "n_clicks")],
        [State(f"navbar-collapse{i}", "is_open")],
    )(toggle_navbar_collapse)

# embedding the navigation bar
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    navbar,
    html.Div(id='page-content')
])


@app.callback(Output('page-content', 'children'),
              [Input('url', 'pathname')])
def display_page(pathname):
    pass
    if pathname == '/niosh':
        return niosh.layout
    elif pathname == '/osha':
        return osha.layout
    elif pathname == '/trend':
        return trend.layout
    elif pathname == '/refer':
        return refer.layout
    else:
        return overview.layout


if __name__ == '__main__':
    app.run_server(host='127.0.0.1', debug=False)
