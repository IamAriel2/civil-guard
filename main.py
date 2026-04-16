from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse, unquote, parse_qs
import mimetypes
import json
import calc_route
import find_closest_node
import osmnx

BASE_DIR = Path(__file__).resolve().parent
ASSETS_DIR = (BASE_DIR / "assets").resolve()
DATA_DIR = (BASE_DIR / "data").resolve()
INDEX_FILE = BASE_DIR / "pages" / "index.html"
G = osmnx.graph_from_place("Holon, Israel", network_type="walk")

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        path = unquote(parsed.path)

        if path == "/route":
            query = parse_qs(parsed.query)
            start = query.get("start", [""])[0]
            dest = query.get("dest", [""])[0]
            m = float(query.get("M", ["0.5"])[0])
            time = int(query.get("time", ["400"])[0])

            if not start or not dest:
                self.send_error(400, "Missing start or dest")
                return
                
            score, route = calc_route.find_way(start, dest, m, time)
            distance = 0
            for i in range(len(route) - 1):
                distance += G.edges[int(route[i]), int(route[i+1]), 0]['length']
            
            # Map route nodes to coordinates
            route_coords = []
            try:
                nodes_data = json.loads((DATA_DIR / "nodes.json").read_text())
                route_coords = [nodes_data.get(str(node))["coords"] for node in route if nodes_data.get(str(node))]
            except Exception as e:
                print(f"Error loading node coordinates: {e}")

            print(route)
            data = json.dumps({"distance": distance, "route": route_coords}).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return

        if path == "/address":
            query = parse_qs(parsed.query)
            address = query.get("address", [""])[0]
            
            if not address:
                self.send_error(400, "Missing address parameter")
                return
                
            node_id = find_closest_node.get_closest_node(address, G=G)
            
            # Return stringified node ID because osmnx might return numpy int types not natively JSON serializable
            data = json.dumps({"node_id": str(node_id) if node_id else None}).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return

        if path == "/":
            self.send_response(302)
            self.send_header("Location", "/index.html")
            self.end_headers()
            return

        if path == "/index.html":
            self._serve_file(INDEX_FILE)
            return
        
        if path == "/shelters.json":
            self._serve_file(DATA_DIR / "shelters.json")
            return

        if path.startswith("/assets/"):
            requested = (ASSETS_DIR / path[len("/assets/"):]).resolve()
            try:
                requested.relative_to(ASSETS_DIR)
            except ValueError:
                self.send_error(403, "Forbidden")
                return

            self._serve_file(requested)
            return

        self.send_error(404, "Not Found")

    def _serve_file(self, file_path: Path):
        if not file_path.exists() or not file_path.is_file():
            self.send_error(404, "Not Found")
            return

        content_type, _ = mimetypes.guess_type(str(file_path))
        if not content_type:
            content_type = "application/octet-stream"

        data = file_path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.end_headers()
        self.wfile.write(data)


if __name__ == "__main__":
    server = ThreadingHTTPServer(("0.0.0.0", 8000), Handler)
    print("Serving on http://localhost:8000")
    server.serve_forever()