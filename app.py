import os

import dash_mantine_components as dmc
from dash import Dash
from dash_iconify import DashIconify

import AppConfig
import DataImportTask
from db import engine
from sqlmodel import SQLModel
from dash import Output, Input, html, callback, Patch
import dash_uploader as du
import dash_core_components as dcc

from views import Home, DashUploader

app = Dash(
    __name__,
    external_stylesheets=[
        "https://fonts.googleapis.com/css2?family=Inter:wght@100;200;300;400;500;900&display=swap"
    ],
)

du.configure_upload(app, os.path.join(os.getcwd(), "stage"))

app.layout = dmc.MantineProvider(
    theme={
        "colorScheme": "dark",
        "colors": {
            "wine-red": ["#C85252"] * 9,
            "dark-green": ["#009688"] * 9,
            "dark-yellow": ["#5C6BC0"] * 9,
            "dark-gray": ["#212121"] * 9,
            "light-cyan": ["#B2EBF2"] * 9
        },
        "fontFamily": "'Inter', sans-serif",
        "primaryColor": "indigo",
        "components": {
            "Button": {"styles": {"root": {"fontWeight": 400}}},
            "Alert": {"styles": {"title": {"fontWeight": 500}}},
        },
    },
    inherit=True,
    withGlobalStyles=True,
    withNormalizeCSS=True,
    children=dmc.NotificationsProvider([
        dcc.Store(id='local', storage_type='local', data={}),
        html.Div(id="notifications-container"),
        Home.get_home_page(),
        DashUploader.get_upload_modal(du)
    ]),
)


@du.callback(
    output=Output("local", "data", allow_duplicate=True),
    id="uploader",
)
def on_upload_completion(status):
    patch_object = Patch()
    patch_object[AppConfig.LAST_DATASET_UPLOADED] = status[0]
    return patch_object


if __name__ == "__main__":
    SQLModel.metadata.create_all(engine)
    app.run_server()
