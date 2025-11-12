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
    
    def __init__(self, portal_url, mac_address, timezone="America/New_York", api_path=None, debug=False, serial_number=None):
        """
        Initialize the Stalker client.
        
        Args:
            portal_url: The base URL of the Stalker portal (e.g., http://portal.example.com)
            mac_address: MAC address of the set-top-box (format: 00:1A:79:XX:XX:XX)
            timezone: Timezone for the client
            api_path: Custom API path (default: tries common paths automatically)
            debug: Enable debug output
            serial_number: Custom serial number (default: MAC without colons)
        """
        self.portal_url = portal_url.rstrip('/')
        self.mac_address = mac_address.upper()
        self.timezone = timezone
        self.token = None
        self.session = requests.Session()
        self.debug = debug
        self.api_path = api_path
        
        # Serial number: only set if explicitly provided
        self.serial_number = serial_number
        self._serial_number_explicit = serial_number is not None
        
        # Set up default headers (like Go implementation)
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (QtEmbedded; U; Linux; C) AppleWebKit/533.3 (KHTML, like Gecko) MAG200 stbapp ver: 4 rev: 2116 Mobile Safari/533.3',
            'X-User-Agent': f'Model: MAG250; Link: Ethernet',
            'Accept': '*/*',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive'
        })
        
        # Set cookies (like Go implementation)
        self.session.cookies.set('PHPSESSID', 'null')  # Important: set to 'null' initially
        self.session.cookies.set('mac', self.mac_address)
        if self._serial_number_explicit:
            self.session.cookies.set('sn', self.serial_number)
        self.session.cookies.set('stb_lang', 'en')
        self.session.cookies.set('timezone', self.timezone)
    
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
            print(f"🔍 DEBUG: Request Headers:")
            print(json.dumps(dict(self.session.headers), indent=2))
            print(f"🔍 DEBUG: Request Cookies:")
            print(json.dumps({c.name: c.value for c in self.session.cookies}, indent=2))
            print(f"🔍 DEBUG: Params:")
            print(json.dumps(params, indent=2))
        
        try:
            response = self.session.get(url, params=params, timeout=10)
            
            if self.debug:
                print(f"🔍 DEBUG: Status Code: {response.status_code}")
                print(f"🔍 DEBUG: Response Headers:")
                print(json.dumps(dict(response.headers), indent=2))
                print(f"🔍 DEBUG: Response Text (first 500 chars):")
                print(response.text[:500])
            
            # Check for rate limiting
            if response.status_code == 429:
                retry_after = response.headers.get('Retry-After')
                x_ratelimit_reset = response.headers.get('X-RateLimit-Reset')
                x_ratelimit_remaining = response.headers.get('X-RateLimit-Remaining')
                
                if self.debug or True:  # Always show rate limit info
                    print(f"⚠️  RATE LIMITED (429)")
                    if retry_after:
                        print(f"   Retry-After: {retry_after} seconds")
                    if x_ratelimit_reset:
                        print(f"   X-RateLimit-Reset: {x_ratelimit_reset}")
                    if x_ratelimit_remaining:
                        print(f"   X-RateLimit-Remaining: {x_ratelimit_remaining}")
                    
                    # Print all headers that might contain rate limit info
                    print(f"   All headers:")
                    for key, value in response.headers.items():
                        if 'rate' in key.lower() or 'limit' in key.lower() or 'retry' in key.lower():
                            print(f"     {key}: {value}")
            
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
        if self.debug:
            print(f"🔄 Initiating handshake with {self.portal_url}...")
        
        # Auto-detect API path if not set
        if not self.api_path:
            self.detect_api_path()
        
        # Use prehash=0 for initial handshake (like Go implementation)
        params = {
            'type': 'stb',
            'action': 'handshake',
            'prehash': '0',
            'token': self.token if self.token else '',
            'JsHttpRequest': '1-xml'
        }
        
        response = self._make_request(self.api_path, params)
        
        if response and 'js' in response:
            js_data = response['js']
            
            # Handle case where js is an array (empty response)
            if isinstance(js_data, list):
                if self.debug:
                    print(f"⚠️  Server returned empty array - may need different approach")
                    print(f"   Try checking if cookies/headers match your TV app exactly")
                return False
            
            # Check for both lowercase and uppercase Token (Go code uses "Token" with capital T)
            token = js_data.get('token') or js_data.get('Token')
            
            if token:
                self.token = token
                if self.debug:
                    print(f"✅ Handshake successful! Token received: {self.token[:20]}...")
                return True
            elif self.token:
                # Token already set and server accepted it (like Go implementation)
                if self.debug:
                    print(f"✅ Handshake successful! Server accepted existing token")
                return True
            else:
                if self.debug:
                    print(f"❌ No token in response: {js_data}")
                return False
        else:
            if self.debug:
                print(f"❌ Handshake failed")
            return False
    
    def authenticate(self):
        """Authenticate with the portal using MAC address."""
        print(f"🔐 Authenticating with MAC address: {self.mac_address}...")
        if self._serial_number_explicit:
            print(f"   Serial Number: {self.serial_number}")
        
        # Minimal parameters - only essentials
        params = {
            'type': 'stb',
            'action': 'get_profile',
            'mac': self.mac_address,
            'prehash': self.token if self.token else '',
            'JsHttpRequest': '1-xml'
        }
        
        # Only add sn if explicitly set
        if self._serial_number_explicit:
            params['sn'] = self.serial_number
        
        response = self._make_request(self.api_path, params)
        
        if response and 'js' in response:
            js_data = response['js']
            
            if self.debug:
                print("✅ Authentication response received!")
                print(f"   Full response: {json.dumps(js_data, indent=2)}")
            else:
                print("✅ Authentication response received!")
            
            # Interpret status codes
            status_code = js_data.get('status')
            msg = js_data.get('msg', '')
            
            # Check if we got full profile (indicates successful auth)
            has_profile_data = 'login' in js_data or 'fname' in js_data or 'expire_billing_date' in js_data
            
            if has_profile_data:
                print(f"   📊 Status: 🟢 Successfully Authenticated!")
                if js_data.get('login'):
                    print(f"   👤 Login: {js_data['login']}")
                if js_data.get('fname'):
                    print(f"   📝 Name: {js_data['fname']}")
                if js_data.get('expire_billing_date'):
                    print(f"   📅 Subscription expires: {js_data['expire_billing_date']}")
                if js_data.get('expirydate'):
                    print(f"   📅 Expiry date: {js_data['expirydate']}")
                # Return True for successful authentication
                return True
            elif status_code == 1 or (isinstance(status_code, str) and status_code == "1"):
                print(f"   📊 Status: 🟢 Active and Authorized")
            elif status_code == 2 or (isinstance(status_code, str) and status_code == "2"):
                print(f"   📊 Status: 🔴 Not Authorized (Authentication Pending)")
                print(f"   ⚠️  This MAC address is not registered/authorized with the provider")
            elif status_code == 0 or (isinstance(status_code, str) and status_code == "0"):
                # Status 0 can mean different things in different contexts
                # If we have profile data, it's success; otherwise inactive
                if not has_profile_data:
                    print(f"   📊 Status: 🟡 Inactive")
            else:
                print(f"   📊 Status: ⚪ Unknown (code: {status_code})")
            
            if msg:
                print(f"   💬 Message: {msg}")
            
            # Display additional info if available
            if js_data.get('info'):
                print(f"   ℹ️  Info: {js_data['info']}")
            
            if js_data.get('template'):
                print(f"   🎨 Template: {js_data['template']}")
            
            if js_data.get('launcher_url'):
                print(f"   🔗 Launcher URL: {js_data['launcher_url']}")
            
            if js_data.get('launcher_profile_url'):
                print(f"   🔗 Launcher Profile: {js_data['launcher_profile_url']}")
            
            # Display account information if available
            if 'phone' in js_data and js_data['phone']:
                print(f"   📱 Phone: {js_data['phone']}")
            if 'account' in js_data and js_data['account']:
                print(f"   💳 Account: {js_data['account']}")
            
            # Show any other fields not explicitly handled
            if self.debug:
                known_fields = {'status', 'msg', 'info', 'template', 'launcher_url', 
                               'launcher_profile_url', 'phone', 'fio', 'account', 
                               'login', 'fname', 'expire_billing_date', 'expirydate'}
                other_fields = {k: v for k, v in js_data.items() if k not in known_fields and not isinstance(v, (dict, list))}
                if other_fields:
                    print(f"   🔍 Other fields: {json.dumps(other_fields, indent=2)}")
            
            # Return True if we have profile data (successful auth) or status is 1
            return has_profile_data or status_code == 1 or (isinstance(status_code, str) and status_code == "1")
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
            
            # Display first 10 channels with formatted output
            if channels:
                print("\n   First 10 channels:")
                for i, channel in enumerate(channels[:10]):
                    name = channel.get('name', 'Unknown')
                    ch_id = channel.get('id', 'N/A')
                    number = channel.get('number', 'N/A')
                    print(f"   {i+1:2d}. {name:40s} | ID: {ch_id:5s} | #: {number}")
                
                if len(channels) > 10:
                    print(f"\n   ... and {len(channels) - 10} more channels")
                    print(f"   💡 Enable debug mode to see full channel data")
            
            if self.debug and channels:
                print("\n   Full channel data (first 3):")
                print(json.dumps(channels[:3], indent=2))
            
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
            print(f"✅ Found {len(genres)} genres:\n")
            
            for genre in genres:
                title = genre.get('title', 'Unknown')
                genre_id = genre.get('id', 'N/A')
                alias = genre.get('alias', 'N/A')
                print(f"   - {title:30s} | ID: {genre_id:5s} | Alias: {alias}")
            
            if self.debug and genres:
                print("\n   Full genre data:")
                print(json.dumps(genres, indent=2))
            
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
        
        # Authentication successful - profile data already received
        print()
        print("="*60)
        print("✅ Connection test completed successfully!")
        print("="*60)
        print()
        print("📊 Summary:")
        print("   ✅ Portal connection")
        print("   ✅ API endpoint detection")
        print("   ✅ Handshake")
        print("   ✅ Authentication")
        print("   ✅ Profile data retrieved")
        print()
        print("💡 Note: Authentication already returned full profile.")
        print("   Additional API calls (genres, channels) can be made separately if needed.")
        print()
        
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


