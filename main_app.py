from flask import Flask, render_template, request, jsonify
import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder, StandardScaler

app = Flask(__name__)

# Load and preprocess data
wine_data = pd.read_excel('wine_database.xlsx').dropna(subset=['rating', 'Prices', 'Varieties', 'color_wine', 'notes', 'Vintage'])

# Create encoders and scaler
variety_encoder = LabelEncoder()
color_encoder = LabelEncoder()
rating_scaler = StandardScaler()

# Fit encoders and scaler
wine_data['Varieties_encoded'] = variety_encoder.fit_transform(wine_data['Varieties'])
wine_data['color_encoded'] = color_encoder.fit_transform(wine_data['color_wine'])
wine_data['rating_scaled'] = rating_scaler.fit_transform(wine_data[['rating']])

# Get unique varieties and colors for dropdowns
unique_varieties = sorted(wine_data['Varieties'].unique().tolist())
unique_colors = sorted(wine_data['color_wine'].unique().tolist())

def recommend_wine(input_data):
    # Initialize default values
    input_rating = 0
    input_price = 0
    variety_code = 0
    color_code = 0
    scaled_rating = 0
    
    try:
        input_rating = float(input_data['rating'])
        input_price = float(input_data['price'])
        input_variety = str(input_data['variety'])
        input_color = str(input_data['color'])
        
        # Convert variety and color to encoded values
        try:
            variety_code = variety_encoder.transform([input_variety])[0]
        except ValueError:
            variety_code = 0  # default if unknown variety
        
        try:
            color_code = color_encoder.transform([input_color])[0]
        except ValueError:
            color_code = 0  # default if unknown color

        # Scale the input rating
        scaled_rating = rating_scaler.transform([[input_rating]])[0][0]
    except Exception as e:
        print(f"Error processing input: {str(e)}")
        return []  # Return empty list if input processing fails

    try:
        # Filter by price range first (±20% of input price)
        price_lower = input_price * 0.8
        price_upper = input_price * 1.2
        filtered = wine_data[
            (wine_data['Prices'] >= price_lower) & 
            (wine_data['Prices'] <= price_upper)
        ].copy()
        
        # If not enough matches, expand price range
        if len(filtered) < 5:
            price_lower = input_price * 0.6
            price_upper = input_price * 1.4
            filtered = wine_data[
                (wine_data['Prices'] >= price_lower) & 
                (wine_data['Prices'] <= price_upper)
            ].copy()
        
        # If still not enough, use all wines sorted by price proximity
        if len(filtered) < 5:
            filtered = wine_data.copy()
            filtered['price_diff'] = abs(filtered['Prices'] - input_price)
            filtered = filtered.sort_values('price_diff')
        
        # Calculate similarity scores
        filtered['similarity'] = 0
        for idx, row in filtered.iterrows():
            # Rating similarity (40% weight)
            rating_sim = 1 - abs(row['rating_scaled'] - scaled_rating)/4
            
            # Price similarity (30% weight)
            price_diff = abs(row['Prices'] - input_price)
            price_sim = 1 / (1 + price_diff/input_price)
            
            # Variety similarity (20% weight)
            variety_sim = 1 if row['Varieties_encoded'] == variety_code else 0
            
            # Color similarity (10% weight)
            color_sim = 1 if row['color_encoded'] == color_code else 0
            
            filtered.at[idx, 'similarity'] = (
                0.4 * rating_sim + 
                0.3 * price_sim + 
                0.2 * variety_sim + 
                0.1 * color_sim
            )
        
        # Get top 5 most similar wines
        top_wines = filtered.sort_values('similarity', ascending=False).head(5)
        
        # Prepare results
        recommendations = []
        for _, wine in top_wines.iterrows():
            original_rating = rating_scaler.inverse_transform([[wine['rating_scaled']]])[0][0]
            
            recommendations.append({
                'name': wine['Names'],
                'rating': round(float(original_rating), 1),
                'price': round(float(wine['Prices']), 2),
                'color': wine['color_wine'],
                'variety': wine['Varieties'],
                'notes': wine['notes'],
                'vintage': wine['Vintage'],
                'similarity_score': round(float(wine['similarity']), 3)
            })
        
        return recommendations
    
    except Exception as e:
        print(f"Error in recommendation process: {str(e)}")
        return []

@app.route('/')
def home():
    return render_template('index.html', 
                         varieties=unique_varieties,
                         colors=unique_colors)

@app.route('/get_wine_varieties')
def get_wine_varieties():
    return jsonify(unique_varieties)

@app.route('/get_wine_colors')
def get_wine_colors():
    return jsonify(unique_colors)

@app.route('/recommend_wine', methods=['POST'])
def get_recommendations():
    try:
        data = request.json
        required = ['rating', 'price', 'variety', 'color']
        if not all(field in data for field in required):
            return jsonify({'error': 'Missing required fields'}), 400
        
        recommendations = recommend_wine(data)
        return jsonify(recommendations)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)