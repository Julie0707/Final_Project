import json
import requests
from bs4 import BeautifulSoup
import os
import networkx as nx
from flask import Flask, render_template, request

class Movie:
    def __init__(self, title, year, rating, url):
        # Store basic information about the movie
        self.title = title
        self.year = year
        self.rating = rating
        self.url = url
        # Initialize additional information to None
        self.plot = None
        self.director = None
        self.actors = None
        self.genre = None
        self.country = None
        self.rotten_tomatoes_rating = None
        self.imdb_rating = None
        self.metacritic_rating = None

    # Method to get additional information about the movie from OMDb API
    def get_details(self, api_key):
        url = f'http://www.omdbapi.com/?t={self.title}&y={self.year}&apikey={api_key}'
        response = requests.get(url)
        if response.status_code == 200:
            # Parse the response content as JSON and check if it contains valid data
            data = json.loads(response.content.decode('utf-8'))
            if data.get('Response') == 'True':
                # Store the additional information in the movie object
                self.plot = data.get('Plot')
                self.director = data.get('Director')
                self.actors = data.get('Actors')
                self.genre = data.get('Genre')
                self.country = data.get('Country')
                #self.ratings = data.get('Ratings')
                for rating in data.get('Ratings'):
                    if rating.get('Source') == 'Rotten Tomatoes':
                        self.rotten_tomatoes_rating = rating.get('Value')
                    elif rating.get('Source') == 'Internet Movie Database':
                        self.imdb_rating = rating.get('Value')
                    elif rating.get('Source') == 'Metacritic':
                        self.metacritic_rating = rating.get('Value')
                        break

    
def get_top_movies(url, num_movies=250):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    movie_list = []

    for movie_info in soup.select("tbody.lister-list > tr")[:num_movies]:
        title = movie_info.select_one(".titleColumn > a").text
        year = int(movie_info.select_one(".titleColumn > .secondaryInfo").text.strip("()"))
        rating = float(movie_info.select_one(".imdbRating > strong").text)
        url = "https://www.imdb.com" + movie_info.select_one(".titleColumn > a")["href"]
        movie = Movie(title, year, rating, url)
        movie_list.append(movie.__dict__)

    return movie_list


def save_cache(movies, filename):
    with open(filename, "w") as outfile:
        json.dump(movies, outfile, indent=4)
        outfile.close()


app = Flask(__name__)

def get_graph_get_path(source_node,target_node):
    with open("top_movies_details.json", "r") as file:
        movies_data = json.load(file)

    # Data structure: graph
    G = nx.Graph()
    # Add nodes and edges
    for movie in movies_data:
        title = movie["title"]
        genre = movie["genre"]
        year = movie["year"]
        rating = movie["rating"]
        country = movie["country"]
        director = movie["director"]
        actors_string = movie["actors"]
        rotten_tomatoes_rating = movie["rotten_tomatoes_rating"]
        imdb_rating = movie["imdb_rating"]
        metacritic_rating = movie["metacritic_rating"]

        # Split the actors string into a list of actor names
        actors = actors_string.split(', ')
        
        # Add movie node
        G.add_node(title, type="movie", year=year, country=country, genre=genre, rating=rating, rotten_tomatoes_rating = rotten_tomatoes_rating, imdb_rating = imdb_rating, metacritic_rating= metacritic_rating)

        # Add director node and edge to the movie
        G.add_node(director, type="director")
        G.add_edge(title, director, relationship="directed_by")

        # Add actor nodes and edges to the movie
        for actor in actors:
            G.add_node(actor, type="actor")
            G.add_edge(title, actor, relationship="acted_in")  
            
    # Find the shortest path
    try:
        shortest_path = nx.shortest_path(G, source_node, target_node)
        #print(f"Shortest path between '{source_node}' and '{target_node}':")
        #print(" -> ".join(shortest_path))
        path_list=[]
        for i in range(len(shortest_path) - 1):
            node1 = shortest_path[i]
            node2 = shortest_path[i + 1]
            relationship = G.edges[node1, node2]["relationship"]
            path_string = f"{node1}   <--({relationship})-->"
            path_list.append(path_string)
        path_list.append(shortest_path[-1])

    except nx.NetworkXNoPath:
        return "There is no link between these two."
    
    file.close()
    return path_list

