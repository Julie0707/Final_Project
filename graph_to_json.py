import json
import networkx as nx

# Read the JSON file
with open("top_movies_details.json", "r") as file:
    movies_data = json.load(file)

# Create a graph
G = nx.Graph()

# Add nodes and edges
for movie in movies_data:
    title = movie["title"]
    year = movie["year"]
    genre = movie["genre"]
    rating = movie["rating"]
    country = movie["country"]
    director = movie["director"]
    actors_string = movie["actors"]
    actors = actors_string.split(', ')

    # Add movie node
    G.add_node(title, type="movie", year=year, country=country,genre=genre,rating=rating)

    # Add director node and edge to the movie
    G.add_node(director, type="director")
    G.add_edge(title, director, relationship="directed_by")

    # Add actor nodes and edges to the movie
    for actor in actors:
        G.add_node(actor, type="actor")
        G.add_edge(title, actor, relationship="acted_in")

# Convert the graph to a dictionary
graph_dict = {
    "nodes": [{"id": n, **G.nodes[n]} for n in G.nodes()],
    "edges": [{"source": u, "target": v, **G.edges[u, v]} for u, v in G.edges()]
}

# Write the graph dictionary to a JSON file
with open("graph.json", "w") as file:
    json.dump(graph_dict, file, indent=2)