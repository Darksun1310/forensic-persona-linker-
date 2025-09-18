from flask import Flask, request, jsonify
import numpy as np
import pickle
import re # Import the regular expression module
from sklearn.metrics.pairwise import cosine_similarity as sk_cosine_similarity

print("--- Loading Persona Linker API ---")
try:
    with open('vendor_model.pkl', 'rb') as f:
        classifier = pickle.load(f)
    with open('vectorizer.pkl', 'rb') as f:
        vectorizer = pickle.load(f)
    with open('scaler.pkl', 'rb') as f:
        scaler = pickle.load(f)
    print("All artifacts loaded successfully.")
except FileNotFoundError:
    print("FATAL ERROR: Model files not found. Please run train.py first.")
    exit()

app = Flask(__name__)

def create_feature_vector(data):
    """Creates a feature vector from a dictionary of listing pair data."""
    # 1. Clean prices
    price1 = clean_price(data['price1'])
    price2 = clean_price(data['price2'])

    # 2. Vectorize descriptions (no need for .toarray())
    vec1 = vectorizer.transform([str(data['desc1'])])
    vec2 = vectorizer.transform([str(data['desc2'])])

    # 3. Create feature vector
    features = np.array([
        [
            # Use the same cosine similarity function as in training for consistency
            sk_cosine_similarity(vec1, vec2)[0][0],
            1 if data['origin1'] == data['origin2'] else 0,
            1 if data['category1'] == data['category2'] else 0,
            np.log1p(abs(price1 - price2))  # Use log-transformed price difference
        ]
    ])
    return features

def clean_price(price_str):
    """Use regex to find the first floating-point number in the string."""
    match = re.search(r'(\d+\.?\d*)', str(price_str))
    return float(match.group(1)) if match else 0.0

def generate_detailed_report(unscaled_features, data):
    """Generates a detailed, human-readable report for each feature with reasoning."""
    report = []

    # 1. Writing Style
    cosine_sim = unscaled_features[0][0]
    writing_style_similarity = int(round(float(cosine_sim) * 100))
    
    if cosine_sim > 0.7:
        style_strength = "Strong Indicator"
        style_reasoning = "The writing style, including vocabulary and sentence structure, is highly similar. This is a strong sign that the same author wrote both descriptions."
    elif cosine_sim > 0.4:
        style_strength = "Moderate Indicator"
        style_reasoning = "There are some notable similarities in the writing style, which suggests a possible connection between the authors."
    else:
        style_strength = "Weak Indicator"
        style_reasoning = "The writing styles are not very similar, providing little evidence for a connection."

    report.append({
        'feature': 'Writing Style',
        'value': f'{writing_style_similarity}% similarity',
        'strength': style_strength,
        'reasoning': style_reasoning
    })

    # 2. Shipping Origin
    origin_match = bool(unscaled_features[0][1])
    origin1 = data.get('origin1', 'N/A')
    origin2 = data.get('origin2', 'N/A')

    if origin_match:
        origin_strength = "Strong Indicator"
        origin_reasoning = "Both listings ship from the same location. This is a significant piece of evidence linking the two vendor accounts."
        origin_value = f"Match ('{origin1}')"
    else:
        origin_strength = "Strong Counter-Indicator"
        origin_reasoning = "The listings ship from different locations. This strongly suggests they are from different vendors."
        origin_value = f"No Match ('{origin1}' vs '{origin2}')"

    report.append({
        'feature': 'Shipping Origin',
        'value': origin_value,
        'strength': origin_strength,
        'reasoning': origin_reasoning
    })

    # 3. Product Category
    category_match = bool(unscaled_features[0][2])
    category1 = data.get('category1', 'N/A')
    category2 = data.get('category2', 'N/A')

    if category_match:
        category_strength = "Moderate Indicator"
        category_reasoning = "Both items are in the same product category. While not definitive, vendors often specialize, making this a moderate indicator of a link."
        category_value = f"Match ('{category1}')"
    else:
        category_strength = "Weak Counter-Indicator"
        category_reasoning = "The items are in different categories. This slightly reduces the likelihood of a match, but many vendors sell a variety of goods."
        category_value = f"No Match ('{category1}' vs '{category2}')"

    report.append({
        'feature': 'Product Category',
        'value': category_value,
        'strength': category_strength,
        'reasoning': category_reasoning
    })

    # 4. Price Difference
    price1 = clean_price(data['price1'])
    price2 = clean_price(data['price2'])
    raw_price_diff = abs(price1 - price2)
    
    max_price = float(max(price1, price2))
    relative_diff = raw_price_diff / max_price if max_price > 0 else 0

    if relative_diff < 0.1:
        price_strength = "Weak Indicator"
        price_reasoning = "The prices are very close. This is a weak indicator, as similar items often have similar prices, but it's consistent with a single vendor."
    elif relative_diff < 0.3:
        price_strength = "Weak Counter-Indicator"
        price_reasoning = "There is a noticeable difference in price. This slightly suggests different vendors, although pricing strategies can vary."
    else:
        price_strength = "Moderate Counter-Indicator"
        price_reasoning = "The prices are significantly different. This is a moderate indicator that the listings are from separate vendors."

    report.append({
        'feature': 'Price Difference',
        'value': f'${raw_price_diff:.2f}',
        'strength': price_strength,
        'reasoning': price_reasoning
    })
    
    return report

@app.route('/predict', methods=['POST'])
def predict():
    try:
        data = request.get_json()
        required_keys = ['desc1', 'desc2', 'origin1', 'origin2', 'category1', 'category2', 'price1', 'price2']
        if not all(key in data for key in required_keys):
            return jsonify({'error': 'Missing required fields in JSON payload. Required: ' + ', '.join(required_keys)}), 400
    except Exception:
        return jsonify({'error': 'Invalid or missing JSON payload'}), 400

    # 1. Feature Engineering (on the input data)
    unscaled_features = create_feature_vector(data)

    # 2. Apply Scaling (using the loaded scaler object)
    final_features = scaler.transform(unscaled_features)

    # 3. Make Prediction
    prediction = classifier.predict(final_features)[0]
    probability = classifier.predict_proba(final_features)[0][1]
    verdict = 'Potential Match' if prediction == 1 else 'No Match'
    
    # 4. Generate Report
    score = int(round(float(probability) * 100))

    report = [] # Initialize report as an empty list
    try:
        # Generate the detailed, human-readable report with reasoning
        print("\n--- DEBUG: Attempting to generate detailed report... ---")
        report = generate_detailed_report(unscaled_features, data)
        print(f"--- DEBUG: Report generated successfully. Content:\n{report}\n")
    except Exception as e:
        print(f"!!! ERROR during generate_detailed_report: {e} !!!")
        # Return an error to the user to make the problem visible
        return jsonify({'error': f'An error occurred while generating the report: {e}'}), 500

    # Build the final response dictionary
    response_data = {
        'verdict': verdict,
        'score': score,
        'report': report
    }
    print(f"--- DEBUG: Final response data before jsonify:\n{response_data}\n")

    try:
        # Attempt to jsonify the response
        response = jsonify(response_data)
        print("--- DEBUG: jsonify successful. ---\n")
        return response
    except Exception as e:
        print(f"!!! ERROR during jsonify: {e} !!!")
        # If jsonify fails, try to return a simpler response that shows the error
        return jsonify({'verdict': verdict, 'score': score, 'error': f'Report could not be serialized: {e}'}), 500

if __name__ == '__main__':
    app.run(port=5000)
