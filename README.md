# Stalker Portal Test Client

A simple console application to test and validate connections with Stalker middleware portals (IPTV/Set-Top-Box providers).

## Features

- ✅ Portal handshake and authentication
- ✅ MAC address-based authentication
- ✅ Profile information retrieval
- ✅ Channel list fetching
- ✅ Genre list retrieval
- ✅ Connection validation testing

## Requirements

- Python 3.6 or higher
- `requests` library

## Installation

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Interactive Mode

Run the client in interactive mode:

```bash
python stalker_client.py
```

You'll be prompted to enter:
- Portal URL (e.g., `http://portal.example.com`)
- MAC Address (e.g., `00:1A:79:XX:XX:XX`)
- Timezone (optional, defaults to `America/New_York`)

### Using a Configuration File

To avoid entering your credentials each time, you can create a `config.json` file:

```json
{
  "portal_url": "http://portal.example.com",
  "mac_address": "00:1A:79:XX:XX:XX",
  "timezone": "America/New_York"
}
```

The application will automatically:
1. Load settings from `config.json` if it exists
2. Allow you to override values (press Enter to keep existing values)
3. Offer to save new settings when values change

**Note**: `config.json` is ignored by git to keep your credentials safe!

### Testing Multiple MAC Addresses

Use the batch MAC tester to test multiple MAC addresses:

```bash
python test_macs.py
```

This utility offers three input methods:

1. **Manual Entry**: Type MAC addresses one per line
2. **From File**: Load from a text file (e.g., `macs.txt`)
3. **Generate Range**: Automatically generate a range (e.g., `00:1A:79:16:BA:00` to `00:1A:79:16:BA:FF`)

**Example file format** (`macs.txt`):
```
# One MAC per line
00:1A:79:16:BA:3E
00:1A:79:16:BA:3F
00:1A:79:16:BA:40
```

The tool will:
- ✅ Show which MACs are authorized (Status 1)
- ⚠️ Show which need authorization (Status 2)
- ❌ Show inactive MACs (Status 0)
- 💾 Offer to save authorized MACs to a file

### Testing Portal Endpoints

To quickly discover available API endpoints:

```bash
python test_portal.py http://portal.example.com
```

This shows which endpoints respond and helps diagnose connection issues.

### Programmatic Usage

You can also use the client as a Python module:

```python
from stalker_client import StalkerClient

# Initialize client
client = StalkerClient(
    portal_url="http://portal.example.com",
    mac_address="00:1A:79:XX:XX:XX",
    timezone="America/New_York"
)

# Run full connection test
client.test_connection()

# Or use individual methods
client.handshake()
client.authenticate()
client.get_all_channels()
client.get_genres()
```

## How It Works

The Stalker middleware uses a specific authentication flow:

1. **Handshake**: Initial connection to obtain a session token
2. **Authentication**: Validates the set-top-box using MAC address
3. **API Calls**: Use the token to fetch channels, profile info, etc.

## Example Output

```
╔════════════════════════════════════════════════════════════╗
║          Stalker Portal Test Client v1.0                  ║
║          Set-Top-Box Connection Validator                 ║
╚════════════════════════════════════════════════════════════╝

============================================================
🚀 Starting Stalker Portal Connection Test
============================================================

🔄 Initiating handshake with http://portal.example.com...
✅ Handshake successful! Token received: abc123...

🔐 Authenticating with MAC address: 00:1A:79:XX:XX:XX...
✅ Authentication response received!
   📱 Phone: +1234567890
   👤 Name: Test User
   💳 Account: 12345
   📊 Status: 🟢 Active

📺 Fetching channel list...
✅ Found 150 channels
   1. Channel 1 (ID: 1)
   2. Channel 2 (ID: 2)
   ...

============================================================
✅ Connection test completed successfully!
============================================================
```

## Troubleshooting

### Common Issues

1. **Handshake fails**: Check that the portal URL is correct and accessible
2. **Authentication fails**: Verify your MAC address is registered with the provider
3. **Timeout errors**: Check your network connection and firewall settings
4. **No channels found**: Your account may not have active subscriptions

### MAC Address Format

The MAC address should be in the format `XX:XX:XX:XX:XX:XX`. Common formats:
- `00:1A:79:12:34:56` ✅
- `00-1A-79-12-34-56` (will be converted)
- `001A79123456` (will be converted)

## Security Notes

- Never share your MAC address or portal credentials publicly
- This tool is for testing legitimate connections with your service provider
- Keep your credentials secure

## License

MIT License - Feel free to use and modify for your testing needs.

