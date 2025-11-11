#!/usr/bin/env python3
"""
Stalker Portal Test Client
A simple console application to test connections with Stalker middleware portals.
"""

import requests
import json
import time
import hashlib
import os
from urllib.parse import urljoin, quote


class StalkerClient:
    """Client for connecting to Stalker portal middleware."""
    
    def __init__(self, portal_url, mac_address, timezone="America/New_York", api_path=None, debug=False):
        """
        Initialize the Stalker client.
        
        Args:
            portal_url: The base URL of the Stalker portal (e.g., http://portal.example.com)
            mac_address: MAC address of the set-top-box (format: 00:1A:79:XX:XX:XX)
            timezone: Timezone for the client
            api_path: Custom API path (default: tries common paths automatically)
            debug: Enable debug output
        """
        self.portal_url = portal_url.rstrip('/')
        self.mac_address = mac_address.upper()
        self.timezone = timezone
        self.token = None
        self.session = requests.Session()
        self.debug = debug
        self.api_path = api_path
        
        # Set up default headers
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (QtEmbedded; U; Linux; C) AppleWebKit/533.3 (KHTML, like Gecko) MAG200 stbapp ver: 2 rev: 250 Safari/533.3',
            'Accept': '*/*',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive'
        })
    
    def _make_request(self, endpoint, params=None):
        """Make a request to the Stalker portal."""
        url = urljoin(self.portal_url + '/', endpoint)
        
        if params is None:
            params = {}
        
        # Add common parameters
        params['type'] = params.get('type', 'stb')
        params['action'] = params.get('action', 'handshake')
        
        if self.token:
            params['token'] = self.token
        
        if self.debug:
            print(f"🔍 DEBUG: Request URL: {url}")
            print(f"🔍 DEBUG: Params: {params}")
        
        try:
            response = self.session.get(url, params=params, timeout=10)
            
            if self.debug:
                print(f"🔍 DEBUG: Status Code: {response.status_code}")
                print(f"🔍 DEBUG: Response Headers: {dict(response.headers)}")
                print(f"🔍 DEBUG: Response Text: {response.text[:500]}")
            
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            if self.debug:
                print(f"🔍 DEBUG: HTTP Error: {e}")
                print(f"🔍 DEBUG: Response content: {response.text}")
            print(f"❌ Request failed: {e}")
            return None
        except requests.exceptions.RequestException as e:
            print(f"❌ Request failed: {e}")
            return None
        except json.JSONDecodeError as e:
            print(f"❌ Failed to parse JSON response: {e}")
            print(f"Response text: {response.text}")
            return None
    
    def detect_api_path(self):
        """Try to detect the correct API path for the portal."""
        common_paths = [
            'portal.php',
            'server/load.php',
            'stalker_portal/server/load.php',
            'c/version.js',
            'api/v1/',
        ]
        
        print("🔍 Trying to detect the correct API endpoint...")
        
        for path in common_paths:
            test_url = urljoin(self.portal_url + '/', path)
            if self.debug:
                print(f"🔍 DEBUG: Testing {test_url}")
            
            try:
                # Try a simple request
                response = self.session.get(test_url, timeout=5)
                if response.status_code == 200:
                    print(f"✅ Found working endpoint: {path}")
                    self.api_path = path
                    return path
                elif self.debug:
                    print(f"   Status {response.status_code}")
            except Exception as e:
                if self.debug:
                    print(f"   Failed: {e}")
                continue
        
        # Default to standard path
        print("⚠️  Could not detect API path, using default: server/load.php")
        self.api_path = 'server/load.php'
        return self.api_path
    
    def handshake(self):
        """Perform initial handshake with the portal."""
        print(f"🔄 Initiating handshake with {self.portal_url}...")
        
        # Auto-detect API path if not set
        if not self.api_path:
            self.detect_api_path()
        
        params = {
            'type': 'stb',
            'action': 'handshake',
            'prehash': self.token if self.token else '',
            'token': '',
            'JsHttpRequest': '1-xml'
        }
        
        response = self._make_request(self.api_path, params)
        
        if response and 'js' in response:
            js_data = response['js']
            if 'token' in js_data:
                self.token = js_data['token']
                print(f"✅ Handshake successful! Token received: {self.token[:20]}...")
                return True
            else:
                print(f"❌ No token in response: {js_data}")
                return False
        else:
            print(f"❌ Handshake failed")
            return False
    
    def authenticate(self):
        """Authenticate with the portal using MAC address."""
        print(f"🔐 Authenticating with MAC address: {self.mac_address}...")
        
        params = {
            'type': 'stb',
            'action': 'get_profile',
            'hd': '1',
            'ver': 'ImageDescription: 0.2.18-r24-pub-250; ImageDate: Fri Dec 28 18:45:22 EET 2018; PORTAL version: 5.6.0; API Version: JS API version: 343; STB API version: 146; Player Engine version: 0x582',
            'num_banks': '2',
            'sn': self.mac_address.replace(':', ''),
            'stb_type': 'MAG250',
            'image_version': '218',
            'auth_second_step': '0',
            'hw_version': '1.7-BD-00',
            'not_valid_token': '0',
            'metrics': json.dumps({"mac": self.mac_address}),
            'hw_version_2': 'a38a7c2b19ca1467a5e9fd29594d1877',
            'timestamp': str(int(time.time())),
            'api_signature': 'FF',
            'prehash': self.token if self.token else '',
            'JsHttpRequest': '1-xml'
        }
        
        response = self._make_request(self.api_path, params)
        
        if response and 'js' in response:
            js_data = response['js']
            print("✅ Authentication response received!")
            
            # Interpret status codes
            status_code = js_data.get('status')
            msg = js_data.get('msg', '')
            
            if status_code == 1:
                print(f"   📊 Status: 🟢 Active and Authorized")
            elif status_code == 2:
                print(f"   📊 Status: 🔴 Not Authorized (Authentication Pending)")
                print(f"   ⚠️  This MAC address is not registered/authorized with the provider")
            elif status_code == 0:
                print(f"   📊 Status: 🟡 Inactive")
            else:
                print(f"   📊 Status: ⚪ Unknown (code: {status_code})")
            
            if msg:
                print(f"   💬 Message: {msg}")
            
            # Display account information if available
            if 'phone' in js_data:
                print(f"   📱 Phone: {js_data['phone']}")
            if 'fio' in js_data:
                print(f"   👤 Name: {js_data['fio']}")
            if 'account' in js_data:
                print(f"   💳 Account: {js_data['account']}")
            
            # Return True only if status is 1 (authorized)
            return status_code == 1
        else:
            print("❌ Authentication failed")
            return False
    
    def get_profile(self):
        """Get profile information."""
        print("📋 Fetching profile information...")
        
        params = {
            'type': 'account_info',
            'action': 'get_main_info',
            'JsHttpRequest': '1-xml'
        }
        
        response = self._make_request(self.api_path, params)
        
        if response and 'js' in response:
            print("✅ Profile information:")
            print(json.dumps(response['js'], indent=2))
            return response['js']
        else:
            print("❌ Failed to get profile")
            return None
    
    def get_all_channels(self):
        """Get list of all channels."""
        print("📺 Fetching channel list...")
        
        params = {
            'type': 'itv',
            'action': 'get_all_channels',
            'JsHttpRequest': '1-xml'
        }
        
        response = self._make_request(self.api_path, params)
        
        if response and 'js' in response:
            channels = response['js'].get('data', [])
            print(f"✅ Found {len(channels)} channels")
            
            # Display first 10 channels
            for i, channel in enumerate(channels[:10]):
                print(f"   {i+1}. {channel.get('name', 'Unknown')} (ID: {channel.get('id', 'N/A')})")
            
            if len(channels) > 10:
                print(f"   ... and {len(channels) - 10} more channels")
            
            return channels
        else:
            print("❌ Failed to get channels")
            return None
    
    def get_genres(self):
        """Get list of genres."""
        print("🎬 Fetching genres...")
        
        params = {
            'type': 'itv',
            'action': 'get_genres',
            'JsHttpRequest': '1-xml'
        }
        
        response = self._make_request(self.api_path, params)
        
        if response and 'js' in response:
            genres = response['js']
            print(f"✅ Found {len(genres)} genres:")
            for genre in genres:
                print(f"   - {genre.get('title', 'Unknown')} (ID: {genre.get('id', 'N/A')})")
            return genres
        else:
            print("❌ Failed to get genres")
            return None
    
    def test_connection(self):
        """Run a full connection test."""
        print("="*60)
        print("🚀 Starting Stalker Portal Connection Test")
        print("="*60)
        print()
        
        # Step 1: Handshake
        if not self.handshake():
            print("\n❌ Connection test failed at handshake")
            print("   The portal may be offline or the URL is incorrect")
            return False
        
        print()
        time.sleep(1)
        
        # Step 2: Authenticate
        auth_success = self.authenticate()
        
        if not auth_success:
            print()
            print("="*60)
            print("⚠️  Connection Test Result: PARTIAL SUCCESS")
            print("="*60)
            print()
            print("✅ Portal connection: SUCCESS")
            print("✅ Handshake: SUCCESS")
            print("❌ MAC Authorization: FAILED")
            print()
            print("📌 Next Steps:")
            print("   1. Verify your MAC address is correct")
            print("   2. Contact your IPTV provider to register/activate this MAC")
            print("   3. Ensure your subscription is active")
            print("   4. Some providers require manual MAC address registration")
            print()
            return False
        
        print()
        time.sleep(1)
        
        # Step 3: Get profile (optional)
        try:
            self.get_profile()
        except Exception as e:
            print(f"⚠️  Profile fetch failed (non-critical): {e}")
        
        print()
        time.sleep(1)
        
        # Step 4: Get genres
        try:
            self.get_genres()
        except Exception as e:
            print(f"⚠️  Genre fetch failed (non-critical): {e}")
        
        print()
        time.sleep(1)
        
        # Step 5: Get channels
        try:
            self.get_all_channels()
        except Exception as e:
            print(f"⚠️  Channel fetch failed (non-critical): {e}")
        
        print()
        print("="*60)
        print("✅ Connection test completed successfully!")
        print("="*60)
        
        return True


