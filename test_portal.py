#!/usr/bin/env python3
"""
Quick portal endpoint tester
"""

import requests
import sys

def test_portal(portal_url):
    """Test various endpoints on a portal."""
    
    endpoints = [
        '',
        'portal.php',
        'server/load.php',
        'stalker_portal/server/load.php',
        'c/version.js',
        'api/v1/',
        'c/',
        'server/',
        'index.html',
    ]
    
    print(f"Testing portal: {portal_url}")
    print("="*60)
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (QtEmbedded; U; Linux; C) AppleWebKit/533.3 (KHTML, like Gecko) MAG200 stbapp ver: 2 rev: 250 Safari/533.3',
    })
    
    for endpoint in endpoints:
        url = portal_url.rstrip('/') + '/' + endpoint
        try:
            response = session.get(url, timeout=5)
            status = response.status_code
            size = len(response.content)
            content_type = response.headers.get('Content-Type', 'unknown')
            
            if status == 200:
                print(f"✅ {status} - {endpoint:40} ({size} bytes, {content_type})")
                if size < 500:
                    print(f"   Preview: {response.text[:200]}")
            elif status in [301, 302, 307, 308]:
                location = response.headers.get('Location', 'unknown')
                print(f"↪️  {status} - {endpoint:40} -> {location}")
            else:
                print(f"❌ {status} - {endpoint:40}")
        except requests.exceptions.Timeout:
            print(f"⏱️  TIMEOUT - {endpoint}")
        except requests.exceptions.ConnectionError as e:
            print(f"🔌 CONNECTION ERROR - {endpoint}")
        except Exception as e:
            print(f"❌ ERROR - {endpoint}: {str(e)[:50]}")
    
    print("="*60)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        portal_url = sys.argv[1]
    else:
        portal_url = input("Enter portal URL: ").strip()
    
    test_portal(portal_url)

