#!/usr/bin/env python3
"""
MAC Address Batch Tester
Tests multiple MAC addresses against a Stalker portal to see which are authorized.
"""

import sys
import time
from stalker_client import StalkerClient, load_config


def test_mac_address(portal_url, mac_address, timezone="America/New_York", verbose=False):
    """
    Test a single MAC address against the portal.
    
    Returns:
        dict: Result with status, message, and other details
    """
    client = StalkerClient(portal_url, mac_address, timezone, debug=False)
    
    result = {
        'mac': mac_address,
        'handshake': False,
        'status': None,
        'message': '',
        'authorized': False,
        'details': {}
    }
    
    try:
        # Handshake
        if not client.handshake():
            result['message'] = 'Handshake failed'
            return result
        
        result['handshake'] = True
        
        # Authenticate
        params = {
            'type': 'stb',
            'action': 'get_profile',
            'hd': '1',
            'ver': 'ImageDescription: 0.2.18-r24-pub-250; ImageDate: Fri Dec 28 18:45:22 EET 2018; PORTAL version: 5.6.0; API Version: JS API version: 343; STB API version: 146; Player Engine version: 0x582',
            'num_banks': '2',
            'sn': mac_address.replace(':', ''),
            'stb_type': 'MAG250',
            'image_version': '218',
            'auth_second_step': '0',
            'hw_version': '1.7-BD-00',
            'not_valid_token': '0',
            'metrics': '{"mac": "' + mac_address + '"}',
            'hw_version_2': 'a38a7c2b19ca1467a5e9fd29594d1877',
            'timestamp': str(int(time.time())),
            'api_signature': 'FF',
            'prehash': client.token if client.token else '',
            'JsHttpRequest': '1-xml'
        }
        
        response = client._make_request(client.api_path, params)
        
        if response and 'js' in response:
            js_data = response['js']
            result['status'] = js_data.get('status')
            result['message'] = js_data.get('msg', '')
            
            # Status 1 = authorized
            if result['status'] == 1:
                result['authorized'] = True
                result['details'] = {
                    'phone': js_data.get('phone', ''),
                    'name': js_data.get('fio', ''),
                    'account': js_data.get('account', '')
                }
            
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
        print("Example: 00:1A:79:16:BA:")
        base = input("Base MAC (first 5 octets with colons): ").strip()
        if not base.endswith(':'):
            base += ':'
        
        start = int(input("Start (0-255): ").strip() or "0")
        end = int(input("End (0-255): ").strip() or "255")
        
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
    print("  - 0.5 seconds (fast, may trigger rate limits)")
    print("  - 1 second (recommended)")
    print("  - 2-3 seconds (safe for strict servers)")
    delay_input = input("Delay in seconds (default: 1): ").strip()
    
    try:
        delay = float(delay_input) if delay_input else 1.0
    except ValueError:
        delay = 1.0
    
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
    
    results = []
    authorized_macs = []
    
    for i, mac in enumerate(macs, 1):
        print(f"[{i}/{len(macs)}] Testing {mac}...", end=' ')
        sys.stdout.flush()
        
        result = test_mac_address(portal_url, mac, timezone)
        results.append(result)
        
        if result['authorized']:
            print(f"✅ AUTHORIZED (Status: {result['status']})")
            authorized_macs.append(mac)
            if result['details'].get('name'):
                print(f"           Name: {result['details']['name']}")
            if result['details'].get('account'):
                print(f"           Account: {result['details']['account']}")
        elif result['status'] == 2:
            print(f"⚠️  Not Authorized (Status: 2)")
        elif result['status'] == 0:
            print(f"❌ Inactive (Status: 0)")
        elif not result['handshake']:
            print(f"❌ Handshake Failed")
        else:
            print(f"❓ Unknown (Status: {result['status']})")
        
        # Small delay to avoid overwhelming the server
        if i < len(macs):
            time.sleep(delay)
    
    # Summary
    print()
    print("="*60)
    print("Test Summary")
    print("="*60)
    print(f"Total MACs tested: {len(macs)}")
    print(f"Authorized: {len(authorized_macs)}")
    print(f"Not authorized: {sum(1 for r in results if r['status'] == 2)}")
    print(f"Inactive: {sum(1 for r in results if r['status'] == 0)}")
    print(f"Failed: {sum(1 for r in results if not r['handshake'])}")
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

