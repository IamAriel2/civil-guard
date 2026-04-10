import json
import heapq
from collections import defaultdict

def find_way(start, dest, M, time):

    with open(f'data/graphs/graph_{time}.json', 'r') as f:
        graph_data = json.load(f)
    
    graph = defaultdict(list)
    
    for edge_key, edge_data in graph_data.items():
        parts = edge_key.split()
        if len(parts) >= 2:
            source = parts[0]
            target = parts[1]
            
            length = edge_data['length']
            shelter_value = edge_data['shelter_value']
            
            if shelter_value == -1:
                weight = float('inf')
            else:
                weight = (1 - M) * length + M * shelter_value * shelter_value
            
            graph[source].append((target, weight))
    
    # Initialize Dijkstra table: Node | Distance | Parent
    dijkstra_table = {}
    visited = []
    
    all_nodes = set()
    for node in graph.keys():
        all_nodes.add(node)
    for node_neighbors in graph.values():
        for neighbor, _ in node_neighbors:
            all_nodes.add(neighbor)
    
    for node in all_nodes:
        dijkstra_table[node] = {
            'distance': float('inf'),
            'parent': None
        }
    
    dijkstra_table[start]['distance'] = 0
    
    pq = [(0, start)]
    
    while pq:
        current_dist, current_node = heapq.heappop(pq)
        
        if current_node in visited:
            continue
            
        visited.append(current_node)
        
        if current_node == dest:
            path = []
            node = dest
            while node is not None:
                path.append(node)
                node = dijkstra_table[node]['parent']
            path.reverse()
            
            return dijkstra_table[dest]['distance'], path
        
        for neighbor, weight in graph[current_node]:
            if neighbor not in visited:
                new_dist = current_dist + weight
                
                if new_dist < dijkstra_table[neighbor]['distance']:
                    dijkstra_table[neighbor]['distance'] = new_dist
                    dijkstra_table[neighbor]['parent'] = current_node
                    heapq.heappush(pq, (new_dist, neighbor))
    
    return float('inf'), []