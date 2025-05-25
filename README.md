# Quiz 2 - PAA

## Code Implementation
Our project implements the Breadth-First Search Algorithm to explore nearby districts within a certain range. The distances between districts are calculated through geographical coordinates. Each district is scored based on distance, price, and crime rate using user-given weights.


# Packages
```
from flask import Flask, render_template, request
from geopy.distance import geodesic
from collections import deque
import pandas as pd


app = Flask(__name__)
```
These are the packages needed in order for us to import the csv, calculate the geographical coordinate distances, queue, and implement our Flask web application.


# CSV File
```
df = pd.read_csv('house_data.csv')
df['Average House Price (IDR)'] = df['Average House Price (IDR)'].str.replace(',', '').astype(float)
districts = df['District'].tolist()
```
The line above reads through the “house_data.csv” and converts the “Average House Price (IDR)” column into float data type for calculation. A variable named districts is then initiated to get a list of all the district names in the csv file.

# Distance
```
adjacency = {}
for i, district_i in enumerate(districts):
   adjacency[district_i] = []
   coord_i = (df.at[i, 'Latitude'], df.at[i, 'Longitude'])
   for j, district_j in enumerate(districts):
       if i == j:
           continue
       coord_j = (df.at[j, 'Latitude'], df.at[j, 'Longitude'])
       distance = geodesic(coord_i, coord_j).km
       adjacency[district_i].append((district_j, distance))
```
A variable named adjacency is initialized as a dictionary to store each district and its neighboring districts along with their distances. Using geopy.distance.geodesic, the code calculates the geographic distance between every pair of districts (excluding itself) and stores them as a list of tuples (neighbor, distance) under the corresponding district key.

# BFS Implementation
```
def bfs_find_houses(start, adjacency, max_distance_km, max_price, max_crime_rate):
   visited = set()
   queue = deque([(start, 0)])
   visited.add(start)
   results = []


   while queue:
       current, dist_so_far = queue.popleft()
       house = df[df['District'] == current].iloc[0]
       price = house['Average House Price (IDR)']
       crime = float(house['Crime Rate (Percent)'])


       if dist_so_far <= max_distance_km and price <= max_price and crime <= max_crime_rate:
           results.append({
               'District': current,
               'Distance (km)': dist_so_far,
               'Price': price,
               'Crime Rate': crime
           })


       for neighbor, dist_to_neighbor in adjacency[current]:
           total_dist = dist_so_far + dist_to_neighbor
           if neighbor not in visited and total_dist <= max_distance_km:
               visited.add(neighbor)
               queue.append((neighbor, total_dist))


   return results
```
The function “bfs_find_houses()” implements a Breadth-First-Search starting from a given district to find nearby districts that meet user-defined constraints. It takes into account a maximum distance, price limit, and crime rate threshold. It uses a queue to explore districts layer by layer (example: shortest distance first). As it visits each district, it checks if the distance calculated so far, house price, and crime rate are within limits. If so, it adds the house to the result list. The algorithm continues until all reachable and eligible districts within the allowed range are checked.

# Score Assigning
```
def score_house(house, max_distance, max_price, max_crime, w_distance, w_price, w_crime):
   total_weight = w_distance + w_price + w_crime
   if total_weight == 0:
       total_weight = 1
   w_distance /= total_weight
   w_price /= total_weight
   w_crime /= total_weight


   score = 0
   if max_distance > 0:
       score += (1 - house['Distance (km)'] / max_distance) * w_distance
   if max_price > 0:
       score += (1 - house['Price'] / max_price) * w_price
   if max_crime > 0:
       score += (1 - house['Crime Rate'] / max_crime) * w_crime
   return score
```
The “score_house()” function calculates a score for each house/district based on how well it meets user preferences for distance, price, and crime rate. Each of these criteria is assigned a weight by the user. The weights are normalized so they add up to 1. Then, for each criterion, a score is computed by comparing the house’s value to the maximum allowed value. The closer it is to 0, the higher the score. The final score is a weighted sum, where lower distance, price, and crime lead to higher overall scores. This helps rank the most suitable houses according to the user’s priorities.

# Display Results
```
@app.route('/', methods=['GET', 'POST'])
def index():
   results = []
   error = None


   if request.method == 'POST':
       try:
           price_range = int(request.form['price'])
           crime_level = float(request.form['crime'])
           coords_input = request.form['coords']
           lat, lon = map(float, coords_input.split(','))


           max_distance_km = float(request.form['max_distance'])
           max_houses = int(request.form['max_houses'])
           sort_by = request.form['sort_by']
           sort_order = request.form['sort_order']


           weight_distance = float(request.form['weight_distance'])
           weight_price = float(request.form['weight_price'])
           weight_crime = float(request.form['weight_crime'])


           user_coord = (lat, lon)
           start_district = min(
               districts,
               key=lambda district: geodesic(user_coord, (
                   df[df['District'] == district]['Latitude'].values[0],
                   df[df['District'] == district]['Longitude'].values[0]
               )).km
           )


           houses = bfs_find_houses(start_district, adjacency, max_distance_km, price_range, crime_level)


           for house in houses:
               house['Score'] = round(score_house(
                   house, max_distance_km, price_range, crime_level,
                   weight_distance, weight_price, weight_crime
               ), 3)


           reverse = (sort_order == 'desc')
           results = sorted(houses, key=lambda x: x[sort_by.capitalize() if sort_by != 'score' else 'Score'], reverse=reverse)
           results = results[:max_houses]


       except Exception as e:
           error = f"Error: {str(e)}. Make sure coordinates are in the format: lat,lon"


   return render_template('index.html', results=results, error=error)


if __name__ == '__main__':
   app.run(debug=True)
```
Lastly, the “index()” function handles user input from a web form. When the user submits the form (POST request), it reads their preferences in terms of price, crime tolerance, coordinates, number of results wanted, sorting, and weights. It finds the nearest district to the user’s location, then runs the “bfs_find_houses()” function to explore nearby districts that fit the user’s budget, safety, and distance preferences. Each house is scored using score_house() based on how close it is, how affordable, and how safe the location is depending on the user’s weights. Finally, the results are sorted, limited to the number requested, and displayed on the web page using render_template. 

