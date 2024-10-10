import pandas as pd
import random
import base64
import io
from dash import Dash, dcc, html
from dash.dependencies import Input, Output, State
import dash_cytoscape as cyto

# 直接從資料生成 Cytoscape 元素
def generate_cytoscape_elements(df, scale_factor=5, node_size=2):
    elements = []
    max_weight = 3  # 因為權重範圍已知 (1-3)，所以設為3即可
    nodes = set()
    
    # 添加節點和邊
    for _, row in df.iterrows():
        # 設定節點顏色
        st_id_color = '#81AFBB' if row['st_id'] <= 20 else '#ED859D'
        order1_color = '#81AFBB' if row['order1'] <= 20 else '#ED859D'
        order2_color = '#81AFBB' if row['order2'] <= 20 else '#ED859D'
        order3_color = '#81AFBB' if row['order3'] <= 20 else '#ED859D'
        
        # 確保每個節點只出現一次
        if row['st_id'] not in nodes:
            elements.append({'data': {'id': str(row['st_id']), 'label': f'{row["st_id"]}', 'score': node_size / 10},
                             'style': {'background-color': st_id_color}})
            nodes.add(row['st_id'])
        if row['order1'] not in nodes:
            elements.append({'data': {'id': str(row['order1']), 'label': f'{row["order1"]}', 'score': node_size / 10},
                             'style': {'background-color': order1_color}})
            nodes.add(row['order1'])
        if row['order2'] not in nodes:
            elements.append({'data': {'id': str(row['order2']), 'label': f'{row["order2"]}', 'score': node_size / 10},
                             'style': {'background-color': order2_color}})
            nodes.add(row['order2'])
        if row['order3'] not in nodes:
            elements.append({'data': {'id': str(row['order3']), 'label': f'{row["order3"]}', 'score': node_size / 10},
                             'style': {'background-color': order3_color}})
            nodes.add(row['order3'])

        # 添加邊，並依照權重調整寬度
        elements.append({'data': {'source': str(row['st_id']), 'target': str(row['order1']), 'weight': 3},
                         'style': {'width': (3 / max_weight) * scale_factor}})
        elements.append({'data': {'source': str(row['st_id']), 'target': str(row['order2']), 'weight': 2},
                         'style': {'width': (2 / max_weight) * scale_factor}})
        elements.append({'data': {'source': str(row['st_id']), 'target': str(row['order3']), 'weight': 1},
                         'style': {'width': (1 / max_weight) * scale_factor}})

    return elements

# 初始化 Dash 應用
app = Dash(__name__)

# Cytoscape 樣式配置
default_stylesheet = [
    {
        'selector': 'node',
        'style': {
            'label': 'data(label)',
            'width': 'mapData(score, 0, 0.5, 20, 60)',
            'height': 'mapData(score, 0, 0.5, 20, 60)',
            'font-size': '10px',
            'text-valign': 'center',
            'text-halign': 'center'
        }
    },
    {
        'selector': 'node:selected',
        'style': {
            'border-width': '6px',
            'border-color': '#FF4500',
            'background-color': '#FFD700',
            'overlay-opacity': 0.2
        }
    },
    {
        'selector': 'edge',
        'style': {
            'line-color': '#888',
            'target-arrow-color': '#888',
            'target-arrow-shape': 'triangle',
            'curve-style': 'bezier'
        }
    }
]

# 設定 Dash 佈局
app.layout = html.Div([
    html.Div([
        cyto.Cytoscape(
            id='cytoscape',
            elements=[],  # 初始時沒有元素
            layout={'name': 'cose'},
            style={'width': '800px', 'height': '600px', 'border': '2px solid black'},
            stylesheet=default_stylesheet,
            panningEnabled=True,
            zoomingEnabled=True,
            boxSelectionEnabled=True,
            autoungrabify=False,
        )
    ], style={'width': '70%', 'display': 'inline-block', 'vertical-align': 'top'}),
    html.Div([
        dcc.Upload(
            id='upload-data',
            children=html.Div(['Drag and Drop or ', html.A('Select a File')]),
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
            html.Button("Download Template", id='download-template-button', n_clicks=0, 
                        style={'background-color': '#4CAF50', 'color': 'white', 
                            'border': 'none', 'padding': '10px 20px', 
                            'text-align': 'center', 'text-decoration': 'none', 
                            'display': 'inline-block', 'font-size': '16px',
                            'border-radius': '5px', 'cursor': 'pointer', 'margin-bottom': '10px'}),
            dcc.Download(id="download-template"),
        ]),
        html.Label("Layout Style", style={'font-weight': 'bold', 'font-size': '17px'}),
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
        html.Div([
            html.Button("re-Layout", id='random-seed-button', n_clicks=0, 
                        style={'background-color': '#4CAF50', 'color': 'white', 
                            'border': 'none', 'padding': '10px 20px', 
                            'text-align': 'center', 'text-decoration': 'none', 
                            'display': 'inline-block', 'font-size': '16px',
                            'border-radius': '5px', 'cursor': 'pointer'}),
            html.Div(id='seed-value', style={'display': 'inline-block', 'margin-left': '10px'})  # 顯示當前 Seed
        ], style={'display': 'flex', 'align-items': 'center', 'margin-bottom': '20px', 'margin-top': '20px'}),
        html.Label("Node Size", style={'font-weight': 'bold', 'font-size': '17px'}),
        dcc.Slider(
            id='node-size-slider',
            min=1,
            max=10,
            step=1,
            value=2,
            marks={i: str(i) for i in range(1, 11)}
        ),
        html.Label("Edge Width Scale Factor", style={'font-weight': 'bold', 'font-size': '17px'}),
        dcc.Slider(
            id='edge-width-slider',
            min=1,
            max=10,
            step=1,
            value=5,
            marks={i: str(i) for i in range(1, 11)}
        ),
        html.Label("Node Repulsion (Distance)", style={'font-weight': 'bold', 'font-size': '17px'}),
        dcc.Slider(
            id='node-repulsion-slider',
            min=1,
            max=10,
            step=1,
            value=4,
            marks={i: str(i) for i in range(1, 11)}
        ),
        html.Label("Font Size", style={'font-weight': 'bold', 'font-size': '17px'}),
        dcc.Slider(
            id='font-size-slider',
            min=5,
            max=30,
            step=1,
            value=12,
            marks={i: str(i) for i in range(5, 35, 5)}
        ),
        html.Label("Text Position", style={'font-weight': 'bold', 'font-size': '17px'}),
        dcc.Dropdown(
            id='text-position-dropdown',
            options=[
                {'label': 'Top', 'value': 'top'},
                {'label': 'Center', 'value': 'center'},
                {'label': 'Bottom', 'value': 'bottom'}
            ],
            value='center',
            clearable=False
        )
    ], style={'width': '30%', 'display': 'inline-block', 'vertical-align': 'top', 'padding-left': '20px'})
], style={'display': 'flex', 'padding-left': '40px', 'padding-right': '40px'})

