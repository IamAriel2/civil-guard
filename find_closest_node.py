import osmnx as ox

def get_closest_node(address, G=None, city="Holon", country="Israel", coords=False):
    """
    Takes an address as text and finds the closest node in the graph.
    If a graph G is provided, it uses it. Otherwise, it generates one from OSM.
    """
    try:
        if not coords:
            # Construct full address for better geocoding accuracy
            full_address = f"{address}, {city}, {country}"
            
            # Get coordinates (lat, lng)
            location = ox.geocode(full_address)
            if not location:
                print(f"Could not find coordinates for: {full_address}")
                return None
                
            lat, lng = location
        else:
            lat, lng = address.split(",")
            lat, lng = float(lat.strip()), float(lng.strip())
        
        # If no graph is passed, retrieve it from osmnx
        if G is None:
            G = ox.graph_from_place(f"{city}, {country}", network_type="walk")
            
        # Find the nearest node to the parsed coordinates
        # ox.nearest_nodes takes (graph, X, Y) where X is longitude, Y is latitude
        closest_node = ox.distance.nearest_nodes(G, X=lng, Y=lat)
        return closest_node
        
    except Exception as e:
        print(f"Error finding closest node for '{address}': {e}")
        return None

if __name__ == "__main__":
    # Example usage:
    address = "Sokolov"
    print(f"Finding closest node for '{address}'...")
    node = get_closest_node(address)
    print(f"Closest node ID: {node}")
