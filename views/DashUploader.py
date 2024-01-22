import uuid

import dash_mantine_components as dmc
from dash import html, Output, Input, State, callback, no_update, clientside_callback
from dash_iconify import DashIconify

import DataImportTask


def get_upload_component(configured_du, cid="uploader", upload_id=uuid.uuid1()):
    return html.Div([
        configured_du.Upload(
            id=cid,
            text='Drag and Drop files here or Click to upload!',
            max_file_size=100,  # 100 Mb,
            max_files=1,
            pause_button=True,
            filetypes=['csv', 'xlsx'],
            default_style={'width': '100%'},
            upload_id=upload_id
        )
    ],
        style={
            'textAlign': 'center',
            'width': '100%',
            'padding': '10px',
            'display': 'inline-block'
        }
    )


def get_upload_modal(du):
    return dmc.Modal(
        title="Data upload",
        id="file_import_modal",
        size="70%", zIndex=10000,
        opened=False,
        children=[
            get_upload_component(du),
            dmc.Space(h=20),
            dmc.Group(
                [
                    dmc.Button("Load Data", id="modal-submit-button", className='zoom',
                               loading=False),
                    dmc.Button(
                        "Close",
                        color="red",
                        variant="outline",
                        id="modal-close-button",
                        className='zoom'
                    ),
                ],
                position="right",
            )
        ]
    )


@callback(
    Output('file_import_modal', 'opened', allow_duplicate=True),
    Input('import-data-btn', 'n_clicks'),
    Input('modal-close-button', 'n_clicks'),
    State('file_import_modal', 'opened'),
    prevent_initial_call=True
)
def on_file_import_button_click(import_btn_clicked, close_btn_clicked, opened):
    if not import_btn_clicked and not close_btn_clicked:
        return no_update
    return not opened


@callback(
    Output('file_import_modal', 'opened', allow_duplicate=True),
    Output('notifications-container', 'children'),
    Output("modal-submit-button", "loading", allow_duplicate=True),
    Input('modal-submit-button', 'n_clicks'),
    State('local', 'data'),
    State('file_import_modal', 'opened'),
    prevent_initial_call=True
)
def on_load_data_button_clicked(load_data_clicked, local_storage, opened):
    if not load_data_clicked:
        return no_update

    DataImportTask.import_from_xlsx(local_storage)

    return not opened, dmc.Notification(
        title="File Upload",
        id="file-upload-notification",
        action="show",
        message="File uploaded successfully",
        icon=DashIconify(icon="ic:round-celebration"),
        style={"zIndex": 12000}
    ), False


clientside_callback(
    """
    function(n_clicks) {
        return true
    }
    """,
    Output('modal-submit-button', 'loading'),
    Input('modal-submit-button', 'n_clicks'),
    prevent_initial_call=True
)
