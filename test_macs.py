#!/usr/bin/env python3
"""
MAC Address Batch Tester
Tests multiple MAC addresses against a Stalker portal to see which are authorized.
"""

import sys
import time
from stalker_client import StalkerClient, load_config


def test_mac_address(portal_url, mac_address, timezone="America/New_York", verbose=False, max_retries=3, api_path=None, serial_number=None):
    """
    Test a single MAC address against the portal.
    
    Args:
        api_path: Pre-detected API path to avoid re-detection for each MAC
        serial_number: Optional custom serial number (only sent if provided)
    
    Returns:
        dict: Result with status, message, and other details
    """
    client = StalkerClient(portal_url, mac_address, timezone, api_path=api_path, debug=False, serial_number=serial_number)
    
    result = {
        'mac': mac_address,
        'handshake': False,
        'status': None,
        'message': '',
        'authorized': False,
        'details': {},
        'rate_limited': False,
        'was_rate_limited': False,  # Track if rate limiting occurred at any point
        'retry_wait_time': 0  # Track total time spent waiting for retries
    }
    
    try:
        # Handshake
        if not client.handshake():
            result['message'] = 'Handshake failed'
            return result
        
        result['handshake'] = True
        
        # Authenticate with retry logic (using minimal params)
        for attempt in range(max_retries):
            params = {
                'type': 'stb',
                'action': 'get_profile',
                'mac': client.mac_address,
                'prehash': client.token if client.token else '',
                'JsHttpRequest': '1-xml'
            }
            
            # Only add sn if explicitly set
            if client._serial_number_explicit:
                params['sn'] = client.serial_number
            
            response = client._make_request(client.api_path, params)
            
            # Check if we got rate limited by looking at the response
            if response is None:
                # Mark that we encountered rate limiting
                result['was_rate_limited'] = True
                
                # Could be rate limited, wait and retry
                if attempt < max_retries - 1:
                    backoff_time = 10 * (2 ** attempt)  # Exponential backoff: 10s, 20s, 40s
                    result['retry_wait_time'] += backoff_time
                    print(f"   ⏳ Rate limited, waiting {backoff_time}s before retry...")
                    time.sleep(backoff_time)
                    continue
                else:
                    result['rate_limited'] = True
                    result['message'] = 'Rate limited (max retries exceeded)'
                    return result
            
            if response and 'js' in response:
                js_data = response['js']
                result['status'] = js_data.get('status')
                result['message'] = js_data.get('msg', '')
                block_msg = js_data.get('block_msg', '')
                
                # Check if we got full profile (indicates successful auth)
                has_profile_data = 'login' in js_data or 'fname' in js_data or 'expire_billing_date' in js_data
                
                # Check for error conditions (device conflict, blocking messages, etc.)
                has_error = (
                    'conflict' in result['message'].lower() or 
                    'mismatch' in result['message'].lower() or
                    block_msg or
                    ('Authentication request' in result['message'] and not has_profile_data)
                )
                
                if has_profile_data and not has_error:
                    result['authorized'] = True
                    result['details'] = {
                        'phone': js_data.get('phone', ''),
                        'name': js_data.get('fname', '') or js_data.get('login', ''),
                        'account': js_data.get('account', ''),
                        'expiry': js_data.get('expire_billing_date', '') or js_data.get('expirydate', '')
                    }
                elif has_error:
                    # Mark as not authorized if there's an error condition
                    result['authorized'] = False
                    if block_msg:
                        result['message'] = f"{result['message']} - {block_msg}"
                elif result['status'] == 1 or (isinstance(result['status'], str) and result['status'] == "1"):
                    # Only treat status 1 as authorized if no errors
                    if not has_error:
                        result['authorized'] = True
                        result['details'] = {
                            'phone': js_data.get('phone', ''),
                            'name': js_data.get('fio', ''),
                            'account': js_data.get('account', '')
                        }
                
                return result
            
            # If we didn't get a valid response but no rate limit, break
            break
        
        return result
        
    except Exception as e:
        result['message'] = f'Error: {str(e)}'
        return result


def generate_mac_range(base_mac, start, end):
    """
    Generate a range of MAC addresses.
    
    Example: generate_mac_range("00:1A:79:16:BA:", 0, 255)
    Returns: ["00:1A:79:16:BA:00", "00:1A:79:16:BA:01", ...]
    """
    macs = []
    for i in range(start, end + 1):
        mac = f"{base_mac}{i:02X}"
        macs.append(mac)
    return macs


