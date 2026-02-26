<?php
/**
 * FHIR CORS Proxy
 * Simple PHP proxy to bypass CORS restrictions for FHIR CapabilityStatement requests
 */

// Enable CORS for your domain
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: GET, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type, Accept');
header('Content-Type: application/json');

// Handle preflight OPTIONS request
if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(200);
    exit();
}

// Only allow GET requests
if ($_SERVER['REQUEST_METHOD'] !== 'GET') {
    http_response_code(405);
    echo json_encode(['error' => 'Method not allowed']);
    exit();
}

// Get the target URL from query parameter
$targetUrl = isset($_GET['url']) ? $_GET['url'] : '';

if (empty($targetUrl)) {
    http_response_code(400);
    echo json_encode(['error' => 'Missing url parameter']);
    exit();
}

// Validate URL
if (!filter_var($targetUrl, FILTER_VALIDATE_URL)) {
    http_response_code(400);
    echo json_encode(['error' => 'Invalid URL']);
    exit();
}

// Security: Only allow HTTPS URLs (optional but recommended)
if (strpos($targetUrl, 'https://') !== 0) {
    http_response_code(400);
    echo json_encode(['error' => 'Only HTTPS URLs are allowed']);
    exit();
}

// Initialize cURL
$ch = curl_init();

// Set cURL options
curl_setopt_array($ch, [
    CURLOPT_URL => $targetUrl,
    CURLOPT_RETURNTRANSFER => true,
    CURLOPT_FOLLOWLOCATION => true,
    CURLOPT_MAXREDIRS => 5,
    CURLOPT_TIMEOUT => 30,
    CURLOPT_SSL_VERIFYPEER => true,
    CURLOPT_HTTPHEADER => [
        'Accept: application/fhir+json, application/json',
        'User-Agent: FHIR-CapabilityStatement-Viewer/1.0'
    ]
]);

// Execute the request
$response = curl_exec($ch);
$httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
$error = curl_error($ch);

curl_close($ch);

// Handle errors
if ($response === false) {
    http_response_code(502);
    echo json_encode([
        'error' => 'Failed to fetch from FHIR server',
        'details' => $error
    ]);
    exit();
}

// Return the response with appropriate status code
http_response_code($httpCode);
echo $response;
?>
