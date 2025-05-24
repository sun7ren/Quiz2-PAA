from flask import Flask, render_template, request
from geopy.distance import geodesic
from collections import deque
import pandas as pd

app = Flask(__name__)

df = pd.read_csv('house_data.csv')
df['Average House Price (IDR)'] = df['Average House Price (IDR)'].str.replace(',', '').astype(float)
districts = df['District'].tolist()

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
