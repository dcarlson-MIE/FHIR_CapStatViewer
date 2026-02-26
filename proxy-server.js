/**
 * FHIR CORS Proxy Server (Node.js/Express)
 * Simple proxy to bypass CORS restrictions for FHIR CapabilityStatement requests
 */

const express = require('express');
const cors = require('cors');
const fetch = require('node-fetch');

const app = express();
const PORT = process.env.PORT || 3001;

// Enable CORS for all origins
app.use(cors());

// Health check endpoint
app.get('/health', (req, res) => {
    res.json({ status: 'ok', service: 'FHIR CORS Proxy' });
});

// Proxy endpoint
app.get('/proxy', async (req, res) => {
    const targetUrl = req.query.url;

    // Validate URL parameter
    if (!targetUrl) {
        return res.status(400).json({ error: 'Missing url parameter' });
    }

    // Validate URL format
    try {
        const url = new URL(targetUrl);
        if (url.protocol !== 'https:') {
            return res.status(400).json({ error: 'Only HTTPS URLs are allowed' });
        }
    } catch (error) {
        return res.status(400).json({ error: 'Invalid URL format' });
    }

    try {
        // Fetch from the target FHIR server
        const response = await fetch(targetUrl, {
            method: 'GET',
            headers: {
                'Accept': 'application/fhir+json, application/json',
                'User-Agent': 'FHIR-CapabilityStatement-Viewer/1.0'
            },
            timeout: 30000
        });

        // Get response body
        const data = await response.text();

        // Set appropriate headers
        res.status(response.status);
        res.set('Content-Type', response.headers.get('content-type') || 'application/json');
        
        // Return the data
        res.send(data);

    } catch (error) {
        console.error('Proxy error:', error);
        res.status(502).json({
            error: 'Failed to fetch from FHIR server',
            details: error.message
        });
    }
});

// Start server
app.listen(PORT, () => {
    console.log(`FHIR CORS Proxy running on port ${PORT}`);
    console.log(`Usage: http://localhost:${PORT}/proxy?url=<FHIR_URL>`);
});
