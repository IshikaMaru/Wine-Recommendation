import requests
from tabulate import tabulate  # Install with: pip install tabulate

url = 'http://127.0.0.1:5000/recommend_wine'
data = {
    "rating": 92.0,
    "Prices": 15.99,
    "Varieties": "Merlot",
    "color_wine": "red"
}

response = requests.post(url, json=data)

if response.status_code == 200:
    recommendations = response.json()
    # Convert to a list of lists for tabulate
    table_data = []
    for wine in recommendations:
        table_data.append([
            wine['name'],
            f"{wine['rating']:.1f}",  # Format rating to 1 decimal place
            f"${wine['price']:.2f}",  # Format price with dollar sign and 2 decimals
            wine['color'],
            wine['vintage'],
            wine['notes'][:50] + "..." if len(wine['notes']) > 50 else wine['notes']  # Truncate long notes
        ])
    
    # Define headers
    headers = ["Name", "Rating", "Price", "Color", "Vintage", "Notes"]
    # Print table with improved formatting
    print("\nWine Recommendations:")
    print(tabulate(table_data, headers=headers, tablefmt="grid", maxcolwidths=[30, None, None, None, None, 50]))
else:
    print(f"Error {response.status_code}: {response.text}")
    