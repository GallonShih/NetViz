import pandas as pd
import networkx as nx
import random
from dash import dcc, html
from dash.dependencies import Input, Output, State
from dash import callback_context
from utils.graph_utilities import (
    generate_cytoscape_elements,
    generate_layout,
    create_directed_graph,
    apply_partition_and_color,
    reset_elements_color
)
from utils.file_processing import process_uploaded_file
import random

def register_callbacks(app):

    @app.callback(
        Output('cytoscape', 'elements'),
        [Input('upload-data', 'contents'),
         Input('male-start', 'value'), Input('male-end', 'value'),
         Input('female-start', 'value'), Input('female-end', 'value'),
         Input('male-group-sizes', 'value'),  # 新增 male group sizes 輸入
         Input('female-group-sizes', 'value'),  # 新增 female group sizes 輸入
         Input('node-size-slider', 'value'),
         Input('update-color-button', 'n_clicks'),
         Input('preference-options', 'value')],
        [State('cytoscape', 'elements'),
         State('cytoscape', 'selectedNodeData'),
         State('cytoscape', 'selectedEdgeData'),
         State('color-picker', 'value')]
    )
    def update_graph(contents, male_start, male_end, female_start, female_end, male_group_sizes, female_group_sizes, node_size, n_clicks, preference_option, existing_elements, selected_nodes, selected_edges, color_value):
        triggered = callback_context.triggered[0]['prop_id'].split('.')[0]
        
        regen_triggers = [
            'upload-data',
            'male-start',
            'male-end', 'male-end',
            'female-start', 'female-end',
            'male-group-sizes', 'female-group-sizes',
            'preference-options'
        ]
        if triggered in regen_triggers:
            # 使用共用的验证和警告函数
            warning_message, validation_message, validation_style, male_group_check, female_group_check, df = validate_and_process_data(
                contents, male_start, male_end, female_start, female_end, male_group_sizes, female_group_sizes
            )
            if df is not None:
                if triggered == 'upload-data':
                    # 生成 Cytoscape 元素
                    existing_elements = generate_cytoscape_elements(df, node_size)

                if validation_message == "Group size verification successful" and warning_message == "":
                    # if triggered in ['preference-options', '']
                    update_target = 'both'
                    # if 'male-group-sizes' == triggered:
                    #     update_target = 'male'
                    # elif 'female-group-sizes' == triggered:
                    #     update_target = 'female'

                    existing_elements = apply_partition_and_color(
                        df, (male_start, male_end), (female_start, female_end), 
                        existing_elements, male_group_sizes, female_group_sizes, 
                        preference_option, update_target
                    )
                else:
                    update_target = 'both'
                    if "Warning" not in male_group_check and warning_message == "":
                        update_target = 'female'
                    elif "Warning" not in female_group_check and warning_message == "":
                        update_target = 'male'

                    existing_elements = reset_elements_color(
                        existing_elements, (male_start, male_end), 
                        (female_start, female_end), update_target
                    )

        # 处理节点大小或颜色变化
        if triggered == 'node-size-slider':
            for element in existing_elements:
                if 'score' in element['data']:
                    element['data']['score'] = node_size / 10

        elif triggered == 'update-color-button':
            if selected_nodes:
                for node in selected_nodes:
                    node_id = node['id']
                    for element in existing_elements:
                        if element['data'].get('id') == node_id:
                            element['data']['color'] = color_value['hex']
            if selected_edges:
                for edge in selected_edges:
                    edge_id = edge['id']
                    for element in existing_elements:
                        if element['data'].get('id') == edge_id:
                            element['data']['color'] = color_value['hex']

        return existing_elements
    
    @app.callback(
        [Output('warning', 'children'),
         Output('group-size-verification', 'children'),
         Output('group-size-verification', 'style')],
        [Input('upload-data', 'contents'),
         Input('male-start', 'value'), Input('male-end', 'value'),
         Input('female-start', 'value'), Input('female-end', 'value'),
         Input('male-group-sizes', 'value'),  # 新增 male group sizes 輸入
         Input('female-group-sizes', 'value'),  # 新增 female group sizes 輸入
         Input('update-color-button', 'n_clicks')]
    )
    def update_msg(contents, male_start, male_end, female_start, female_end, male_group_sizes, female_group_sizes, n_clicks):
        # 直接调用共用的验证和警告函数
        warning_message, validation_message, validation_style, _, _, _ = validate_and_process_data(
            contents, male_start, male_end, female_start, female_end, male_group_sizes, female_group_sizes
        )
        return warning_message, validation_message, validation_style

    @app.callback(
        [Output('advanced-settings-content', 'style'),
         Output('advanced-settings-toggle', 'children')],
        [Input('advanced-settings-toggle', 'n_clicks')]
    )
    def toggle_advanced_settings(n_clicks):
        if n_clicks % 2 == 1:  # Odd clicks -> show settings
            return {'display': 'block'}, '網絡圖進階設定（隱藏）'
        else:  # Even clicks -> hide settings
            return {'display': 'none'}, '網絡圖進階設定（展開）'

    @app.callback(
        Output('file-name', 'children'),
        Input('upload-data', 'filename')
    )
    def display_file_name(filename):
        if filename is None:
            return ""
        return f"Current File: {filename}"

    @app.callback(
        [Output('cytoscape', 'layout'),
         Output('seed-value', 'children')],
        [Input('layout-dropdown', 'value'),
         Input('random-seed-button', 'n_clicks'),
         Input('node-repulsion-slider', 'value')]
    )
    def update_layout(layout_value, n_clicks, node_repulsion):
        seed = random.randint(0, 1000) if n_clicks > 0 else 46
        layout = generate_layout(layout_value, seed, node_repulsion)
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

    @app.callback(
        Output("download-template", "data"),
        Input("download-template-button", "n_clicks"),
        prevent_initial_call=True
    )
    def download_template(n_clicks):
        # 定義座號範圍
        group1 = list(range(1, 15))   # 1~14
        group2 = list(range(21, 35))  # 21~34

        # 定義小團體偏好
        group1_subgroups = [
            list(range(1, 5)),  # 1~4
            list(range(5, 9)),  # 5~8
            list(range(9, 15))  # 9~14
        ]
        group2_subgroups = [
            list(range(21, 25)),  # 21~24
            list(range(25, 29)),  # 24~28
            list(range(29, 35))   # 29~34
        ]

        # 加權選擇偏好
        def weighted_random_choice(choices, weights):
            total = sum(weights)
            r = random.uniform(0, total)
            upto = 0
            for choice, weight in zip(choices, weights):
                if upto + weight >= r:
                    return choice
                upto += weight

        # 根據小團體優先從小組內選擇順位，減少跨組的可能性
        def generate_order_with_preference(group, subgroups, isolated_member):
            order1 = []
            order2 = []
            order3 = []
            for student in group:
                # 找到學生所在的小組
                subgroup = [sg for sg in subgroups if student in sg][0]

                # 如果學生是孤立者，則他可以正常選擇其他人
                if student == isolated_member:
                    # 孤立者可以選擇小組內其他人，或者全組其他人
                    possible_choices = [s for s in group if s != student]
                    order1.append(weighted_random_choice(possible_choices, [1] * len(possible_choices)))
                    order2.append(weighted_random_choice(possible_choices, [1] * len(possible_choices)))
                    order3.append(weighted_random_choice(possible_choices, [1] * len(possible_choices)))
                    continue

                # 對於其他人，排除孤立者
                possible_choices = [s for s in subgroup if s != student and s != isolated_member]
                other_choices = [s for s in group if s not in possible_choices and s != student and s != isolated_member]

                # 設置選擇權重，讓同組優先
                order1.append(weighted_random_choice(possible_choices + other_choices, [1.0] * len(possible_choices) + [0.0] * len(other_choices)))
                order2.append(weighted_random_choice(possible_choices + other_choices, [0.95] * len(possible_choices) + [0.05] * len(other_choices)))
                order3.append(weighted_random_choice(possible_choices + other_choices, [0.9] * len(possible_choices) + [0.1] * len(other_choices)))

            return order1, order2, order3

        # 隨機選擇一個孤立者，從 group1 和 group2 各選一個
        isolated_member_group1 = random.choice(group1)
        isolated_member_group2 = random.choice(group2)

        # 生成兩個分組的順位，考慮小團體偏好並排除孤立者
        order1_group1, order2_group1, order3_group1 = generate_order_with_preference(group1, group1_subgroups, isolated_member_group1)
        order1_group2, order2_group2, order3_group2 = generate_order_with_preference(group2, group2_subgroups, isolated_member_group2)

        # 合併生成 DataFrame
        template_data = pd.DataFrame({
            '座號': group1 + group2,
            '順位1': order1_group1 + order1_group2,
            '順位2': order2_group1 + order2_group2,
            '順位3': order3_group1 + order3_group2
        })

        # 將隨機生成的模板導出為 Excel 文件
        return dcc.send_data_frame(template_data.to_excel, "template.xlsx", index=False)

    # 分組結果回調
    @app.callback(
        [Output('group-results', 'children'),
        Output('group-display', 'style')],
        [Input('cytoscape', 'elements'),
        Input('group-size-verification', 'children'),
        Input('warning', 'children'),
        Input('male-start', 'value'),
        Input('male-end', 'value'),
        Input('female-start', 'value'),
        Input('female-end', 'value')]
    )
    def display_group_results(elements, validation_message, warning_message, male_start, male_end, female_start, female_end):
        # 當驗證成功且無警告時才顯示分組結果
        if validation_message == "Group size verification successful" and warning_message == "":
            
            # 男生和女生的範圍
            male_range = set(range(male_start, male_end + 1))
            female_range = set(range(female_start, female_end + 1))
            
            male_groups = {}
            female_groups = {}

            # 先從elements提取節點並根據顏色進行分組
            for element in elements:
                if 'source' not in element['data']:
                    node_id = int(element['data']['id'])  # 節點ID
                    color = element['data'].get('color', 'none')  # 顏色標識分組
                    
                    if node_id in male_range:
                        if color not in male_groups:
                            male_groups[color] = []
                        male_groups[color].append(node_id)
                    elif node_id in female_range:
                        if color not in female_groups:
                            female_groups[color] = []
                        female_groups[color].append(node_id)
            
            # 合併顯示男生和女生的分組結果
            group_results_html = [
                html.H3("分組結果", style={'font-size': '22px', 'font-weight': 'bold', 'margin-bottom': '15px', 'text-align': 'left'}),
                html.Hr(style={'border-top': '1px solid #ccc', 'margin-bottom': '15px'})
            ]

            # 男生分組結果
            group_results_html.append(html.H4("男生分組", style={'font-size': '20px', 'font-weight': 'bold', 'margin-top': '10px', 'color': '#007BFF'}))
            for i, (color, group) in enumerate(sorted(male_groups.items(), key=lambda x: min(x[1])), 1):
                group_results_html.append(html.Div(
                    [
                        html.Span(f"組別 {i}: ", style={'font-weight': 'bold', 'font-size': '18px'}),
                        html.Span(f"{', '.join(map(str, sorted(group)))}", style={'color': color, 'font-size': '18px'})
                    ], style={'margin-left': '10px'}
                ))

            # 女生分組結果
            group_results_html.append(html.H4("女生分組", style={'font-size': '20px', 'font-weight': 'bold', 'margin-top': '20px', 'color': '#FF4081'}))
            for i, (color, group) in enumerate(sorted(female_groups.items(), key=lambda x: min(x[1])), 1):
                group_results_html.append(html.Div(
                    [
                        html.Span(f"組別 {i}: ", style={'font-weight': 'bold', 'font-size': '18px'}),
                        html.Span(f"{', '.join(map(str, sorted(group)))}", style={'color': color, 'font-size': '18px'})
                    ], style={'margin-left': '10px'}
                ))

            return group_results_html, {'display': 'block'}
        
        # 如果驗證失敗或有警告，則不顯示
        return "", {'display': 'none'}
    
    # 回調處理節點事件（mouseoverNode）
    @app.callback(
        Output('hover-info', 'children'),
        Input('cytoscape', 'tapNode'),
        State('cytoscape', 'elements')
    )
    def display_node_edges_on_hover(node_data, elements):
        if node_data:
            node_id = node_data['data']['id']
            incoming_edges = [e for e in elements if 'target' in e['data'] and e['data']['target'] == node_id]
            outgoing_edges = [e for e in elements if 'source' in e['data'] and e['data']['source'] == node_id]

            # 構造顯示的邊的描述
            incoming_edges_info = [f"{e['data']['source']} -> {node_id}" for e in incoming_edges]
            outgoing_edges_info = [f"{node_id} -> {e['data']['target']}" for e in outgoing_edges]

            return [
                html.Div(f"節點: {node_id}"),
                html.Div(f"入邊: {', '.join(incoming_edges_info)}" if incoming_edges_info else "沒有入邊"),
                html.Div(f"出邊: {', '.join(outgoing_edges_info)}" if outgoing_edges_info else "沒有出邊")
            ]
        return ""