def format_mac(mac):
    """Ensure MAC address is properly formatted."""
    # Remove common separators
    clean = mac.replace(':', '').replace('-', '').replace('.', '')
    
    # Add colons every 2 characters
    if len(clean) == 12:
        return ':'.join(clean[i:i+2] for i in range(0, 12, 2)).upper()
    
    return mac.upper()


def main():
    """Main entry point."""
    print()
    print("╔════════════════════════════════════════════════════════════╗")
    print("║          MAC Address Batch Tester                         ║")
    print("║          Test Multiple MACs Against Portal                ║")
    print("╚════════════════════════════════════════════════════════════╝")
    print()
    
    # Load config for portal URL
    config = load_config()
    
    # Get portal URL
    if config.get('portal_url'):
        portal_url = input(f"Portal URL [{config['portal_url']}]: ").strip()
        if not portal_url:
            portal_url = config['portal_url']
    else:
        portal_url = input("Portal URL: ").strip()
    
    if not portal_url:
        print("❌ Portal URL is required!")
        return
    
    # Get timezone
    timezone = config.get('timezone', 'America/New_York')
    
    print()
    print("Choose input method:")
    print("  1. Enter MAC addresses manually (one per line)")
    print("  2. Load from file (macs.txt)")
    print("  3. Generate range (e.g., 00:1A:79:16:BA:00 to 00:1A:79:16:BA:FF)")
    print()
    
    choice = input("Choice (1/2/3): ").strip()
    
    macs = []
    
    if choice == '1':
        print()
        print("Enter MAC addresses (one per line, blank line to finish):")
        while True:
            mac = input("> ").strip()
            if not mac:
                break
            macs.append(format_mac(mac))
    
    elif choice == '2':
        filename = input("Filename (default: macs.txt): ").strip() or "macs.txt"
        try:
            with open(filename, 'r') as f:
                for line in f:
                    mac = line.strip()
                    if mac and not mac.startswith('#'):
                        macs.append(format_mac(mac))
            print(f"✅ Loaded {len(macs)} MAC addresses from {filename}")
        except FileNotFoundError:
            print(f"❌ File {filename} not found!")
            return
        except Exception as e:
            print(f"❌ Error reading file: {e}")
            return
    
    elif choice == '3':
        print()
        
        # Try to get default base from config
        default_base = ""
        if config.get('mac_address'):
            # Extract first 5 octets from config MAC
            config_mac = config['mac_address']
            octets = config_mac.split(':')
            if len(octets) >= 6:
                default_base = ':'.join(octets[:5]) + ':'
        
        if default_base:
            print(f"Example: 00:1A:79:16:BA:")
            base = input(f"Base MAC (first 5 octets with colons) [{default_base}]: ").strip()
            if not base:
                base = default_base
        else:
            print("Example: 00:1A:79:16:BA:")
            base = input("Base MAC (first 5 octets with colons): ").strip()
        
        if not base.endswith(':'):
            base += ':'
        
        start = int(input("Start (0-255, default: 0): ").strip() or "0")
        end = int(input("End (0-255, default: 255): ").strip() or "255")
        
        macs = generate_mac_range(base, start, end)
        print(f"✅ Generated {len(macs)} MAC addresses")
    
    else:
        print("❌ Invalid choice!")
        return
    
    if not macs:
        print("❌ No MAC addresses to test!")
        return
    
    # Confirm before testing
    print()
    print(f"About to test {len(macs)} MAC address(es)")
    print(f"Portal: {portal_url}")
    print()
    
    # Get delay between requests
    print("Delay between requests (to avoid rate limiting):")
    print("  ⚠️  Note: Each MAC = 2 requests (handshake + auth)")
    print("  - 5 seconds (recommended for this server)")
    print("  - 10 seconds (safer)")
    print("  - 15+ seconds (very safe, but slow)")
    delay_input = input("Delay in seconds (default: 5): ").strip()
    
    try:
        delay = float(delay_input) if delay_input else 5.0
    except ValueError:
        delay = 5.0
    
    # Calculate estimated time
    estimated_time = len(macs) * delay
    minutes = int(estimated_time // 60)
    seconds = int(estimated_time % 60)
    
    if minutes > 0:
        time_str = f"{minutes}m {seconds}s"
    else:
        time_str = f"{seconds}s"
    
    print(f"⏱️  Estimated time: ~{time_str}")
    print()
    confirm = input("Continue? (y/n): ").strip().lower()
    
    if confirm != 'y':
        print("Cancelled.")
        return
    
    # Test all MACs
    print()
    print("="*60)
    print("Starting MAC address tests...")
    print("="*60)
    print()
    
    # Detect API path once to avoid extra requests
    print("🔍 Detecting API endpoint...")
    dummy_client = StalkerClient(portal_url, macs[0], timezone, debug=False)
    dummy_client.detect_api_path()
    api_path = dummy_client.api_path
    print(f"✅ Using endpoint: {api_path}")
    print()
    
    results = []
    authorized_macs = []
    
    for i, mac in enumerate(macs, 1):
        print(f"[{i}/{len(macs)}] Testing {mac}...", end=' ')
        sys.stdout.flush()
        
        result = test_mac_address(portal_url, mac, timezone, api_path=api_path)
        results.append(result)
        
        if result['authorized']:
            print(f"✅ AUTHORIZED (Status: {result['status']})")
            authorized_macs.append(mac)
            if result['details'].get('name'):
                print(f"           Name: {result['details']['name']}")
            if result['details'].get('account'):
                print(f"           Account: {result['details']['account']}")
            if result['details'].get('expiry'):
                print(f"           Expires: {result['details']['expiry']}")
        elif 'conflict' in result['message'].lower() or 'mismatch' in result['message'].lower():
            print(f"🔴 Device Conflict (Status: {result['status']})")
            if result['message']:
                print(f"           {result['message']}")
        elif result['status'] == 2 or (isinstance(result['status'], str) and result['status'] == "2"):
            print(f"⚠️  Not Authorized (Status: 2)")
        elif result['status'] == 0 or (isinstance(result['status'], str) and result['status'] == "0"):
            # Status 0 without profile data means inactive
            print(f"❌ Inactive (Status: 0)")
        elif result.get('rate_limited'):
            print(f"⏱️  Rate Limited")
        elif not result['handshake']:
            print(f"❌ Handshake Failed")
        else:
            print(f"❓ Unknown (Status: {result['status']})")
            if result['message']:
                print(f"           {result['message']}")
        
        # Small delay to avoid overwhelming the server
        # Skip delay if we just waited for retries (already waited enough)
        if i < len(macs):
            if result.get('retry_wait_time', 0) > 0:
                # We already waited during retry, skip or reduce the delay
                remaining_delay = max(0, delay - result['retry_wait_time'])
                if remaining_delay > 0:
                    time.sleep(remaining_delay)
                # else: skip delay entirely, we waited enough
            else:
                # Normal delay between requests
                time.sleep(delay)
    
    # Summary
    print()
    print("="*60)
    print("Test Summary")
    print("="*60)
    print(f"Total MACs tested: {len(macs)}")
    print(f"Authorized: {len(authorized_macs)}")
    print(f"Not authorized: {sum(1 for r in results if r['status'] == 2 or (isinstance(r['status'], str) and r['status'] == '2'))}")
    print(f"Inactive: {sum(1 for r in results if r['status'] == 0 or (isinstance(r['status'], str) and r['status'] == '0'))}")
    
    rate_limited_count = sum(1 for r in results if r.get('was_rate_limited'))
    failed_retry_count = sum(1 for r in results if r.get('rate_limited'))
    
    if rate_limited_count > 0:
        print(f"Encountered rate limiting: {rate_limited_count} (recovered with retry)")
    if failed_retry_count > 0:
        print(f"Failed (max retries): {failed_retry_count}")
    
    print(f"Failed (handshake): {sum(1 for r in results if not r['handshake'])}")
    print()
    
    if authorized_macs:
        print("🎉 Authorized MAC addresses:")
        for mac in authorized_macs:
            print(f"   ✅ {mac}")
            # Find details
            for r in results:
                if r['mac'] == mac and r['details']:
                    if r['details'].get('name'):
                        print(f"      Name: {r['details']['name']}")
                    if r['details'].get('account'):
                        print(f"      Account: {r['details']['account']}")
                    if r['details'].get('expiry'):
                        print(f"      Expires: {r['details']['expiry']}")
        print()
        
        # Offer to save
        save = input("💾 Save authorized MACs to file? (y/n): ").strip().lower()
        if save == 'y':
            filename = input("Filename (default: authorized_macs.txt): ").strip() or "authorized_macs.txt"
            with open(filename, 'w') as f:
                for mac in authorized_macs:
                    f.write(f"{mac}\n")
            print(f"✅ Saved to {filename}")
    else:
        print("❌ No authorized MAC addresses found.")
        print()
        print("💡 Tips:")
        print("   - Verify the portal URL is correct")
        print("   - Contact your provider to check which MACs are registered")
        print("   - Check if your subscription is active")
        
        if rate_limited_count > 0:
            print()
            print("⚠️  Rate Limiting Detected:")
            print(f"   - {rate_limited_count} request(s) were rate limited")
            print("   - Consider increasing the delay between requests")
            print("   - Current delay: {:.1f}s, try 10-15s for heavily rate-limited servers".format(delay))
    
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

