import pandas as pd
import random
import base64
import io
from dash import Dash, dcc, html
from dash.dependencies import Input, Output, State
import dash_cytoscape as cyto
import dash_daq as daq
from dash import callback_context

# 直接從資料生成 Cytoscape 元素
def generate_cytoscape_elements(df, node_size=2):
    elements = []
    max_weight = 3
    nodes = set()
    
    # 添加節點和邊
    for _, row in df.iterrows():
        st_id_color = '#81AFBB' if row['st_id'] <= 20 else '#ED859D'
        
        # 確保每個節點只出現一次
        if row['st_id'] not in nodes:
            elements.append({'data': {'id': str(row['st_id']), 'label': f'{row["st_id"]}', 
                                      'score': node_size / 10, 'color': st_id_color}})
            nodes.add(row['st_id'])

        # 添加邊
        elements.append({'data': {'source': str(row['st_id']), 'target': str(row['order1']), 'weight': 3/max_weight}, 'color': '#888'})
        elements.append({'data': {'source': str(row['st_id']), 'target': str(row['order2']), 'weight': 2/max_weight}, 'color': '#888'})
        elements.append({'data': {'source': str(row['st_id']), 'target': str(row['order3']), 'weight': 1/max_weight}, 'color': '#888'})

    return elements

# 初始化 Dash 應用
app = Dash(__name__)

# Cytoscape 樣式配置
default_stylesheet = [
    {
        'selector': 'node',
        'style': {
            'label': 'data(label)',
            'width': 'mapData(score, 0, 1, 20, 60)',
            'height': 'mapData(score, 0, 1, 20, 60)',
            'font-size': '10px',
            'text-valign': 'center',
            'text-halign': 'center',
            'background-color': 'data(color)'
        }
    },
    {
        'selector': 'node:selected',
        'style': {
            'border-width': '2px',
            'border-color': '#877F6C',
            # 'background-color': '#877F6C',
            'overlay-opacity': 0.2
        }
    },
    {
        'selector': 'edge',
        'style': {
            'line-color': 'data(color)',
            'target-arrow-color': 'data(color)',
            'target-arrow-shape': 'triangle',
            'curve-style': 'bezier',
            'opacity': 0.8,  # 增加透明度
            'arrow-scale': 1.2,  # 調整箭頭的大小
            'width': f'mapData(weight, 0, 1, 0, 5)'
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
        ),
        html.Label("Change Node / Edge Color", style={'font-weight': 'bold', 'font-size': '17px'}),
        daq.ColorPicker(
            id='color-picker',
            value={'hex': '#81AFBB'},  # 初始顏色
            style={'margin-bottom': '10px'}
        ),
        html.Button("Change Color", id='update-color-button', n_clicks=0, 
                    style={'background-color': '#4CAF50', 'color': 'white',
                        'border': 'none', 'padding': '10px 20px',
                        'text-align': 'center', 'text-decoration': 'none',
                        'display': 'inline-block', 'font-size': '16px',
                        'border-radius': '5px', 'cursor': 'pointer', 'margin-bottom': '10px'})
    ], style={'width': '30%', 'display': 'inline-block', 'vertical-align': 'top', 'padding-left': '20px'})
], style={'display': 'flex', 'padding-left': '40px', 'padding-right': '40px'})

@app.callback(
    Output('cytoscape', 'elements'),
    [Input('upload-data', 'contents'),
     Input('node-size-slider', 'value'),
     Input('update-color-button', 'n_clicks')],
    [State('cytoscape', 'elements'),
     State('cytoscape', 'selectedNodeData'),
     State('cytoscape', 'selectedEdgeData'),
     State('color-picker', 'value')]
)
def update_graph(contents, node_size, n_clicks, existing_elements, selected_nodes, selected_edges, color_value):
    # 檢查 callback 觸發來源
    triggered = callback_context.triggered[0]['prop_id'].split('.')[0]

    # 如果是上傳資料
    if triggered == 'upload-data' and contents:
        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)
        try:
            df = pd.read_excel(io.BytesIO(decoded), dtype={'座號': 'str', '順位1': 'str', '順位2': 'str'})
            df.columns = ['st_id', 'order1', 'order2', 'order3']
            df.dropna(inplace=True)
            df = df.astype(int)  # 直接轉換為整數型態

            elements = generate_cytoscape_elements(df, node_size)
            return elements
        except Exception as e:
            print(e)
            return existing_elements  # 保留現有元素

    # 如果是調整節點大小
    elif triggered == 'node-size-slider':
        for element in existing_elements:
            if 'score' in element['data']:
                element['data']['score'] = node_size / 10

    # 如果是更新顏色按鈕
    elif triggered == 'update-color-button':
        if selected_nodes:
            # 更新選擇節點的顏色
            for node in selected_nodes:
                node_id = node['id']
                for element in existing_elements:
                    if element['data'].get('id') == node_id:
                        element['data']['color'] = color_value['hex']
        # 更新選擇邊的顏色
        if selected_edges:
            for edge in selected_edges:
                edge_id = edge['id']
                for element in existing_elements:
                    if element['data'].get('id') == edge_id:
                        element['data']['color'] = color_value['hex']

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

@app.callback(
    Output('cytoscape', 'stylesheet'),
    [Input('font-size-slider', 'value'),
     Input('text-position-dropdown', 'value'),
     Input('edge-width-slider', 'value')],
    State('cytoscape', 'stylesheet')
)
def update_stylesheet(font_size, text_position, edge_width_scale, current_stylesheet):
    # 初始化為當前的 stylesheet
    updated_stylesheet = current_stylesheet.copy()

    # 更新節點樣式
    node_style = next((style for style in updated_stylesheet if style['selector'] == 'node'), None)
    if node_style:
        node_style['style']['font-size'] = f'{font_size}px'
        node_style['style']['text-valign'] = text_position

    # 更新邊樣式
    edge_style = next((style for style in updated_stylesheet if style['selector'] == 'edge'), None)
    if edge_style:
        edge_style['style']['width'] = f'mapData(weight, 0, 1, 0, {edge_width_scale})'

    return updated_stylesheet

# 回調函數來生成模板
@app.callback(
    Output("download-template", "data"),
    Input("download-template-button", "n_clicks"),
    prevent_initial_call=True
)
def download_template(n_clicks):
    # 創建一個範例的模板 DataFrame
    template_data = pd.DataFrame({
        '座號': ['1', '2', '3', '4', '5', '6'],
        '順位1': ['2', '3', '4', '5', '6', '1'],
        '順位2': ['3', '4', '5', '6', '1', '2'],
        '順位3': ['4', '5', '6', '1', '2', '3']
    })
    
    # 生成 Excel 文件並提供下載
    return dcc.send_data_frame(template_data.to_excel, "template.xlsx", index=False)

if __name__ == '__main__':
    app.run_server(debug=True, host="0.0.0.0", port=8050)