# 檢查男生和女生範圍是否重疊
def check_range_overlap(male_end, female_start):
    if male_end >= female_start:
        return "Error: Male and Female ranges overlap!"
    return ""

# 檢查是否有 st_id 不在定義的男生或女生範圍內
def check_invalid_ids(df, male_start, male_end, female_start, female_end):
    invalid_ids = df[~df['st_id'].between(male_start, male_end) & ~df['st_id'].between(female_start, female_end)]
    if not invalid_ids.empty:
        return f"Warning: Some st_id are outside the defined male or female ranges! Invalid st_id: {invalid_ids['st_id'].tolist()}."
    return ""

# 檢查男生和女生網絡是否連通
def check_network_connection(G, male_nodes, female_nodes):
    for male_node in male_nodes:
        for female_node in female_nodes:
            if nx.has_path(G, male_node, female_node) or nx.has_path(G, female_node, male_node):
                return "Warning: Male and Female networks are connected!"
    return ""

def check_group_size(group_sizes_input, actual_count, group_label):
    """
    檢查group size是否符合實際人數
    - group_sizes_input: 用戶輸入的組別大小 (string，如 "4, 4, 4, 2")
    - actual_count: 實際的人數
    - group_label: 組別標籤 (用於warning，例如 "Male" 或 "Female")

    返回: 警告訊息，如果一切正常則返回空字串
    """
    if not group_sizes_input:
        return f"Warning: {group_label} group sizes are empty!"
    
    try:
        # 將用戶輸入的組別大小轉換為整數列表
        group_sizes = [int(x.strip()) for x in group_sizes_input.split(',')]
        # 計算組別大小的總和
        total_group_size = sum(group_sizes)
        if total_group_size != actual_count:
            return f"Warning: {group_label} group sizes ({total_group_size}) do not match the actual count ({actual_count})!"
        return f"{group_label} group size verification successful!"
    except ValueError:
        return f"Warning: Invalid {group_label} group sizes format!"