# 處理檔案上傳並更新 Cytoscape 元素的回調函數
@app.callback(
    Output('cytoscape', 'elements'),
    [Input('upload-data', 'contents'),
     Input('node-size-slider', 'value'),
     Input('edge-width-slider', 'value')],
    State('cytoscape', 'elements')
)
def update_graph(contents, node_size, scale_factor, existing_elements):
    if contents is None and not existing_elements:
        return []  # 如果沒有上傳，並且不存在現有的元素，返回空列表

    if contents:
        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)
        try:
            df = pd.read_excel(io.BytesIO(decoded), dtype={'座號': 'str', '順位1': 'str', '順位2': 'str'})
            df.columns = ['st_id', 'order1', 'order2', 'order3']
            df.dropna(inplace=True)
            for col in ['st_id', 'order1', 'order2', 'order3']:
                df[col] = df[col].astype('int')

            # 生成 Cytoscape 元素
            return generate_cytoscape_elements(df, scale_factor, node_size)
        except Exception as e:
            print(e)
            return existing_elements  # 如果上傳失敗，保留現有的元素

    return existing_elements

# 更新顯示的檔案名稱
@app.callback(
    Output('file-name', 'children'),
    Input('upload-data', 'filename')
)
def display_file_name(filename):
    if filename is None:
        return ""
    return f"Current File: {filename}"

# 更新 layout 和 Seed 值的顯示
@app.callback(
    [Output('cytoscape', 'layout'),
     Output('seed-value', 'children')],
    [Input('layout-dropdown', 'value'),
     Input('random-seed-button', 'n_clicks'),
     Input('node-repulsion-slider', 'value')]
)
def update_layout(layout_value, n_clicks, node_repulsion):
    seed = random.randint(0, 1000) if n_clicks > 0 else 46
    layout = {'name': layout_value, 'randomize': True, 'seed': seed}
    if layout_value == 'cose':
        layout['nodeRepulsion'] = node_repulsion * 10000
    return layout, f"Seed: {seed}"

# 其他回調函數保持不變
@app.callback(
    Output('cytoscape', 'stylesheet'),
    [Input('font-size-slider', 'value'),
     Input('text-position-dropdown', 'value')]
)
def update_stylesheet(font_size, text_position):
    return [
        {
            'selector': 'node',
            'style': {
                'label': 'data(label)',
                'width': 'mapData(score, 0, 0.5, 20, 60)',
                'height': 'mapData(score, 0, 0.5, 20, 60)',
                'font-size': f'{font_size}px',
                'text-valign': text_position,
                'text-halign': 'center'
            }
        },
        {
            'selector': 'node:selected',
            'style': {
                'border-width': '2px',
                'border-color': '#877F6C',
                'background-color': '#877F6C',
                'overlay-opacity': 0.2
            }
        },
        {
            'selector': 'edge',
            'style': {
                'line-color': '#888',
                'target-arrow-color': '#888',
                'target-arrow-shape': 'triangle',
                'curve-style': 'bezier',
                'opacity': 0.8,  # 增加透明度
                'arrow-scale': 1.2  # 調整箭頭的大小
            }
        },
        {
            'selector': 'edge:selected',
            'style': {
                'border-width': '2px',
                'border-color': '#877F6C',
                'background-color': '#877F6C',
                'overlay-opacity': 0.2
            }
        }
    ]

# 回調函數來生成模板
@app.callback(
    Output("download-template", "data"),
    Input("download-template-button", "n_clicks"),
    prevent_initial_call=True
)
def download_template(n_clicks):
    # 創建一個範例的模板 DataFrame
    template_data = pd.DataFrame({
        '座號': ['1', '2', '3'],
        '順位1': ['2', '3', '1'],
        '順位2': ['3', '1', '2'],
        '順位3': ['1', '2', '3']
    })
    
    # 生成 Excel 文件並提供下載
    return dcc.send_data_frame(template_data.to_excel, "template.xlsx", index=False)

if __name__ == '__main__':
    app.run_server(debug=True, host="0.0.0.0", port=8050)
