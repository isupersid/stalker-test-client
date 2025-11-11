# Connection Test Results

## Test Summary for Portal: http://8k.iristv.cc

### ✅ Working Components:
- **Portal Connection**: SUCCESS
- **API Endpoint Detection**: SUCCESS (found: `stalker_portal/server/load.php`)
- **Handshake**: SUCCESS (token received)
- **Server Response**: SUCCESS (server is online and responding)

### ❌ Failed Components:
- **MAC Authorization**: FAILED
- **Reason**: Status code 2 = "Authentication request" (MAC not authorized)

---

## What This Means:

Your client is **correctly connecting** to the portal, but your MAC address `00:1A:79:16:BA:3E` is **not registered or authorized** with the provider.

### Status Code Meanings:
- **Status 1** = 🟢 Active and Authorized (can access content)
- **Status 2** = 🔴 Not Authorized (needs provider approval)
- **Status 0** = 🟡 Inactive (subscription expired)

**Your Status**: 2 (Not Authorized)

---

## Next Steps:

1. **Verify MAC Address**: 
   - Double-check that `00:1A:79:16:BA:3E` is the correct MAC address
   - Some providers use different MAC formats
   - Your actual device MAC might be different

2. **Contact Provider**:
   - Contact your IPTV provider (8k.iristv.cc)
   - Ask them to register/activate MAC: `00:1A:79:16:BA:3E`
   - Provide them with your subscription details

3. **Check Subscription**:
   - Verify your subscription is active
   - Some providers require payment before activation
   - Check if there are any outstanding issues

4. **Alternative MACs**:
   - Some providers allow you to register the MAC yourself via a web portal
   - Check if they have a customer portal or app
   - You might need to use the MAC from your actual set-top-box

---

## Technical Details:

### Handshake Response:
```json
{
  "token": "3DE781B9FBF0EB66FFF2C38C42C31D5C",
  "random": "54e25b36dd4cd460f86d28535400698944129bc0",
  "not_valid": 0
}
```

### Authentication Response:
```json
{
  "status": 2,
  "msg": "Authentication request",
  "template": "default"
}
```

The status code `2` clearly indicates the MAC is not in their authorized devices list.

---

## Testing with Real Device MAC:

If you have access to the actual set-top-box:

1. Find the MAC address on the device:
   - Usually on a sticker on the device
   - Or in Settings → System Info
   - Format: `00:1A:79:XX:XX:XX`

2. Update your `config.json` with the real MAC

3. Run the test again

---

## Conclusion:

✅ **Your test client is working perfectly!**  
❌ **The MAC address just needs to be authorized by the provider**

The "Unauthorized request" errors on subsequent API calls are **expected behavior** when the MAC is not authorized. Once the provider activates your MAC, all subsequent calls will work.