# 通用的验证和警告函数
def validate_and_process_data(contents, male_start, male_end, female_start, female_end, male_group_sizes, female_group_sizes):
    warning_message = ""
    validation_message = ""
    male_group_check = ""
    female_group_check = ""
    validation_style = {'color': 'red'}
    df = None

    # 检查范围是否重叠
    warning_message += check_range_overlap(male_end, female_start)

    if contents:
        df = process_uploaded_file(contents)
        if df is not None:
            # 检查是否有 st_id 不在定义的范围内
            warning_message += check_invalid_ids(df, male_start, male_end, female_start, female_end)
            if warning_message:
                return warning_message, validation_message, validation_style, male_group_check, female_group_check, df
            # 使用男生和女生的范围过滤数据
            df_male = df[df['st_id'].between(male_start, male_end)]
            df_female = df[df['st_id'].between(female_start, female_end)]

            # 生成有向图
            G = create_directed_graph(df)

            # 男生和女生的节点集合
            male_nodes = set(df_male['st_id'])
            female_nodes = set(df_female['st_id'])

            # 检查男生和女生网络是否连接
            warning_message += check_network_connection(G, male_nodes, female_nodes)

            # 检查 group size 是否正确
            male_count = len(df_male)
            female_count = len(df_female)
            male_group_check = check_group_size(male_group_sizes, male_count, "Male")
            female_group_check = check_group_size(female_group_sizes, female_count, "Female")

            # 检查结果
            validation_message = f"{male_group_check} {female_group_check}"
            if "Warning" not in validation_message:
                validation_message = "Group size verification successful"
                validation_style = {'color': 'green'}
            else:
                validation_style = {'color': 'red'}

    return warning_message, validation_message, validation_style, male_group_check, female_group_check, df