<?php
header('Content-Type: application/json');

/**
 * NEW: Function to find a random listing for a vendor from the SQLite database.
 * This is much faster than reading a CSV.
 */
function findVendorData(string $vendorName, PDO $pdo): ?array
{
    // The 'LIMIT 1' is efficient, we just need one sample.
    $stmt = $pdo->prepare("SELECT * FROM listings WHERE Vendor = :vendor ORDER BY RANDOM() LIMIT 1");
    $stmt->execute([':vendor' => $vendorName]);
    $result = $stmt->fetch(PDO::FETCH_ASSOC);
    
    return $result ?: null;
}

// Check if vendor names were submitted
if (isset($_POST['vendor1']) && isset($_POST['vendor2'])) {
    $vendor1_name = trim($_POST['vendor1']);
    $vendor2_name = trim($_POST['vendor2']);
    $db_file = 'agora_test.db';

    try {
        // Connect to the SQLite database
        $pdo = new PDO('sqlite:' . $db_file);
        $pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);

        // Find data for both vendors
        $vendor1_data = findVendorData($vendor1_name, $pdo);
        $vendor2_data = findVendorData($vendor2_name, $pdo);

    } catch (PDOException $e) {
        echo json_encode(['verdict' => 'Error', 'score' => 0, 'report' => [['feature' => 'Database Error', 'observation' => 'Could not connect to the database.']]]);
        exit;
    }

    // Error handling (no changes)
    if (!$vendor1_data) {
        echo json_encode(['verdict' => 'Error', 'score' => 0, 'report' => [['feature' => 'Input Error', 'observation' => "Vendor '{$vendor1_name}' not found."]]]);
        exit;
    }
    if (!$vendor2_data) {
        echo json_encode(['verdict' => 'Error', 'score' => 0, 'report' => [['feature' => 'Input Error', 'observation' => "Vendor '{$vendor2_name}' not found."]]]);
        exit;
    }

    // Prepare data and call Python API (no changes needed here)
    $data_to_pass = [
        'origin1'   => $vendor1_data['Origin'],
        'category1' => $vendor1_data['Category'],
        'price1'    => $vendor1_data['Price'],
        'desc1'     => $vendor1_data['Item Description'],
        'origin2'   => $vendor2_data['Origin'],
        'category2' => $vendor2_data['Category'],
        'price2'    => $vendor2_data['Price'],
        'desc2'     => $vendor2_data['Item Description'],
    ];

    $python_api_url = 'http://localhost:5000/predict';
    $ch = curl_init($python_api_url);
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    curl_setopt($ch, CURLOPT_POST, true);
    curl_setopt($ch, CURLOPT_HTTPHEADER, ['Content-Type: application/json']);
    curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode($data_to_pass));
    curl_setopt($ch, CURLOPT_CONNECTTIMEOUT, 10);
    curl_setopt($ch, CURLOPT_TIMEOUT, 20);
    
    $result_json = curl_exec($ch);
    $httpcode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    curl_close($ch);

    if ($result_json !== false && $httpcode == 200) {
        echo $result_json;
    } else {
        $error_message = ['verdict' => 'Error', 'score' => 0, 'report' => [['feature' => 'API Error', 'observation' => 'Could not connect to the Python prediction service.']]];
        echo json_encode($error_message);
    }
} else {
    echo json_encode(['verdict' => 'Error', 'message' => 'Invalid input.']);
}
?>