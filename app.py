from dash import Dash, dcc, html
import dash_cytoscape as cyto
import dash_daq as daq

from utils.graph_utilities import get_default_stylesheet
from utils.callbacks import register_callbacks

# 初始化 Dash 應用
app = Dash(
    __name__,
    external_stylesheets=["https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css"]
)

# Cytoscape 樣式配置
default_stylesheet = get_default_stylesheet()

# 設定 Dash 佈局
app.layout = html.Div([
    html.Div([
        # 包含 Cytoscape 的大區域
        html.Div([
            html.Div([
                # 標題與說明
                html.Label([
                    html.Span("房間室友偏好", style={'font-size': '48px', 'font-weight': 'bold'}),  # 首字母較大
                    html.Span("  網絡關係圖 ", style={'font-size': '32px', 'font-weight': 'bold'}),
                ], style={'display': 'inline-block', 'line-height': '1.2'}),
                # 使用 Font Awesome 圖標
                html.I(className="fa-solid fa-circle-info info-icon", id="info-icon", style={'font-size': '24px', 'margin-left': '10px'}),
                html.Span("按住Shift，可以圈選多個『節點/邊』來移動或編輯顏色(進階設定)", className="tooltip-text")
            ], style={'position': 'relative', 'display': 'inline-block', 'margin-bottom': '5px'}),
            
            dcc.Loading(
                id="loading-output",
                type="default",  # 加載動畫樣式，'default', 'circle', 'dot' 皆可
                children=[
                    cyto.Cytoscape(
                        id='cytoscape',
                        elements=[],  # 初始時沒有元素
                        layout={'name': 'cose'},
                        style={'width': '98%', 'height': '600px', 'border': '2px solid black'},
                        stylesheet=default_stylesheet,
                        panningEnabled=True,
                        zoomingEnabled=True,
                        boxSelectionEnabled=True,
                        autoungrabify=False,
                    ),
                    html.Div(id='hover-info', style={'margin-top': '20px', 'font-weight': 'bold'})
                ]
            )
        ], style={'width': '100%', 'display': 'inline-block', 'vertical-align': 'top'}),
        
        # 分組結果顯示區域
        html.Div([
            html.Div([                
                html.Div([
                    html.Div(id='group-results', style={'width': '100%', 'border-radius': '10px', 'background-color': '#f9f9f9', 'box-shadow': '0 1px 3px rgba(0, 0, 0, 0.1)'})
                ], style={'width': '900px', 'margin-bottom': '30px'})
            ])
        ], id='group-display', style={'display': 'none', 'margin-top': '30px', 'border-top': '1px solid #ccc'})
    ], style={'width': '70%', 'display': 'inline-block'}),
    html.Div([
        html.Label("步驟一：根據模板格式修改", style={'font-weight': 'bold', 'font-size': '22px', 'margin-bottom': '5px', 'display': 'block'}),
        html.Div([
            html.Button("下載模板", id='download-template-button', n_clicks=0, 
                        style={'background-color': '#4CAF50', 'color': 'white', 
                            'border': 'none', 'padding': '10px 20px', 
                            'text-align': 'center', 'text-decoration': 'none', 
                            'display': 'inline-block', 'font-size': '16px',
                            'border-radius': '5px', 'cursor': 'pointer', 'margin-bottom': '10px'}),
            dcc.Download(id="download-template"),
        ]),

        html.Label("步驟二：上傳Excel", style={'font-weight': 'bold', 'font-size': '22px', 'margin-bottom': '5px', 'display': 'block'}),
        dcc.Upload(
            id='upload-data',
            children=html.Div(html.A('選擇檔案(excel)')),
            style={
                'width': '100%',
                'height': '60px',
                'lineHeight': '60px',
                'borderWidth': '1px',
                'borderStyle': 'dashed',
                'borderRadius': '5px',
                'textAlign': 'center',
                'margin': '10px'
            },
            multiple=False
        ),
        html.Div(id='file-name', style={'textAlign': 'center', 'margin-bottom': '10px'}),  # 顯示檔案名稱

        html.Div([
            html.Label("步驟三：男生/女生 相關設定", style={'font-weight': 'bold', 'font-size': '22px', 'margin-bottom': '5px', 'display': 'block'}),

            # Combined Male and Female ID Range and Group Sizes
            html.Div([
                # Male Configuration
                html.Div([
                    html.Label("男生", style={'font-weight': 'bold', 'font-size': '17px'}),
                    html.Div([
                        html.Label("編號範圍", style={'font-size': '16px', 'margin-right': '10px'}),
                        dcc.Input(id='male-start', type='number', min=1, max=40, value=1,
                                style={'width': '60px', 'padding': '5px', 'border-radius': '5px', 'border': '1px solid #ccc'}),
                        html.Span("~", style={'font-size': '16px', 'padding': '0 10px'}),
                        dcc.Input(id='male-end', type='number', min=1, max=40, value=20,
                                style={'width': '60px', 'padding': '5px', 'border-radius': '5px', 'border': '1px solid #ccc'}),
                    ], style={'display': 'flex', 'align-items': 'center', 'margin-bottom': '10px'}),

                    html.Div([
                        html.Label("分組大小", style={'font-size': '16px', 'margin-right': '10px'}),
                        dcc.Input(id='male-group-sizes', type='text', value='4, 4, 4, 2', placeholder='例如：4, 4, 4, 2',
                                style={'width': '220px', 'padding': '5px', 'border-radius': '5px', 'border': '1px solid #ccc'}),
                    ], style={'display': 'flex', 'align-items': 'center'}),
                ], style={'background-color': '#f1f1f1', 'padding': '15px', 'border-radius': '10px', 'box-shadow': '0 1px 3px rgba(0, 0, 0, 0.1)', 'margin-bottom': '10px'}),
                
                # Female Configuration
                html.Div([
                    html.Label("女生", style={'font-weight': 'bold', 'font-size': '17px'}),
                    html.Div([
                        html.Label("編號範圍", style={'font-size': '16px', 'margin-right': '10px'}),
                        dcc.Input(id='female-start', type='number', min=1, max=40, value=21,
                                style={'width': '60px', 'padding': '5px', 'border-radius': '5px', 'border': '1px solid #ccc'}),
                        html.Span("~", style={'font-size': '16px', 'padding': '0 10px'}),
                        dcc.Input(id='female-end', type='number', min=1, max=40, value=40,
                                style={'width': '60px', 'padding': '5px', 'border-radius': '5px', 'border': '1px solid #ccc'}),
                    ], style={'display': 'flex', 'align-items': 'center', 'margin-bottom': '10px'}),

                    html.Div([
                        html.Label("分組大小", style={'font-size': '16px', 'margin-right': '10px'}),
                        dcc.Input(id='female-group-sizes', type='text', value='4, 4, 4, 2', placeholder='例如：4, 4, 4, 2',
                                style={'width': '220px', 'padding': '5px', 'border-radius': '5px', 'border': '1px solid #ccc'}),
                    ], style={'display': 'flex', 'align-items': 'center'}),
                ], style={'background-color': '#f1f1f1', 'padding': '15px', 'border-radius': '10px', 'box-shadow': '0 1px 3px rgba(0, 0, 0, 0.1)', 'margin-bottom': '10px'}),
            ], style={'max-width': '600px', 'margin': 'auto', 'padding': '10px'}),

            # Warning Div
            html.Div(id='warning', style={'color': 'red', 'font-size': '16px', 'margin-top': '2px'}),
            # Validation Div
            html.Div(id='group-size-verification', style={'color': 'red', 'font-size': '16px', 'margin-top': '2px'}),
        ], style={'padding': '5px'}),

        html.Div([
            html.Button("隨機重新繪圖", id='random-seed-button', n_clicks=0, 
                        style={'background-color': '#4CAF50', 'color': 'white', 
                            'border': 'none', 'padding': '10px 20px', 
                            'text-align': 'center', 'text-decoration': 'none', 
                            'display': 'inline-block', 'font-size': '16px',
                            'border-radius': '5px', 'cursor': 'pointer'}),
            html.Div(id='seed-value', style={'display': 'inline-block', 'margin-left': '10px', 'visibility': 'hidden'})  # 顯示當前 Seed
        ], style={'display': 'flex', 'align-items': 'center', 'margin-bottom': '20px', 'margin-top': '5px'}),
        
        html.Div([
            html.Label("步驟四：選擇分組模式", style={'font-weight': 'bold', 'font-size': '22px', 'margin-bottom': '5px', 'display': 'block'}),
            
            html.Div([
                dcc.RadioItems(
                    id='preference-options',
                    options=[
                        {'label': '符合多數學生意願', 'value': 'option1'},
                        {'label': '人數少的組別也想要同伴', 'value': 'option2'},
                        {'label': '邊緣人的春天', 'value': 'option3'}
                    ],
                    value='option1',  # 預設為第一個選項
                    labelStyle={
                        'display': 'inline-block', 
                        'padding': '10px 20px', 
                        'border-radius': '5px',
                        'margin': '5px', 
                        'border': '1px solid #ccc', 
                        'cursor': 'pointer',
                        'background-color': '#f5f5f5',
                        'font-size': '16px',
                        'color': '#333'
                    },
                    inputStyle={
                        'margin-right': '10px',
                        'transform': 'scale(1.2)',  # 放大選項按鈕
                        'vertical-align': 'middle'
                    }
                ),
            ], style={
                'background-color': '#f9f9f9', 
                'padding': '15px', 
                'border-radius': '10px', 
                'box-shadow': '0 1px 3px rgba(0, 0, 0, 0.1)', 
                'margin-bottom': '20px',
                'display': 'inline-block',
                'width': '100%'
            })
        ]),

        html.Div([
            html.Button(
                '網絡圖進階設定', 
                id='advanced-settings-toggle',
                n_clicks=0,
                style={'background-color': '#4CAF50', 'color': 'white', 
                            'border': 'none', 'padding': '10px 20px', 
                            'text-align': 'center', 'text-decoration': 'none', 
                            'display': 'inline-block', 'font-size': '16px',
                            'border-radius': '5px', 'cursor': 'pointer', 'margin-bottom': '10px'}),
            html.Div([
                html.Label("繪製樣式", style={'font-weight': 'bold', 'font-size': '17px'}),
                dcc.Dropdown(
                    id='layout-dropdown',
                    options=[
                        {'label': 'Cose', 'value': 'cose'},
                        {'label': 'Preset', 'value': 'preset'},
                        {'label': 'Grid', 'value': 'grid'},
                        {'label': 'Circle', 'value': 'circle'},
                        {'label': 'Concentric', 'value': 'concentric'}
                    ],
                    value='cose',
                    clearable=False
                ),
                html.Label("節點大小", style={'font-weight': 'bold', 'font-size': '17px'}),
                dcc.Slider(
                    id='node-size-slider',
                    min=1,
                    max=10,
                    step=1,
                    value=2,
                    marks={i: str(i) for i in range(1, 11)}
                ),
                html.Label("邊寬", style={'font-weight': 'bold', 'font-size': '17px'}),
                dcc.Slider(
                    id='edge-width-slider',
                    min=1,
                    max=10,
                    step=1,
                    value=5,
                    marks={i: str(i) for i in range(1, 11)}
                ),
                html.Label("節點之間的距離", style={'font-weight': 'bold', 'font-size': '17px'}),
                dcc.Slider(
                    id='node-repulsion-slider',
                    min=1,
                    max=10,
                    step=1,
                    value=4,
                    marks={i: str(i) for i in range(1, 11)}
                ),
                html.Label("文字大小", style={'font-weight': 'bold', 'font-size': '17px'}),
                dcc.Slider(
                    id='font-size-slider',
                    min=5,
                    max=30,
                    step=1,
                    value=12,
                    marks={i: str(i) for i in range(5, 35, 5)}
                ),
                html.Label("文字位置", style={'font-weight': 'bold', 'font-size': '17px'}),
                dcc.Dropdown(
                    id='text-position-dropdown',
                    options=[
                        {'label': 'Top', 'value': 'top'},
                        {'label': 'Center', 'value': 'center'},
                        {'label': 'Bottom', 'value': 'bottom'}
                    ],
                    value='center',
                    clearable=False
                ),
                html.Label("手動改變『節點/邊』的顏色", style={'font-weight': 'bold', 'font-size': '17px'}),
                daq.ColorPicker(
                    id='color-picker',
                    value={'hex': '#81AFBB'},  # 初始顏色
                    style={'margin-bottom': '10px'}
                ),
                html.Button("更新顏色", id='update-color-button', n_clicks=0, 
                            style={'background-color': '#4CAF50', 'color': 'white',
                                'border': 'none', 'padding': '10px 20px',
                                'text-align': 'center', 'text-decoration': 'none',
                                'display': 'inline-block', 'font-size': '16px',
                                'border-radius': '5px', 'cursor': 'pointer', 'margin-bottom': '10px'})
            ], id='advanced-settings-content', style={'display': 'none'})
        ])
    ], style={'width': '30%', 'display': 'inline-block', 'vertical-align': 'top', 'padding-left': '20px', 'margin-top': '30px'})
], style={'display': 'flex', 'padding-left': '40px', 'padding-right': '40px'})

# 註冊回調
register_callbacks(app)

if __name__ == '__main__':
    app.run_server(debug=True, host="0.0.0.0", port=8050)
