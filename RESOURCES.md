# Stalker Portal Resources & Documentation

## Official Documentation

### Primary Resources
1. **Infomir Stalker Documentation** (Official)
   - URL: https://docs.infomir.com.ua/
   - Main documentation for Stalker Middleware
   - Installation, configuration, and feature guides

2. **Configuration Reference**
   - URL: https://docs.infomir.com.ua/doku.php?id=en:stalker:config_file
   - Detailed configuration options

3. **Installation Guide**
   - URL: https://docs.infomir.com.ua/doku.php?id=en:stalker:install_and_configure
   - Setup and deployment instructions

## API Actions & Endpoints

Based on the Stalker Portal API structure, here are common actions:

### Authentication & Profile
- `type=stb&action=handshake` - Initial connection, get token
- `type=stb&action=get_profile` - Get STB profile and authorization status
- `type=account_info&action=get_main_info` - Get account details

### Live TV (ITV)
- `type=itv&action=get_all_channels` - Get list of all TV channels
- `type=itv&action=get_ordered_list` - Get ordered channel list
- `type=itv&action=get_genres` - Get TV channel genres
- `type=itv&action=create_link` - Get streaming link for a channel
- `type=itv&action=get_epg_info` - Get EPG (Electronic Program Guide) data

### Video on Demand (VOD)
- `type=vod&action=get_categories` - Get VOD categories
- `type=vod&action=get_ordered_list` - Get VOD content list
- `type=vod&action=create_link` - Get streaming link for VOD content
- `type=vod&action=get_movie` - Get movie details

### Series/TV Shows
- `type=series&action=get_categories` - Get series categories
- `type=series&action=get_ordered_list` - Get series list
- `type=series&action=get_series_info` - Get series details

### Radio
- `type=radio&action=get_all_channels` - Get radio channels
- `type=radio&action=get_genres` - Get radio genres

### Recordings
- `type=pvr&action=get_list` - Get PVR recordings list

### Miscellaneous
- `type=epg&action=get_simple_data_table` - Get EPG data
- `type=weatherco&action=get_list` - Get weather information (if enabled)

## Response Format

All responses follow this structure:
```json
{
  "js": {
    // Actual data/response here
  },
  "text": "generated in: 0.013s; query counter: 1; ..."
}
```

### Status Codes (Authentication)
- **Status 1**: Active and Authorized (can access content)
- **Status 2**: Not Authorized (MAC not registered)
- **Status 0**: Inactive (subscription expired)

## API Parameters

### Common Parameters
- `token` - Session token (from handshake)
- `JsHttpRequest` - Usually "1-xml"
- `type` - Request type (stb, itv, vod, series, etc.)
- `action` - Action to perform

### STB (Set-Top Box) Parameters
- `mac` - MAC address
- `sn` - Serial number (MAC without colons)
- `stb_type` - Device model (e.g., "MAG250", "MAG254")
- `image_version` - Firmware version
- `ver` - Full version string
- `hw_version` - Hardware version

## MAG Device Types

Common MAG STB models:
- **MAG250** - Basic HD model
- **MAG254** - Enhanced HD with faster processor
- **MAG256** - 4K support
- **MAG322** - Budget model
- **MAG324** - Mid-range model
- **MAG351** - 4K HDR model
- **MAG410** - Android-based model

## Rate Limiting

Most Stalker portals implement rate limiting:
- Typically 3-5 requests per time window
- Cloudflare protection often used (429 errors)
- No standard headers (varies by provider)
- Best practice: 5-10 second delays between requests

## Security & Authentication Flow

1. **Handshake**: Get session token
2. **Authentication**: Verify MAC address
3. **Token Usage**: Include token in all subsequent requests
4. **Token Refresh**: Some portals require periodic re-handshake

## GitHub Resources

### Community Projects
- **stalker_portal** - https://github.com/azhurb/stalker_portal
  - Open source Stalker portal implementation
  
- **Ministra** (formerly Stalker)
  - Commercial version with additional features
  - https://ministra.tv/

## Testing Your Portal

Use these tools (included in this repository):
- `stalker_client.py` - Full connection test
- `test_portal.py` - Endpoint discovery
- `test_macs.py` - Batch MAC testing

## Common Issues

### 404 Errors
- API path varies by portal
- Try: `portal.php`, `server/load.php`, `stalker_portal/server/load.php`

### 429 Rate Limiting
- Use delays of 5-10 seconds between requests
- Each MAC test = 2 requests (handshake + auth)

### Status 2 (Not Authorized)
- MAC not registered with provider
- Contact your IPTV provider to register

### Cloudflare Protection
- Some portals use Cloudflare
- May require proper User-Agent headers
- This client mimics MAG250 STB

## Learning More

### Explore Your Portal
Use the interactive client to discover features:
```python
from stalker_client import StalkerClient

client = StalkerClient("http://portal.example.com", "00:1A:79:XX:XX:XX")
client.handshake()
client.authenticate()

# Try different actions
client.get_all_channels()
client.get_genres()
```

### Add New Features
Check `stalker_client.py` and add new methods based on the API actions above.

## Disclaimer

This client is for **testing legitimate connections** with your own IPTV service provider. Always:
- Use your own credentials
- Respect rate limits
- Follow your provider's terms of service
- Don't share credentials publicly

## Contributing

Found new API actions or features? Feel free to contribute:
1. Test the new action
2. Add a method to `stalker_client.py`
3. Document it
4. Submit a pull request

---

**Last Updated**: November 2025  
**Stalker Version Compatibility**: 5.x, 6.x (Ministra)