def load_config(config_path="config.json"):
    """Load configuration from JSON file."""
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            print(f"✅ Loaded configuration from {config_path}")
            return config
        except json.JSONDecodeError as e:
            print(f"⚠️  Error parsing {config_path}: {e}")
            return {}
        except Exception as e:
            print(f"⚠️  Error reading {config_path}: {e}")
            return {}
    return {}


def save_config(portal_url, mac_address, timezone, config_path="config.json"):
    """Save configuration to JSON file."""
    config = {
        "portal_url": portal_url,
        "mac_address": mac_address,
        "timezone": timezone
    }
    
    try:
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        print(f"✅ Configuration saved to {config_path}")
        return True
    except Exception as e:
        print(f"⚠️  Error saving configuration: {e}")
        return False


def main():
    """Main entry point for the console application."""
    print()
    print("╔════════════════════════════════════════════════════════════╗")
    print("║          Stalker Portal Test Client v1.0                  ║")
    print("║          Set-Top-Box Connection Validator                 ║")
    print("╚════════════════════════════════════════════════════════════╝")
    print()
    
    # Try to load configuration from file
    config = load_config()
    
    # Get values from config or prompt user
    if config:
        print("Using configuration file (press Enter to keep, or type new value):")
        print()
    else:
        print("No configuration file found. Please enter your connection details:")
        print()
    
    # Portal URL
    if config.get('portal_url'):
        prompt = f"Portal URL [{config['portal_url']}]: "
        portal_url = input(prompt).strip()
        if not portal_url:
            portal_url = config['portal_url']
    else:
        portal_url = input("Portal URL (e.g., http://portal.example.com): ").strip()
    
    if not portal_url:
        print("❌ Portal URL is required!")
        return
    
    # MAC Address
    if config.get('mac_address'):
        prompt = f"MAC Address [{config['mac_address']}]: "
        mac_address = input(prompt).strip()
        if not mac_address:
            mac_address = config['mac_address']
    else:
        mac_address = input("MAC Address (e.g., 00:1A:79:XX:XX:XX): ").strip()
    
    if not mac_address:
        print("❌ MAC address is required!")
        return
    
    # Timezone
    default_timezone = config.get('timezone', 'America/New_York')
    timezone = input(f"Timezone (default: {default_timezone}): ").strip()
    if not timezone:
        timezone = default_timezone
    
    # Debug mode
    print()
    debug_choice = input("🐛 Enable debug mode? (y/n, default: n): ").strip().lower()
    debug = debug_choice == 'y'
    
    # Ask to save configuration if it's new or changed
    if not config or config.get('portal_url') != portal_url or \
       config.get('mac_address') != mac_address or config.get('timezone') != timezone:
        print()
        save_choice = input("💾 Save these settings to config.json? (y/n): ").strip().lower()
        if save_choice == 'y':
            save_config(portal_url, mac_address, timezone)
    
    print()
    
    # Create client and test connection
    client = StalkerClient(portal_url, mac_address, timezone, debug=debug)
    client.test_connection()
    
    print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()

