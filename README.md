An advanced web-based intelligence tool designed to analyze and predict the likelihood that two distinct online vendor personas are operated by the same individual. This project uses a hybrid PHP/Python architecture to perform multi-factor forensic analysis on marketplace data.


► Overview
The Forensic Persona Linker is an operational prototype that demonstrates how machine learning can be applied to solve complex identity resolution problems. The application's backend is powered by a Random Forest Classifier trained on the "Agora" marketplace dataset. It provides a verdict by correlating four distinct forensic markers:

Stylometry (Writing Style): Analyzes linguistic patterns in product descriptions.

Shipping Logistics: Compares the origin countries for shipments.

Product Categorization: Checks for specialization in the same product categories.

Pricing Strategy: Analyzes the difference in product pricing.

The system uses a simple "token" based input (vendor names) and returns a detailed analysis, complete with a confidence score and a report explaining the reasoning behind its conclusion.

► Key Features
Multi-Factor Analysis: Goes beyond simple text comparison by integrating logistics, product, and pricing data for a more accurate verdict.

High-Efficiency Architecture: Employs a hybrid PHP/Python system where a Python API handles intensive machine learning tasks and PHP manages fast web requests.

High-Performance Database Lookup: Uses an indexed SQLite database to retrieve vendor data in milliseconds, replacing slow CSV file parsing.

Interactive Web Interface: A clean and professional frontend that allows for easy input and presents the complex analysis in a clear, user-friendly report with a confidence score.

Robust Machine Learning Model: The backend uses a scikit-learn RandomForestClassifier that has been trained and evaluated to perform with high accuracy, precision, and recall.

► Model Performance
The final model was evaluated on a reserved test set, achieving the following performance metrics:

Metric

No Match

Match

Accuracy

Precision 0.93 0.83

Recall 0.81 0.94 87%

F1-Score 0.86 0.88


Precision (83% for Match): When the model predicts a match, it is correct 83% of the time.

Recall (94% for Match): The model successfully identifies 94% of all true matches in the dataset.

► Technology Stack
Backend API: Python 3, Flask

Machine Learning: Scikit-learn, Pandas, NumPy

Frontend: PHP 8+

Database: SQLite

Web Server: Apache (via XAMPP)

► Setup and Installation Guide
Follow these steps to get the project running on a local machine.

1. Prerequisites
XAMPP: Install XAMPP with the Apache web server.

Python 3: Ensure Python is installed and accessible from your command line.

Python Libraries: Install all necessary packages by running:

pip install pandas scikit-learn numpy flask joblib

2. One-Time Setup
Place the raw Agora.csv dataset in the project root folder and run the following commands from your terminal in the project directory.

Train the Machine Learning Model:
This script will process the raw data, train the classifier, and save the final model artifacts (.pkl files).

python train.py

Create the Lookup Database:
This script converts the Agora.csv into a highly efficient SQLite database for the PHP application.

python create_database.py

3. Launching the Application
The application requires two servers to be running simultaneously.

Start the Python API Server:
In your terminal, run the Flask server. This terminal window must remain open.

python api_server.py

You should see output indicating that the server is running on http://127.0.0.1:5000.

Start the Apache Web Server:
Open the XAMPP Control Panel and start the Apache module.

Access the Web App:
Open your web browser and navigate to:

http://localhost/forensic_prototype/

(Note: Assumes your project folder is named forensic_prototype inside C:\xampp\htdocs\)

► How to Use
Navigate to the web application in your browser.

Open the agora_lookup.db (using a tool like DB Browser for SQLite) or the original Agora.csv to find valid vendor names.

Enter the name of the first vendor in the "Vendor Name 1" field.

Enter the name of the second vendor in the "Vendor Name 2" field.

Click the "Analyze" button. The system will perform the analysis and display the detailed report.

► Project File Structure
forensic_prototype/
│
├── agora_lookup.db             # SQLite database for fast vendor lookups
├── Agora.csv                   # The original raw dataset
│
├── train.py                    # (One-Time) Python script to train the ML model
├── create_database.py          # (One-Time) Python script to create the SQLite DB
│
├── api_server.py               # (Run constantly) The Python Flask API backend
│
├── vendor_model.pkl            # Saved trained classifier model
├── vectorizer.pkl              # Saved TF-IDF vectorizer
├── scaler.pkl                  # Saved feature scaler
│
├── analyze.php                 # PHP script that handles form submission and calls the Python API
├── index.php                   # The main PHP web page (user interface)
│
└── vendor/                     # Folder for Composer PHP dependencies
