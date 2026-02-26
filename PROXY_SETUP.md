# FHIR CapabilityStatement Viewer - Proxy Setup Guide

This guide explains how to deploy a server-side proxy to avoid reliance on third-party CORS proxies.

## Why Use a Server-Side Proxy?

Third-party CORS proxies (`api.allorigins.win`, `corsproxy.io`) may be:
- Blocked by corporate firewalls
- Restricted by ISPs or geographic regions
- Unreliable or slow
- Blocked by browser extensions

A server-side proxy hosted alongside your application solves these issues.

## Deployment Options

Choose the option that matches your server environment:

---

## Option 1: PHP Proxy (Recommended for most web servers)

### Requirements
- PHP 5.4+ (with cURL extension enabled)
- Any web server (Apache, Nginx, etc.)

### Deployment Steps

1. **Upload the proxy file:**
   ```bash
   # Copy proxy.php to your web root
   cp proxy.php /path/to/fhircapstatviewer.os.mieweb.org/
   ```

2. **Verify PHP and cURL are enabled:**
   ```bash
   php -m | grep curl
   # Should show "curl"
   ```

3. **Test the proxy:**
   ```bash
   curl "https://fhircapstatviewer.os.mieweb.org/proxy.php?url=https://omg.webchartnow.com/webchart.cgi/fhir/metadata"
   ```

4. **Set permissions (if needed):**
   ```bash
   chmod 644 proxy.php
   ```

### Apache Configuration (optional)

If you want cleaner URLs, add to `.htaccess`:
```apache
RewriteEngine On
RewriteRule ^api/proxy$ proxy.php [QSA,L]
```

Then access as: `https://yourdomain.com/api/proxy?url=...`

---

## Option 2: Node.js Proxy (For dedicated servers)

### Requirements
- Node.js 14+ and npm
- PM2 or similar process manager (recommended)

### Deployment Steps

1. **Install dependencies:**
   ```bash
   npm install
   ```

2. **Start the proxy server:**
   ```bash
   # Development
   npm start

   # Production with PM2
   pm2 start proxy-server.js --name fhir-proxy
   pm2 save
   pm2 startup
   ```

3. **Configure proxy port:**
   Edit `proxy-server.js` or set environment variable:
   ```bash
   export PORT=3001
   npm start
   ```

4. **Set up reverse proxy (recommended):**

   **Nginx configuration:**
   ```nginx
   location /api/proxy {
       proxy_pass http://localhost:3001/proxy;
       proxy_http_version 1.1;
       proxy_set_header Upgrade $http_upgrade;
       proxy_set_header Connection 'upgrade';
       proxy_set_header Host $host;
       proxy_cache_bypass $http_upgrade;
   }
   ```

   **Apache configuration:**
   ```apache
   ProxyPass /api/proxy http://localhost:3001/proxy
   ProxyPassReverse /api/proxy http://localhost:3001/proxy
   ```

5. **Test the proxy:**
   ```bash
   curl "https://fhircapstatviewer.os.mieweb.org/api/proxy?url=https://omg.webchartnow.com/webchart.cgi/fhir/metadata"
   ```

---

## Application Configuration

The application (`app.js`) is already configured to:
1. **Try local proxy first:** `/proxy.php?url=` (or your custom path)
2. **Fall back to third-party proxies** if local proxy fails

### Custom Proxy URL

If your proxy is at a different path, update `app.js` line ~88:

```javascript
// Change this line:
let localProxyUrl = window.location.origin + '/proxy.php?url=';

// To your custom path:
let localProxyUrl = window.location.origin + '/api/proxy?url=';
// Or absolute URL:
let localProxyUrl = 'https://fhircapstatviewer.os.mieweb.org/api/proxy?url=';
```

---

## Testing

### Test the proxy directly:
```bash
curl "https://fhircapstatviewer.os.mieweb.org/proxy.php?url=https://omg.webchartnow.com/webchart.cgi/fhir/metadata"
```

### Expected response:
- HTTP 200 status
- JSON content type
- FHIR CapabilityStatement JSON data

### Test in the application:
1. Open browser console (F12)
2. Load a FHIR URL
3. Look for console messages:
   - ✅ "Attempting local proxy fetch to: ..."
   - ✅ "Local proxy fetch successful..."
   - ❌ "Local proxy failed, trying third-party proxy..." (if local proxy has issues)

---

## Security Considerations

### Current Security Features:
- ✅ HTTPS-only URLs enforced
- ✅ URL validation
- ✅ CORS headers properly configured
- ✅ 30-second timeout limit

### Optional Enhancements:

1. **Restrict allowed domains:**
   
   Edit `proxy.php` around line 25:
   ```php
   // Add after URL validation
   $allowedDomains = ['webchartnow.com', 'webchart.app', 'fhir.org'];
   $urlHost = parse_url($targetUrl, PHP_URL_HOST);
   $allowed = false;
   foreach ($allowedDomains as $domain) {
       if (strpos($urlHost, $domain) !== false) {
           $allowed = true;
           break;
       }
   }
   if (!$allowed) {
       http_response_code(403);
       echo json_encode(['error' => 'Domain not allowed']);
       exit();
   }
   ```

2. **Add rate limiting:**
   Consider using nginx `limit_req` module or PHP rate limiting libraries.

3. **Add authentication:**
   Require API key for proxy access if needed.

---

## Troubleshooting

### PHP Proxy Issues:

**"Failed to fetch from FHIR server"**
- Check if cURL is enabled: `php -m | grep curl`
- Install if missing: `sudo apt-get install php-curl` (Ubuntu/Debian)
- Restart web server after installation

**"Only HTTPS URLs are allowed"**
- Make sure your FHIR URL starts with `https://`

**CORS errors still appearing**
- Verify the proxy file is accessible
- Check web server error logs
- Ensure PHP has internet access (check firewall rules)

### Node.js Proxy Issues:

**Port already in use:**
```bash
# Find process using port 3001
lsof -i :3001
# Kill it
kill -9 <PID>
# Or use different port
PORT=3002 npm start
```

**Dependencies missing:**
```bash
npm install
```

---

## Monitoring

### Check PHP proxy logs:
```bash
# Apache
tail -f /var/log/apache2/error.log

# Nginx
tail -f /var/log/nginx/error.log
```

### Check Node.js proxy logs with PM2:
```bash
pm2 logs fhir-proxy
pm2 monit
```

---

## Performance Tips

1. **Enable caching** (optional):
   Add caching headers to reduce repeated requests to FHIR servers.

2. **Use CDN** (if applicable):
   Route proxy requests through a CDN for better global performance.

3. **Monitor usage**:
   Set up logging to track proxy usage and identify issues.

---

## Support

For issues or questions:
- Check browser console for error messages
- Review proxy logs
- Test proxy endpoint directly with curl
- Verify FHIR server is accessible from your server

---

## Quick Reference

### File Locations:
- **PHP Proxy:** `proxy.php`
- **Node.js Proxy:** `proxy-server.js`
- **Package file:** `package.json`
- **Application:** `app.js` (line ~88 for proxy URL)

### Test Commands:
```bash
# Test PHP proxy
curl "https://yourdomain.com/proxy.php?url=https://fhir-server/metadata"

# Test Node.js proxy
curl "http://localhost:3001/proxy?url=https://fhir-server/metadata"

# Check PHP modules
php -m | grep curl

# Check Node.js processes
pm2 list
```
