import dash
import dash_bootstrap_components as dbc
from script.data_preparation import initialize_data

# bootstrap theme
# https://bootswatch.com/lux/
external_stylesheets = [dbc.themes.LUX]

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

server = app.server

audiometries = initialize_data()
app.config.suppress_callback_exceptions = True