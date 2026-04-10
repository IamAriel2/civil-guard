from shapely.geometry import LineString
import json
import osmnx as ox



RADIUS = 810

shelters_path = "data/shelters.json"
graph_path = f"data/graphs/graph_{RADIUS - 10}.json"    

def street_distance(loc1, loc2):
    return ox.distance.great_circle(lat1=loc1[0], lon1=loc1[1],
                                  lat2=loc2[0], lon2=loc2[1])

def address_to_coords(address):
    try:
        full_address = f"{address}, Holon, Israel"
        location = ox.geocode(full_address)
        return location
        
    except Exception as e:
        print(f"Error converting address '{address}': {e}")
        return None

id = 0
def split_street(G, u, v, key, loc):
    global id
    u_loc = (G.nodes[u]['x'], G.nodes[u]['y'])
    v_loc = (G.nodes[v]['x'], G.nodes[v]['y'])
    shelter_loc = (loc[1], loc[0])

    id += 1
    G.add_node(id, y=loc[0], x=loc[1])
    G.add_edge(u, id, length=street_distance((G.nodes[u]['y'], G.nodes[u]['x']), loc),
               geometry=LineString([u_loc, shelter_loc]))
    G.add_edge(id, v, length=street_distance((G.nodes[v]['y'], G.nodes[v]['x']), loc),
               geometry=LineString([shelter_loc, v_loc]))
    G.remove_edge(u, v, key)
    return id

def add_shelter_nodes(G, shelters):
    shelter_nodes = list()

    for shelter in shelters:
        loc = shelter['coords']
        u, v, key = ox.nearest_edges(G, loc[1], loc[0])
        new_node = split_street(G, u, v, key, loc)
        G.nodes[new_node]['shelter'] = True
        G.nodes[new_node]['name'] = shelter['name']
        shelter_nodes.append(new_node)

    return shelter_nodes

# Proccessing the graph to create circles around shelters
def create_circle_rec(G, node, radius):
    for u, v, data in G.edges(node, data=True): 
        other = u if v == node else v
        dist = G.nodes[node]['dist'] + data['length']
        
        # Only update and recurse if we found a strictly shorter path
        # and it's within the radius.
        if dist < radius and dist < G.nodes[other].get('dist', RADIUS):
            G.nodes[other]['dist'] = dist
            create_circle_rec(G, other, radius)

def create_circles(G, nodes, radius):
    for node in nodes:
        G.nodes[node]['dist'] = 0
        create_circle_rec(G, node, radius)

def calc_lengths(G):
    lengths = {}
    for u, v, key, data in G.edges(keys=True, data=True):
        length = data['length']
        dist_u, dist_v = G.nodes[u]['dist'], G.nodes[v]['dist']
        if dist_u == RADIUS or dist_v == RADIUS:
            val = -1 # Mark as unreachable street
        else:
            val = 0.25 * (length * length + 2 * length * (dist_u + dist_v) - (dist_u - dist_v) * (dist_u - dist_v))
        lengths[f"{u} {v} {key}"] = {"length": data['length'], "shelter_value": val}
    return lengths
"""
def reduction_to_zero(G):
    min_rem = RADIUS
    for node in G.nodes:
        min_rem = min(min_rem, G.nodes[node]['dist'])
    print(f"Reducing all rem values by {min_rem}")
    for node in G.nodes:
        G.nodes[node]['dist'] = max(G.nodes[node]['dist'] - min_rem, 0)
        """

def build_map():
    G = ox.graph_from_place("Holon, Israel", network_type="walk")
    with open(shelters_path, encoding="utf-8") as f:
        shelters = json.load(f)

    for node in G.nodes:
        G.nodes[node]['shelter'] = False
        G.nodes[node]['dist'] = RADIUS
    shelter_nodes = add_shelter_nodes(G, shelters)
    create_circles(G, shelter_nodes, RADIUS)
    #reduction_to_zero(G)
    lengths = calc_lengths(G)


    with open(graph_path, "w") as f:
        json.dump(lengths, f, indent=4)

    nodes_data = {}
    for node in G.nodes:
        nodes_data[str(node)] = {
            "coords": [G.nodes[node]['y'], G.nodes[node]['x']],
            "dist": G.nodes[node]['dist']
        }
    with open("data/nodes.json", "w") as f:
        json.dump(nodes_data, f, indent=4)

    print(f"Saved {len(lengths)} edge lengths to {graph_path}")
    print(f"Saved {len(nodes_data)} nodes to data/nodes.json")
    return G

if __name__ == "__main__":
    G = build_map()