def save_config(portal_url, mac_address, timezone, serial_number=None, config_path="config.json"):
    """Save configuration to JSON file."""
    config = {
        "portal_url": portal_url,
        "mac_address": mac_address,
        "timezone": timezone
    }
    
    if serial_number:
        config["serial_number"] = serial_number
    
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
    
    # Serial Number (optional)
    if config.get('serial_number'):
        prompt = f"Serial Number (optional) [{config['serial_number']}]: "
        serial_number = input(prompt).strip()
        if not serial_number:
            serial_number = config['serial_number']
    else:
        serial_number = input("Serial Number (optional, defaults to MAC without colons): ").strip()
        if not serial_number:
            serial_number = None
    
    # Debug mode
    print()
    debug_choice = input("🐛 Enable debug mode? (y/n, default: n): ").strip().lower()
    debug = debug_choice == 'y'
    
    # Ask to save configuration if it's new or changed
    if not config or config.get('portal_url') != portal_url or \
       config.get('mac_address') != mac_address or config.get('timezone') != timezone or \
       config.get('serial_number') != serial_number:
        print()
        save_choice = input("💾 Save these settings to config.json? (y/n): ").strip().lower()
        if save_choice == 'y':
            save_config(portal_url, mac_address, timezone, serial_number)
    
    print()
    
    # Create client and test connection
    client = StalkerClient(portal_url, mac_address, timezone, debug=debug, serial_number=serial_number)
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