def get_table(source):
    with open("top_movies_details.json", "r") as file:
        movies_data = json.load(file)
    if source=="imdb_rating":
        # Sort the movies based on rating (descending order)
        sorted_movies = sorted(movies_data, key=lambda movie: float(movie[source].split('/')[0]) if movie[source] is not None else 0, reverse=True)
    elif source=="rotten_tomatoes_rating":
        sorted_movies = sorted(movies_data, key=lambda movie: float(movie[source].split('%')[0]) if movie[source] is not None else 0, reverse=True)
    elif source=="metacritic_rating":
        sorted_movies = sorted(movies_data, key=lambda movie: float(movie[source].split('/')[0]) if movie[source] is not None else 0, reverse=True)
    elif source=="genre":
        sorted_movies = sorted(movies_data, key=lambda movie: movie["genre"])
    elif source=="director":
        sorted_movies = sorted(movies_data, key=lambda movie: movie["director"])

    file.close()
    return sorted_movies

@app.route('/')
def index():
    return render_template('user_input.html')
    

@app.route('/handle_form', methods=['POST'])
def handle_the_form():
    user_name = request.form["name"]
    criteria = request.form.get('criteria')
    source = request.form.get('source')
    question = request.form.get('question')
    name_one = request.form["name_one"]
    name_two = request.form["name_two"]
    path_result=""
    try:
        path_result = get_graph_get_path(name_one, name_two)
    except:
        path_result=["Oops","There is no link between these two."]

    if question == 'yes' and criteria!="rating":
        table_result1 = get_table(criteria)
        return render_template('presen1.html', name=user_name, criteria=criteria, source=source, name_one=name_one, name_two=name_two,path_result=path_result,table_result1=table_result1)
    elif question == 'no' and criteria!="rating":
        table_result1 = get_table(criteria)
        return render_template('presen2.html', name=user_name, criteria=criteria, source=source, table_result1=table_result1)
    elif question == 'yes' and criteria=="rating":
        table_result2 = get_table(source)
        return render_template('presen3.html', name=user_name, criteria=criteria, source=source, name_one=name_one, name_two=name_two,path_result=path_result, table_result2=table_result2)
    elif question == 'no' and criteria=="rating":
        table_result2 = get_table(source)
        return render_template('presen4.html', name=user_name, criteria=criteria, source=source,table_result2=table_result2)


if __name__ == "__main__":
    # Get the data from the first cached json
    if os.path.isfile('top_movies.json'):
        # Load data from the cache file
        with open('top_movies.json', 'r') as f:
            data = json.load(f)
            # Create objects from the cached json
            top_movies = []
            for movie_data in data:              
                movie = Movie(movie_data['title'], movie_data['year'], movie_data['rating'], movie_data['url'])
                top_movies.append(movie.__dict__)
            f.close()
    # Web scraping to get data and save cache
    else:
        url = "https://www.imdb.com/chart/top/?ref_=nv_mv_250"
        top_movies = get_top_movies(url)
        save_cache(top_movies, "top_movies.json")

    # Get the data from the second cached json
    if os.path.isfile('top_movies_details.json'):
        # Load data from the cache file
        with open('top_movies_details.json', 'r') as f:
            movies_data = json.load(f)
            movies = []
            for movie_data in movies_data:              
                movie = Movie(movie_data['title'], movie_data['year'], movie_data['rating'], movie_data['url'])
                movie.plot = movie_data['plot']
                movie.director = movie_data['director']
                movie.actors = movie_data['actors'] 
                movie.genre = movie_data['genre']
                movie.country = movie_data['country']
                movie.rotten_tomatoes_rating = movie_data['rotten_tomatoes_rating']
                movie.imdb_rating = movie_data['imdb_rating']
                movie.metacritic_rating = movie_data['metacritic_rating']
                movies.append(movie.__dict__)
            f.close()
    # Get data from web api and save cache
    else:
        with open('top_movies.json', 'r') as f:
            movies_data = json.load(f)
            api_key = '2a5e1e1b'
            movies = []
            for movie_data in movies_data:              
                movie = Movie(movie_data['title'], movie_data['year'], movie_data['rating'], movie_data['url'])
                movie.get_details(api_key)
                movies.append(movie.__dict__)
            f.close()
        save_cache(movies, "top_movies_details.json")
    

    app.run(debug=True) 

    










    



