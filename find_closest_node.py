import osmnx as ox

def get_closest_node(address, G=None, city="Holon", country="Israel", coords=0):
    """
    Takes an address as text and finds the closest node in the graph.
    If a graph G is provided, it uses it. Otherwise, it generates one from OSM.
    """
    try:
        if not coords:
            full_address = f"{address}, {city}, {country}"
            
            location = ox.geocode(full_address)
            if not location:
                print(f"Could not find coordinates for: {full_address}")
                return None
                
            lat, lng = location
        else:
            lat, lng = address.split(",")
            lat, lng = float(lat.strip()), float(lng.strip())
        
        if G is None:
            G = ox.graph_from_place(f"{city}, {country}", network_type="walk")
            
        closest_node = ox.distance.nearest_nodes(G, X=lng, Y=lat)
        return closest_node, (lat, lng)
        
    except Exception as e:
        print(f"Error finding closest node for '{address}': {e}")
        return None

if __name__ == "__main__":
    address = "Sokolov"
    print(f"Finding closest node for '{address}'...")
    node = get_closest_node(address)
    print(f"Closest node ID: {node}")
