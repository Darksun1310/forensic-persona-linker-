import pandas as pd
import numpy as np
import random
import pickle
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler
from sklearn.svm import SVC
from sklearn.metrics import classification_report
from sklearn.metrics.pairwise import cosine_similarity as sk_cosine_similarity

print("--- Starting Model Training ---")

random.seed(42)
np.random.seed(42)

# 1. Load Raw Data with Encoding Fallback
print("Loading raw dataset...")
try:
    # --- FIX IS HERE ---
    try:
        df = pd.read_csv('Agora.csv', encoding='utf-8')
    except UnicodeDecodeError:
        print("UTF-8 failed, trying latin-1 encoding...")
        df = pd.read_csv('Agora.csv', encoding='latin-1')

    df.rename(columns=lambda x: x.strip(), inplace=True)
    if 'Item Descr' in df.columns:
        df.rename(columns={'Item Descr': 'Item Description'}, inplace=True)

    # 2. Data Cleaning
    print("Cleaning price data...")
    df['Price'] = df['Price'].astype(str).str.extract(r'(\d+\.?\d*)', expand=False).astype(float)
    df.dropna(subset=['Price', 'Vendor', 'Item Description', 'Category', 'Origin'], inplace=True)
    
    print("Data loaded successfully.")

    # 3. Generate Paired Data
    print("Generating positive and negative pairs for training...")
    pairs = []
    labels = []
    grouped = df.groupby('Vendor')
    vendors_with_multiple_listings = [vendor for vendor, listings in grouped if len(listings) > 1]
    all_vendors = list(grouped.groups.keys())

    for vendor in vendors_with_multiple_listings:
        listings = grouped.get_group(vendor)
        for _ in range(min(len(listings), 5)):
            samples = listings.sample(n=2, random_state=42)
            pairs.append((samples.iloc[0], samples.iloc[1]))
            labels.append(1)
        
        for _ in range(min(len(listings), 5)):
            random_vendor_name = random.choice(all_vendors)
            while random_vendor_name == vendor:
                random_vendor_name = random.choice(all_vendors)
            
            l1 = listings.sample(n=1, random_state=42).iloc[0]
            l2 = grouped.get_group(random_vendor_name).sample(n=1, random_state=42).iloc[0]
            pairs.append((l1, l2))
            labels.append(0)

    train_df = pd.DataFrame({
        'Origin 1': [p[0]['Origin'] for p in pairs],
        'Category 1': [p[0]['Category'] for p in pairs],
        'Price 1': [p[0]['Price'] for p in pairs],
        'Item Description 1': [p[0]['Item Description'] for p in pairs],
        'Origin 2': [p[1]['Origin'] for p in pairs],
        'Category 2': [p[1]['Category'] for p in pairs],
        'Price 2': [p[1]['Price'] for p in pairs],
        'Item Description 2': [p[1]['Item Description'] for p in pairs],
        'Match': labels
    })

    # 4. Feature Engineering
    print("Engineering features...")
    all_descriptions = pd.concat([train_df['Item Description 1'].astype(str), train_df['Item Description 2'].astype(str)])
    vectorizer = TfidfVectorizer(stop_words='english', max_features=1500, ngram_range=(1, 2))
    vectorizer.fit(all_descriptions)

    vecs1 = vectorizer.transform(train_df['Item Description 1'].astype(str))
    vecs2 = vectorizer.transform(train_df['Item Description 2'].astype(str))

    print("Calculating cosine similarity (memory-efficiently)...")
    cosine_sims = [sk_cosine_similarity(vecs1[i], vecs2[i])[0][0] for i in range(vecs1.shape[0])]

    origin_match = (train_df['Origin 1'] == train_df['Origin 2']).astype(int)
    category_match = (train_df['Category 1'] == train_df['Category 2']).astype(int)
    price_diff = np.log1p(abs(train_df['Price 1'] - train_df['Price 2']))

    X = np.vstack([cosine_sims, origin_match, category_match, price_diff]).T
    y = train_df['Match']

    # 5. Data Splitting and Scaling
    print("Splitting and scaling data...")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    scaler = MinMaxScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    # 6. Train the Classifier
    print("Training the SVC model...")
    classifier = SVC(kernel='rbf', probability=True, class_weight='balanced', random_state=42)
    classifier.fit(X_train_scaled, y_train)

    # Evaluate the model
    print("\n--- Model Evaluation ---")
    y_pred = classifier.predict(X_test_scaled)
    print(classification_report(y_test, y_pred, target_names=['No Match', 'Match']))
    print("------------------------\n")

    # 7. Save Artifacts
    print("Saving model artifacts...")
    with open('vendor_model.pkl', 'wb') as f: pickle.dump(classifier, f)
    with open('vectorizer.pkl', 'wb') as f: pickle.dump(vectorizer, f)
    with open('scaler.pkl', 'wb') as f: pickle.dump(scaler, f)

    print("--- Model Training Complete! ---")

except FileNotFoundError:
    print(f"ERROR: 'Agora.csv' not found. Please make sure the file is in the same directory.")
except Exception as e:
    print(f"An unexpected error occurred: {e}")
    