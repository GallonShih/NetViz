# utils/graph_utilities.py
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import matplotlib.colors as mcolors  # 匯入正確的 colors 模組
import networkx as nx

def generate_cytoscape_elements(df, node_size=2):
    elements = []
    max_weight = 3
    nodes = set()
    
    # 添加節點和邊
    for _, row in df.iterrows():
        # st_id_color = '#81AFBB' if row['st_id'] <= 20 else '#ED859D'
        
        # 確保每個節點只出現一次
        if row['st_id'] not in nodes:
            elements.append({'data': {'id': str(row['st_id']), 'label': f'{row["st_id"]}', 
                                      'score': node_size / 10, 'color': '#ED859D'}})
            nodes.add(row['st_id'])

        # 添加邊
        elements.append({'data': {'source': str(row['st_id']), 'target': str(row['order1']), 'weight': 3/max_weight}, 'color': '#888'})
        elements.append({'data': {'source': str(row['st_id']), 'target': str(row['order2']), 'weight': 2/max_weight}, 'color': '#888'})
        elements.append({'data': {'source': str(row['st_id']), 'target': str(row['order3']), 'weight': 1/max_weight}, 'color': '#888'})

    return elements

def get_default_stylesheet():
    return [
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
                'opacity': 0.8,
                'arrow-scale': 1.2,
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

def generate_layout(layout_value, seed, node_repulsion):
    layout = {'name': layout_value, 'randomize': True, 'seed': seed}
    if layout_value == 'cose':
        layout['nodeRepulsion'] = node_repulsion * 10000
    return layout

def create_directed_graph(df):
    """
    從資料框生成一個有向圖 (networkx.DiGraph)
    
    參數:
    - df: 包含 'st_id', 'order1', 'order2', 'order3' 的 DataFrame
    
    返回:
    - G: NetworkX 的有向圖
    """
    # 將 order1, order2, order3 展開
    df_order = pd.melt(df, id_vars='st_id', value_vars=['order1', 'order2', 'order3'])
    df_order.columns = ['from', 'weight', 'to']

    # 根據順序給予不同的邊權重
    df_order.weight = df_order.weight.map({
        'order1': 3,
        'order2': 2,
        'order3': 1
    })

    df_order = df_order[['from', 'to', 'weight']]

    # 建立有向圖
    G = nx.DiGraph()

    # 將節點和邊添加到圖中
    for _, row in df_order.iterrows():
        G.add_edge(row['from'], row['to'], weight=row['weight'])

    return G

def create_separate_directed_graphs(df, male_range, female_range):
    """
    根據給定的男女生範圍，生成男生和女生各自的有向圖 (networkx.DiGraph)
    
    參數:
    - df: 包含 'st_id', 'order1', 'order2', 'order3' 的 DataFrame
    - male_range: 男生的範圍，格式為 (male_start, male_end)
    - female_range: 女生的範圍，格式為 (female_start, female_end)
    
    返回:
    - G_male: 男生的有向圖 (NetworkX DiGraph)
    - G_female: 女生的有向圖 (NetworkX DiGraph)
    """
    male_start, male_end = male_range
    female_start, female_end = female_range

    # 過濾出男生和女生的資料
    df_male = df[df['st_id'].between(male_start, male_end)]
    df_female = df[df['st_id'].between(female_start, female_end)]

    # 生成男生的有向圖
    G_male = create_directed_graph(df_male)

    # 生成女生的有向圖
    G_female = create_directed_graph(df_female)

    return G_male, G_female

# 將有向圖轉換為無向圖並加總雙向邊的權重
def convert_directed_to_undirected(directed_G):
    """將有向圖轉換為無向圖並加總雙向邊的權重"""
    undirected_G = nx.Graph()
    for u, v, data in directed_G.edges(data=True):
        if undirected_G.has_edge(u, v):
            undirected_G[u][v]['weight'] += data['weight']
        elif undirected_G.has_edge(v, u):
            undirected_G[v][u]['weight'] += data['weight']
        else:
            undirected_G.add_edge(u, v, weight=data['weight'])
    return undirected_G

# 檢查節點是否與組內已有的節點相連
def is_connected_to_group(node, group, G):
    """檢查節點 node 是否與 group 中的其他節點相連"""
    for member in group:
        if G.has_edge(node, member) or G.has_edge(member, node):
            return True
    return False

# 計算組內和組間的邊權重
def calculate_group_weights(optimized_groups, G):
    """計算當前分組方案的組內邊權重和組間邊權重"""
    intra_group_weight = 0
    inter_group_weight = 0
    group_mapping = {}

    # 建立節點到組的映射
    for group_id, nodes in optimized_groups.items():
        for node in nodes:
            group_mapping[node] = group_id

    # 計算組內和組間邊權重
    for u, v, data in G.edges(data=True):
        if u in group_mapping and v in group_mapping:
            if group_mapping[u] == group_mapping[v]:
                intra_group_weight += data['weight']
            else:
                inter_group_weight += data['weight']

    return intra_group_weight, inter_group_weight

# 回溯優化過程
def backtrack_optimize_groups(G, target_sizes):
    """
    回溯法進行優化分配，確保組內邊權重最大，組間邊權重最小。
    """
    # 初始化分組和狀態
    optimized_groups = {i: [] for i in range(len(target_sizes))}
    assigned_nodes = set()  # 已分配的節點
    sorted_nodes = sorted(G.degree(weight='weight'), key=lambda x: x[1])  # 根據邊權重排序

    # 初始化最佳結果
    best_intra_weight = float('-inf')  # 初始化最大組內邊權重為負無窮
    best_inter_weight = float('inf')   # 初始化最小組間邊權重為正無窮
    best_groups = None  # 初始化最優分組方案

    # 嘗試將節點分配到組內
    def try_assign_node(node, group_id):
        """將節點分配到組內，並根據邊的權重進行優先分配"""
        if len(optimized_groups[group_id]) < target_sizes[group_id]:
            # 如果組內無其他節點，直接分配
            if not optimized_groups[group_id]:
                optimized_groups[group_id].append(node)
                assigned_nodes.add(node)
                return True
            # 否則，計算該節點與組內其他節點的連接權重總和，優先分配高權重的節點
            total_weight = sum(G[node][member]['weight'] for member in optimized_groups[group_id] if G.has_edge(node, member) or G.has_edge(member, node))
            if total_weight > 0:
                optimized_groups[group_id].append(node)
                assigned_nodes.add(node)
                return True
        return False

    # 回溯分配節點
    def backtrack_assign(remaining_nodes):
        """遞歸回溯進行分配，遍歷所有可能的分配方案"""
        nonlocal best_intra_weight, best_inter_weight, best_groups

        # 將剩餘節點根據與其他節點的邊的權重排序，優先處理高權重的節點
        remaining_nodes = sorted(remaining_nodes, key=lambda n: sum(G[n][neighbor]['weight'] for neighbor in G.neighbors(n)), reverse=True)

        # 所有節點已分配，計算當前分組方案的權重
        if not remaining_nodes:
            intra_weight, inter_weight = calculate_group_weights(optimized_groups, G)
            # 更新最佳結果
            if intra_weight > best_intra_weight:
                # print(f"optimized_groups: {optimized_groups}, {intra_weight}, {best_intra_weight}")
                best_intra_weight = intra_weight
                best_inter_weight = inter_weight
                best_groups = {group_id: list(nodes) for group_id, nodes in optimized_groups.items()}
            return True

        # 對於剩餘的節點，嘗試分配到不同的組
        node = remaining_nodes[0]
        assigned = False

        for group_id in optimized_groups:
            if try_assign_node(node, group_id):
                # 遞歸嘗試下一個節點的分配
                if backtrack_assign(remaining_nodes[1:]):
                    assigned = True
                # 撤銷分配，回溯
                optimized_groups[group_id].remove(node)
                assigned_nodes.remove(node)

        return assigned

    # 找出尚未分配的節點並進行回溯分配
    remaining_nodes = [n for n, weighted_degree in sorted_nodes if n not in assigned_nodes]
    backtrack_assign(remaining_nodes)

    return best_groups, best_intra_weight, best_inter_weight

def optimize_graph_partition(directed_G, target_sizes):
    """主函數，接受有向圖和分組大小，返回最優分組結果"""
    # 將有向圖轉換為無向圖
    undirected_G = convert_directed_to_undirected(directed_G)

    # 開始回溯優化分配
    best_groups, best_intra_weight, best_inter_weight = backtrack_optimize_groups(undirected_G, target_sizes)

    return best_groups, best_intra_weight, best_inter_weight

def weight_outgoing_edges_for_isolated_nodes(directed_G, weight=2):
    """
    對於有向圖中那些沒有被其他節點指向的節點，將其指向其他節點的邊的權重乘以 2。
    
    :param directed_G: NetworkX有向圖
    :return: 權重已被修改的有向圖
    """
    # 複製原有的圖，以免修改原圖
    updated_G = directed_G.copy()

    # 找到入度為0的節點（即沒有被其他節點指向的節點）
    isolated_nodes = [node for node, in_degree in directed_G.in_degree() if in_degree == 0]

    # 對於每個入度為0的節點，將其指向的邊的權重加倍
    for node in isolated_nodes:
        for neighbor in directed_G.successors(node):  # 找到該節點指向的節點
            current_weight = directed_G[node][neighbor]['weight']
            # 將邊的權重加倍
            updated_G[node][neighbor]['weight'] = current_weight * weight
            # print(f"節點 {node} 指向節點 {neighbor} 的邊權重已變為 {updated_G[node][neighbor]['weight']}")

    return updated_G

def weight_outgoing_edges_for_min_in_degree_nodes(directed_G, weight=2):
    """
    對於有向圖中那些入度最小的節點，將其指向其他節點的邊的權重乘以 weight。
    如果所有節點的入度相同，則返回空列表。
    
    :param directed_G: NetworkX有向圖
    :param weight: 權重調整因子，默認為2
    :return: 權重已被修改的有向圖
    """
    # 複製原有的圖，以免修改原圖
    updated_G = directed_G.copy()

    # 計算每個節點的入度
    in_degrees = dict(directed_G.in_degree())
    
    # 找到最小入度值
    min_in_degree = min(in_degrees.values())
    
    # 找到所有具有最小入度的節點
    min_in_degree_nodes = [node for node, in_degree in in_degrees.items() if in_degree == min_in_degree]

    # 如果所有節點的入度相同，返回空列表
    if len(set(in_degrees.values())) == 1:
        return updated_G

    # 對於每個入度最小的節點，將其指向的邊的權重加倍
    for node in min_in_degree_nodes:
        for neighbor in directed_G.successors(node):  # 找到該節點指向的節點
            current_weight = directed_G[node][neighbor]['weight']
            # 將邊的權重加倍
            updated_G[node][neighbor]['weight'] = current_weight * weight
            # print(f"節點 {node} 指向節點 {neighbor} 的邊權重已變為 {updated_G[node][neighbor]['weight']}")

    return updated_G


def weight_edges_for_smallest_group(directed_G, optimal_groups, weight=2):
    """
    根據最優分組結果，將人數最少組別的節點指向其他組別的邊的權重加倍。
    如果所有組別人數相同，則不進行處理。
    
    :param directed_G: NetworkX有向圖
    :param optimal_groups: 最優分組結果的字典 {group_id: [node1, node2, ...]}
    :return: 權重已被修改的有向圖
    """
    # 複製原有的圖，以免修改原圖
    updated_G = directed_G.copy()

    # 計算每個組別的節點數量
    group_sizes = {group_id: len(nodes) for group_id, nodes in optimal_groups.items()}
    
    # 找到人數最少的組的大小
    min_group_size = min(group_sizes.values())

    # 檢查是否有超過一個組別人數最少，且不是所有組別人數相同
    smallest_groups = [group_id for group_id, size in group_sizes.items() if size == min_group_size]

    # 如果所有組別人數相同，則不做處理
    if len(smallest_groups) == len(optimal_groups):
        print("所有組別人數相同，不進行處理。")
        return updated_G

    # 處理最少人數的組別，將其指向其他組別的邊權重加倍
    for group_id in smallest_groups:
        for node in optimal_groups[group_id]:
            for neighbor in directed_G.successors(node):
                # 確保 neighbor 不在同一組內
                if neighbor not in optimal_groups[group_id]:
                    current_weight = directed_G[node][neighbor]['weight']
                    # 將指向其他組的邊的權重加倍
                    updated_G[node][neighbor]['weight'] = current_weight * weight
                    # print(f"節點 {node} 指向節點 {neighbor} 的邊權重已加倍，新的權重為 {updated_G[node][neighbor]['weight']}")

    return updated_G

def generate_partition_colors(num_groups):
    """
    根據 num_groups 的數量，從 'tab10' 和 'Set3' 組合後的 colormap 中生成顏色。

    :param num_groups: 所需顏色的數量
    :return: 生成的顏色列表（hex 格式）
    """
    # 獲取 'tab10' 和 'Set3' 調色盤
    cmap1 = cm.get_cmap('tab10')
    cmap2 = cm.get_cmap('Set3')

    # 提取這兩個調色盤的顏色
    num_colors_cmap1 = cmap1.N
    num_colors_cmap2 = cmap2.N

    # 將兩個 colormap 的顏色組合
    colors_cmap1 = [mcolors.to_hex(cmap1(i / num_colors_cmap1)) for i in range(num_colors_cmap1)]
    colors_cmap2 = [mcolors.to_hex(cmap2(i / num_colors_cmap2)) for i in range(num_colors_cmap2)]

    # 合併顏色列表
    combined_colors = colors_cmap1 + colors_cmap2

    # 如果 num_groups 大於合併後顏色數量，則循環使用這些顏色
    final_colors = [combined_colors[i % len(combined_colors)] for i in range(num_groups)]

    return final_colors

def apply_partition_and_color(df, male_range, female_range, elements, male_target_sizes, female_target_sizes, preference_option, update_target="both"):
    """
    根據分組結果給 elements 中的節點進行分組顏色標記
    
    參數:
    - df: 包含 'st_id', 'order1', 'order2', 'order3' 的 DataFrame
    - male_range: 男生的範圍，格式為 (male_start, male_end)
    - female_range: 女生的範圍，格式為 (female_start, female_end)
    - elements: 包含節點資訊的 Cytoscape 元素列表
    - male_target_sizes: 男生分組目標大小列表
    - female_target_sizes: 女生分組目標大小列表
    - preference_option: 用戶選擇的偏好選項
    - update_target: 控制要更新的目標 ('male', 'female', 'both')

    返回:
    - elements: 更新後的 Cytoscape 元素列表
    """
    
    # Step 1: 生成男生和女生的有向圖
    G_male, G_female = create_separate_directed_graphs(df, male_range, female_range)

    # 將 target_sizes 轉換成列表
    male_target_sizes = [int(x.strip()) for x in male_target_sizes.split(',')]
    female_target_sizes = [int(x.strip()) for x in female_target_sizes.split(',')]

    # Step 2: 根據用戶選項決定是否進行加權處理
    def partition_with_weight_adjustment(G, target_sizes, original_groups, preference_option):
        """
        遞增邊的權重，直到分組結果與原始結果有差異，或者達到上限。
        
        參數:
        - G: 有向圖
        - target_sizes: 目標分組大小
        - original_groups: 原始的分組結果
        
        返回:
        - best_groups: 最優分組結果
        """
        iteration = 1
        max_iteration = 10
        weight = 5
        best_groups = original_groups
        while iteration <= max_iteration:
            # 根據當前 weight 修改圖的權重
            if preference_option == 'option2':
                updated_G = weight_edges_for_smallest_group(G, best_groups, weight)
                if compare_graphs(updated_G, G):
                    break
                new_best_groups, _, _ = optimize_graph_partition(updated_G, target_sizes)
            elif preference_option == 'option3':
                updated_G = weight_outgoing_edges_for_min_in_degree_nodes(G, weight)
                if compare_graphs(updated_G, G):
                    break
                new_best_groups, _, _ = optimize_graph_partition(updated_G, target_sizes)
            
            if new_best_groups != best_groups:
                return new_best_groups
            
            weight += 5
            iteration += 1

        return best_groups

    # Step 3: 根據分組目標大小生成顏色，根據 update_target 控制分組的執行
    male_best_groups, female_best_groups = None, None
    if update_target in ['both', 'male']:
        male_best_groups, _, _ = optimize_graph_partition(G_male, male_target_sizes)
    if update_target in ['both', 'female']:
        female_best_groups, _, _ = optimize_graph_partition(G_female, female_target_sizes)

    # Step 4: 如果選擇 `option2` 或 `option3`，則增加權重進行重新分組
    if preference_option in ['option2', 'option3']:
        if update_target in ['both', 'male']:
            male_best_groups = partition_with_weight_adjustment(G_male, male_target_sizes, male_best_groups, preference_option)
        if update_target in ['both', 'female']:
            female_best_groups = partition_with_weight_adjustment(G_female, female_target_sizes, female_best_groups, preference_option)

    # Step 5: 根據分組目標大小生成顏色
    total_groups = len(male_target_sizes) + len(female_target_sizes)
    partition_colors = generate_partition_colors(total_groups)

    # Step 6: 更新男生節點顏色（如果更新目標包含男生）
    if update_target in ['both', 'male']:
        male_color_start_index = 0
        for group_id, male_group in male_best_groups.items():
            color = partition_colors[male_color_start_index % total_groups]
            for node_id in male_group:
                for element in elements:
                    if element['data'].get('id') == str(node_id):
                        element['data']['color'] = color
            male_color_start_index += 1

    # Step 7: 更新女生節點顏色（如果更新目標包含女生）
    if update_target in ['both', 'female']:
        female_color_start_index = len(male_target_sizes)
        for group_id, female_group in female_best_groups.items():
            color = partition_colors[female_color_start_index % total_groups]
            for node_id in female_group:
                for element in elements:
                    if element['data'].get('id') == str(node_id):
                        element['data']['color'] = color
            female_color_start_index += 1

    return elements

def reset_elements_color(elements, male_range, female_range, update_target="both"):
    """
    根據男生和女生的範圍，並根據 `update_target` 決定是否重置男生、女生或兩者的 Cytoscape 元素顏色。

    參數:
    - elements: Cytoscape 的元素列表
    - male_range: 男生編號範圍 (tuple: male_start, male_end)
    - female_range: 女生編號範圍 (tuple: female_start, female_end)
    - update_target: 指定要更新的對象 ('male', 'female', 'both')
    
    返回:
    - 更新後的 elements
    """
    male_start, male_end = male_range
    female_start, female_end = female_range
    
    for element in elements:
        if 'source' not in element['data']:  # 只針對節點元素重置顏色
            node_id = int(element['data']['id'])  # 將 ID 轉換為整數進行比較
            
            # 根據 update_target 決定重置哪些節點的顏色
            if update_target == "both" or update_target == "male":
                if male_start <= node_id <= male_end:
                    element['data']['color'] = '#ED859D'  # 預設的男生顏色
            
            if update_target == "both" or update_target == "female":
                if female_start <= node_id <= female_end:
                    element['data']['color'] = '#ED859D'  # 預設的女生顏色

    return elements


def compare_graphs(G1, G2):
    # 比较节点是否相同
    if set(G1.nodes()) != set(G2.nodes()):
        return False

    # 比较边是否相同
    if set(G1.edges()) != set(G2.edges()):
        return False

    # 比较边的属性是否相同（如权重）
    for u, v in G1.edges():
        if G1[u][v] != G2[u][v]:
            return False

    return True