import os
from pathlib import Path

KB_PATH = Path(__file__).parent.parent / "data" / "kb_articles"
KB_PATH.mkdir(parents=True, exist_ok=True)

articles = {
"KB001_Password_Reset_Account_Lockout.md": """# KB001 — Password Reset & Account Lockout
**Category:** Account & Access | **Priority:** P2 — High | **Updated:** 2025-04-05

## Common Symptoms
- Cannot login to Windows/Mac
- "Invalid username or password" error
- Account locked after multiple login attempts
- "Your account has been locked for security reasons"
- Forgot corporate password
- Need password for recently joined account

## Account Lockout Causes
- **Automatic lockout**: 5 failed login attempts lock account for 30 minutes
- **Security incident**: Suspicious activity triggers automatic lock
- **Expired password**: Corporate passwords expire every 90 days (warning at 14 days)
- **Credential sync delay**: New accounts take up to 4 hours to sync across systems

## Troubleshooting Steps

### Step 1: Wait for Automatic Unlock (If Locked)
- Account automatically unlocks after **30 minutes** from lockout time
- You'll receive an email notification about the lockout
- If urgent, proceed to Step 2

### Step 2: Reset Password via Self-Service Portal
- Go to **https://password.company.com** (from any device)
- Click **"Forgot Password?"**
- Enter your email address (firstname.lastname@company.com)
- Verify identity using:
  - Security questions you set up
  - MFA code from Authenticator
  - Backup codes (if available)
- Create new password following requirements:
  - Minimum 12 characters
  - At least 1 uppercase, 1 number, 1 special character (!@#$%^&*)
  - Cannot contain your username or last 3 passwords
- New password takes effect immediately

### Step 3: Reset on Windows
- Open **Command Prompt** as Administrator
- Type: `net user username *`
- Replace "username" with your Windows login
- You'll be prompted to enter new password twice
- Restart computer after change

### Step 4: Reset on Mac
- At login screen: Click **"?" icon** (or press **Option** button)
- Select **"Reset Password"**
- Answer security questions or use Recovery Key
- Enter new password (same requirements as Windows)
- Authenticate with Apple ID if prompted

### Step 5: Sync Issues (Recently Joined Users)
- New accounts sometimes don't sync immediately to all systems
- Wait 4 hours, then try login again
- Check your hire date email — will specify when credentials activate
- If still failing: Contact IT with your employee ID

### Step 6: Unlock via Manager Approval (Emergency)
- If self-service fails: Contact your manager
- Manager can request emergency unlock via IT portal
- Unlock takes 30 minutes after approval
- Must reset password again after unlock

## Password Requirements & Best Practices
- **Length**: 12+ characters (longer = more secure)
- **Complexity**: Mix of upper, lower, numbers, symbols
- **Avoid**: Dictionary words, company name, birthdates, sequential numbers
- **Never share**: IT will NEVER ask for your password
- **Update**: Don't wait for expiration — change if you suspect compromise
- **Passphrase option**: Use 4+ random words instead (e.g., "Correct-Horse-Battery-Staple")

## Common Errors & Fixes
| Error | Cause | Fix |
|-------|-------|-----|
| "Password history violation" | Used a recent password | Use a new password not in last 3 |
| "Does not meet complexity" | Missing uppercase/number/special char | Add variety: `P@ssw0rd2025!` |
| "Change failed - try again later" | Sync delay | Wait 1 hour and retry |
| "Account locked" | Too many failed attempts | Wait 30 min or use Step 6 |

## When to Escalate (P2 Priority)
- Account locked and unable to work
- Password reset tool shows errors
- Forgot security questions + no backup codes
- Suspect account compromise/unauthorized access
- New employee account not syncing after 4 hours
- Executive/admin account issues (P1 URGENT)

## Password Security FAQ
**Q: How often do I need to change my password?**
A: Corporate policy requires change every 90 days. You'll get reminder emails starting 14 days before expiration.

**Q: Can I reuse an old password?**
A: No, system prevents using any of your last 3 passwords.

**Q: What if I forget my password multiple times?**
A: After 3 failed self-service attempts, your account locks for 24 hours for security. Contact IT.

**Q: Is my password stored anywhere?**
A: Never. Only encrypted hash is stored. IT cannot see your actual password.

## Resolution Rate: 92% resolved at L1 (self-service)
""",

"KB002_Email_Configuration_Setup.md": """# KB002 — Email Configuration & Setup
**Category:** Software & Apps | **Priority:** P3 — Medium | **Updated:** 2025-04-05

## Supported Email Platforms
- **Outlook Desktop** (Windows/Mac) — Recommended
- **Outlook Web** (https://outlook.office365.com)
- **Microsoft Teams** (integrated)
- **Mobile**: Outlook app (iOS/Android)
- **Compatibility**: Gmail, Apple Mail (via IMAP/SMTP)

## Common Symptoms
- Cannot add work email to Outlook
- "Authentication failed" error
- Emails not syncing
- Cannot send emails (SMTP error)
- Cannot receive emails (IMAP error)
- MFA blocking email access
- Calendar not showing
- Contacts not syncing

## Setup Instructions

### Quick Setup — Outlook Desktop (Recommended)
1. Open **Outlook** (or install from office365.com)
2. Click **File** → **Add Account**
3. Enter your email: **firstname.lastname@company.com**
4. Click **Connect**
5. Sign in with corporate credentials
6. If MFA prompt appears: Approve in Authenticator or enter code
7. Click **Done** — Outlook configures automatically
8. Emails appear within 1-5 minutes

**Troubleshooting**: If stuck on login:
- Close Outlook completely
- Delete cached credentials: Press Win+R → `netplwiz` → remove account → retry

### Setup — Outlook Web (No Installation)
1. Visit **https://outlook.office365.com**
2. Click **"Sign in"**
3. Enter email: **firstname.lastname@company.com**
4. Enter password
5. Approve MFA (Authenticator or phone call)
6. Works on any browser or device
7. No download needed

**Pro tips**:
- Use Outlook Web on public computers (more secure)
- Can set up out-of-office, delegated access, forwarding here
- Mobile notifications work best with Outlook app

### Setup — Mobile (Outlook App)
1. Download **Microsoft Outlook** from App Store or Play Store
2. Tap **"Add Account"**
3. Enter work email: **firstname.lastname@company.com**
4. Tap **"Sign In"**
5. Approve MFA prompt
6. Emails sync within 5 minutes
7. Calendar and contacts also sync automatically

### Setup — Apple Mail (Mac/iPhone)
1. **Mail app** → **Mail** (menu) → **Preferences**
2. Click **Accounts** tab → Click **+** button
3. Select **Microsoft Exchange**
4. Enter: Email = firstname.lastname@company.com
5. Enter password → Sign In
6. If prompted for "Autodiscover settings": Leave default, click **OK**
7. Verify MFA approval on your phone

### Setup — Gmail/Apple Mail (IMAP/SMTP)
**IMAP Settings** (receive mail):
- Server: **imap.office365.com**
- Port: **993**
- Security: **SSL/TLS**
- Username: **firstname.lastname@company.com**
- Password: Your corporate password

**SMTP Settings** (send mail):
- Server: **smtp.office365.com**
- Port: **587**
- Security: **STARTTLS**
- Username: **firstname.lastname@company.com**
- Password: Your corporate password

**Note**: Save username/password when prompted

## Troubleshooting Common Issues

### "Authentication failed"
- Verify correct email format: firstname.lastname@company.com
- Check if account locked (see KB001 — Password Reset)
- Disable MFA temporarily: https://mfa.company.com/settings
- For third-party apps: Use app-specific password:
  - Go to **https://mfa.company.com/app-passwords**
  - Generate app password
  - Use that password instead of corporate password
  - Password is 16 characters with hyphens

### "Cannot send mail" (SMTP Error)
- Check SMTP port is **587** (not 25, not 465)
- Check SMTP security is **STARTTLS** (not TLS)
- Try sending from Outlook Web first to isolate
- If Outlook Web works but desktop doesn't: Remove/re-add account
- Some corporate networks block port 587: use VPN or ask IT

### Emails not syncing
- Check internet connection (WiFi or cellular)
- **Outlook**: File → Options → Advanced → Offline → uncheck **Work Offline**
- Close and reopen email client
- Restart the device
- Check if account is in safe mode (Outlook → File → Info → check status)

### MFA Blocking Email Access
- Authenticator app must be installed **before** MFA enabled
- Third-party apps (Gmail, Apple Mail) require app-specific password (not regular password)
- Microsoft Authenticator app doesn't work? Try Microsoft Authenticator fallback
- If lost authenticator: See KB013 — MFA & Authentication Issues

### Out-of-office reply not working
- Must set in **Outlook Web** (https://outlook.office365.com)
- Click **Settings** (gear icon) → **Mail** → **Automatic replies**
- Set date range and message (internal + external)
- Desktop Outlook syncs within 1 hour
- Out-of-office doesn't stop email receiving, just auto-replies

### Emails in archive folder instead of inbox
- Archived emails move after 1 year (automatic archiving)
- Find them: Search for date range or click **Archive** folder
- To restore: Drag from Archive back to Inbox
- To disable auto-archive: Settings → Retention policies → contact IT

## Email Storage & Quotas
- **Inbox limit**: 50 GB per user
- **Auto-archive**: Emails auto-move after 1 year of inactivity
- **Manage storage**: 
  - Outlook → File → Account Settings → see used space
  - Delete emails older than 2 years to free space
  - Search for large attachments: `hasattachment:yes size:>5MB`
- **Shared mailboxes**: Do not count against personal quota

## Email Retention Policies
- **Standard user**: 3-year retention (then auto-deleted)
- **Department heads**: 7-year retention (compliance)
- **Legal hold**: Email never deleted if under litigation
- **Backup**: Daily backups kept for 30 days, IT can recover deleted email

## Security Best Practices
- Never reply to suspicious emails asking for password
- IT will NEVER ask for password via email
- Enable two-factor authentication (MFA) for account protection
- Use Outlook web to verify email before downloading
- Report phishing emails to **security@company.com**
- Don't download attachments from unknown senders
- Hover over links before clicking to verify sender

## Advanced Features

### Delegate Access
- Settings → Shared calendars → **Delegate access**
- Enter colleague's email
- Choose permissions (calendar view, task access)
- They get **Calendar** invite to add to Outlook

### Email Forwarding
- **Outlook Web**: Settings → Mail → Forwarding
- Choose: Forward, Keep copy, or Redirect
- Note: Forwarded emails go to other address, original inbox still receives

### Email Signatures
- **Outlook**: File → Options → Mail → Signatures
- Create signature with name, title, contact info
- Set to auto-apply to new emails
- Can have different signature for replies
- Use HTML for logo insertion

## When to Escalate
- Shared mailbox access needed
- Email migration from old system
- Delegate access for department
- Compromise suspected (URGENT — P1)
- Cannot setup after all troubleshooting
- Restore deleted email older than 30 days
- Archive/PST file recovery

## Resolution Rate: 88% resolved at L1
""",

"KB003_Network_WiFi_Connectivity.md": """# KB003 — Network & WiFi Connectivity
**Category:** Network & Infrastructure | **Priority:** P2 — High | **Updated:** 2025-04-05

## Common Symptoms
- Cannot connect to WiFi
- "WiFi no internet" despite connected signal
- Slow internet speed
- Connection drops frequently
- Cannot connect to corporate WiFi
- Device connects but no traffic
- One device loses connection while others work

## Network Types
- **Corporate WiFi (WPA3)**: Secure, recommended for work
- **Guest WiFi**: Limited access, for visitors
- **Mobile hotspot**: Personal phone as WiFi
- **VPN**: Encrypts traffic for security

## Troubleshooting Steps

### Step 1: Forget & Reconnect to WiFi
**Windows**:
- Click WiFi icon → Network settings
- Click **"Manage known networks"**
- Find your network → Click **"Forget"**
- Restart WiFi or restart computer
- WiFi icon → select network → enter password again

**Mac**:
- Click WiFi icon (top right) → "Open Network Preferences"
- Click WiFi in left menu → Advanced
- Select network → Click **"-"** to remove
- Click **"Apply"** → restart WiFi
- Reconnect and enter password

**Mobile**:
- Settings → WiFi → find network → tap **"Forget"**
- Turn WiFi off/on
- Reconnect and enter password

### Step 2: Restart Router/Access Point
- Find your WiFi router/access point
- Unplug power cable for 60 seconds
- Plug back in, wait for lights to stabilize (2-3 minutes)
- Try connecting again
- If multiple routers: Restart one at a time

### Step 3: Check Corporate WiFi Credentials
- Corporate WiFi uses **WPA3 Enterprise** (most secure)
- Requires:
  - **Network name**: CompanyWiFi-Secure
  - **Username**: firstname.lastname@company.com
  - **Password**: Corporate password (same as Windows login)
- If still fails: Try **CompanyWiFi-Guest** as temporary fix
  - No authentication needed
  - Limited to web traffic only

### Step 4: Reset Network Settings
**Windows**:
- Settings → System → Troubleshoot → Reset this PC
- Choose "Keep my files"
- Or: Settings → Network & Internet → **Reset**
- Restart computer

**Mac**:
- System Preferences → Network → WiFi → Advanced
- Click **"Remove WiFi Preferences"** (trash icon)
- Apply → restart
- Manually reconnect to networks

**Mobile**:
- Settings → General → Reset → **Reset Network Settings**
- Requires re-entering WiFi passwords
- Don't lose iPhone backup code!

### Step 5: Check DNS Settings
- If page won't load but WiFi shows connected:
  - Windows: Settings → Network → Advanced → DNS
  - Change to:
    - **Primary**: 8.8.8.8 (Google DNS)
    - **Secondary**: 8.8.4.4
  - Or use corporate DNS:
    - **Primary**: 10.0.0.1
    - **Secondary**: 10.0.0.2
  - Click Apply → test browser

### Step 6: Update WiFi Driver (Windows Only)
- Right-click Start → Device Manager
- Expand **Network adapters**
- Right-click WiFi adapter (Intel/Qualcomm/Broadcom)
- Click **Update driver**
- Choose "Search automatically for updated driver"
- Restart computer

### Step 7: Check VPN Connection
- If using company VPN:
  - VPN client must be connected before WiFi traffic
  - Check VPN app status (should show "Connected")
  - If disconnected: Open VPN app → tap "Connect"
  - Some sites only accessible via VPN
- If disconnected frequently:
  - Check VPN app for reconnection settings
  - Update VPN client (Settings → Apps → update VPN)

## WiFi Speed Issues

### Troubleshooting Slow Speed
1. **Move closer to router**: Signal strength decreases with distance
2. **Check interference**: Avoid using microwave/cordless phones while testing
3. **Change WiFi channel**: Router may be on congested channel
   - Android: WiFi → Long-press network → Modify → Channel
   - iPhone: Cannot change; contact IT
4. **Reduce connected devices**: Limit to 10 devices per router
5. **Use 5 GHz band if available**: Faster but shorter range
6. **Test via Ethernet**: If you have ethernet cable
   - Plug cable into computer and router
   - If speed good on ethernet, WiFi hardware is the issue

### Speed Test Results
- **Minimum acceptable**: 5 Mbps download, 1 Mbps upload
- **Recommended**: 25 Mbps download, 5 Mbps upload
- **For video calls**: 2.5 Mbps minimum, 4 Mbps recommended
- Test: Visit speedtest.net

## Frequent Disconnections Fix

### Common Causes
1. **Weak signal**: Move closer to router
2. **WiFi sleep settings**: Disable WiFi auto-sleep
   - Windows: Device Manager → Network adapters → right-click WiFi → Properties → Power Management → uncheck "Allow computer to turn off this device"
   - Mac: System Preferences → Network → WiFi → Advanced → uncheck "Turn off WiFi when not in use"
3. **Router overheating**: Ensure router has ventilation
4. **Outdated router firmware**: Router may need update
   - Check router manufacturer website (TP-Link, Cisco, etc.)
   - Download latest firmware
   - Upload to router via admin page (192.168.1.1)

### Mobile Disconnections
- Check device WiFi sleep: Settings → Power saving → disable
- Check auto-switch to mobile data: Settings → WiFi → disable "Switch to mobile data"
- Restart phone weekly to prevent memory leak

## Corporate WiFi Specific

### Can't Connect to Corporate WiFi
1. Check **network name visible**:
   - WiFi list shows "CompanyWiFi-Secure"?
   - If not: You're too far from access point
   - Move closer, try again
2. Verify credentials:
   - Username: firstname.lastname@company.com (exact format)
   - Password: Current corporate password
   - If recently changed password: Use new password
3. Try **Guest network** as temporary:
   - CompanyWiFi-Guest (open, no password)
   - Contact IT while connected to guest
4. Certificate issue (common on Mac):
   - System Preferences → Profiles
   - Install any "Cisco" or "Company" certificates that appear
   - Try corporate WiFi again

### Guest Network Limitations
- CompanyWiFi-Guest: Internet only
  - Can browse web, check email (Outlook Web)
  - Cannot access: File shares, printing, internal systems
  - Password-free, auto-connects when nearby

## When to Escalate
- Connection still failing after all steps
- Multiple people cannot connect (network down)
- Suspected security breach (unusual activity)
- VPN not connecting (requires IT)
- Enterprise WiFi certificate expired
- Ethernet also not working (whole computer offline)

## Network FAQ
**Q: Is corporate WiFi secure?**
A: Yes, WPA3 Enterprise is one of most secure WiFi standards.

**Q: Why does guest network have limited access?**
A: By design — guests don't need access to internal systems. Use corporate network for work.

**Q: Can I share my WiFi password?**
A: Yes, corporate password sharing is fine (it's your login anyway).

**Q: Is my traffic monitored?**
A: Corporate IT can see which sites visited, but not content (if using HTTPS). Never browse personal content at work.

## Resolution Rate: 79% resolved at L1
""",

"KB004_VPN_Remote_Access.md": """# KB004 — VPN & Remote Access
**Category:** Network & Security | **Priority:** P2 — High | **Updated:** 2025-04-05

## Common Symptoms
- Cannot connect to VPN
- VPN disconnects randomly
- "Authentication failed" error
- Slow connection through VPN
- Cannot access internal systems even when connected
- VPN shows "Connecting" but never connects
- Cisco AnyConnect crashes on startup

## VPN Requirement
- **Required for**: Accessing file shares, printers, internal applications from outside corporate network
- **When needed**: Working from home, coffee shops, airports, public WiFi
- **When NOT needed**: When at office on corporate WiFi
- **Security**: Encrypts all traffic, hides IP address

## VPN Types at Company

### Type 1: Cisco AnyConnect (Primary)
- **Download**: https://vpn.company.com
- **Protocol**: SSL/TLS (secure)
- **Authentication**: Corporate username/password + MFA
- **Best for**: Full network access, all applications

### Type 2: Pulse Secure (Secondary)
- **Download**: https://pulse.company.com
- **Protocol**: Pulse protocol (proprietary)
- **Use if**: Cisco AnyConnect fails
- **Best for**: Legacy systems, some printers

## Setup Instructions

### Install Cisco AnyConnect
1. Go to **https://vpn.company.com** (on corporate network or with VPN)
2. Click **"Download"** button
3. Choose your operating system (Windows/Mac/Linux)
4. Run installer, follow prompts
5. Accept license agreement
6. Click **"Install"**
7. Restart computer when complete
8. Look for Cisco icon in system tray

### Connect to VPN for First Time
1. Click **Cisco AnyConnect** icon (system tray or Applications)
2. In connection field, type: **vpn.company.com**
3. Click **"Connect"**
4. Enter username: **firstname.lastname** (not full email)
5. Enter password: Your corporate password
6. Approve MFA in Authenticator app
7. Wait for "Connected" status (30-60 seconds)
8. Green lock icon = secure connection

### Reconnecting to VPN
1. Cisco AnyConnect icon → Click **"Connect"**
2. It remembers vpn.company.com
3. Enter password + approve MFA
4. Connected in 10-30 seconds

## Troubleshooting

### "Cannot Connect" / "Connection Failed"
1. **Check internet**: Open browser, visit google.com
   - If pages don't load: Fix internet first (see KB003 — Network)
2. **Check Cisco service running**:
   - Windows: Services → "Cisco AnyConnect VPN Agent" → should be "Running"
   - If stopped: Right-click → Start
3. **Restart Cisco AnyConnect**:
   - Click Cisco icon → **"Disconnect"** (if connected)
   - Close Cisco completely
   - Open again → Connect
4. **Check credentials**:
   - Username: **firstname.lastname** (NOT @company.com)
   - Password: Current corporate password (changed recently? Use new)
5. **Try Pulse Secure instead**:
   - Download from **https://pulse.company.com**
   - Same credentials work
   - Some networks prefer Pulse

### "Authentication Failed"
- **Likely cause**: Wrong password or account locked
- **Fix**:
  1. Verify password is current (changed last 90 days?)
  2. Reset password: https://password.company.com
  3. Wait 1 minute after password change
  4. Try VPN again with new password
- **Still failing?**:
  - Check if account is locked: Try to login to Windows
  - If Windows login fails, reset via KB001

### "MFA Code Invalid"
- Check device time is automatic (not manual)
  - Wrong time = wrong codes
  - Windows: Settings → Time & Language → Set automatically
  - Mac: System Preferences → Date & Time → Set date and time automatically
- Codes expire every 30 seconds, use current code only
- Backup codes work too (longer, starts with "SG")
- If lost authenticator: Contact IT for MFA reset (P2)

### VPN Disconnects Randomly
- **Firewall/proxy issue**: Some networks block VPN
  - Try different network (mobile hotspot, guest WiFi)
  - If works elsewhere but not at home: Check home router
- **Idle timeout**: Cisco disconnects after 2 hours of inactivity
  - Open file from server to keep connection active
  - Or keep VPN window visible (doesn't minimize)
- **Computer sleep**: Computer going to sleep disconnects VPN
  - Settings → Power → Sleep after 1 hour only
  - Or keep computer awake during VPN session
- **Firewall dropping connection**: Disable firewall temporarily
  - Windows Defender → Firewall → Turn off temporarily
  - If VPN stable, firewall rule issue → escalate to IT
- **WiFi instability**: Switch to ethernet if possible
  - Ethernet = more stable than WiFi

### Slow Speed Over VPN
1. **Expected**: VPN adds 10-30% latency
2. **Test speed**: speedtest.net over VPN
   - Should be 50%+ of normal speed
   - If much slower: Might be wrong region server
3. **Choose closest VPN server**:
   - Cisco AnyConnect → Settings → Server → Select
   - Choose server in your region (e.g., US-East if in NY)
4. **Check for throttling**: 
   - Some companies limit VPN to 10 Mbps
   - Contact IT if critical work needs higher speed
5. **Use local-only apps**:
   - Apps on your computer: don't route through VPN
   - Only data to corporate systems goes through VPN
   - File shares, email, internal apps use VPN

### Cannot Access Files Over VPN
- **Common cause**: VPN connected but not showing shares
- **Fix**:
  1. Ensure VPN fully connected (look for "Connected" status in Cisco)
  2. Wait 30 seconds (DNS resolution)
  3. Try accessing via IP instead of name:
     - Instead of `\\server\folder`
     - Use `\\192.168.1.100\folder`
  4. If IP works but name doesn't: DNS issue → escalate to IT
- **Some apps need re-launch**: Open them AFTER VPN connects
  - If opened before VPN: Close, then reopen

### Cisco AnyConnect Crashes
- **Uninstall completely**:
  1. Control Panel → Programs → Uninstall
  2. Find "Cisco AnyConnect Secure Mobility Client"
  3. Click Uninstall
  4. On restart prompt: Choose Restart
  5. Download fresh from vpn.company.com and install
- **Update Cisco**:
  - Sometimes older versions buggy
  - After install, check Cisco icon → Check for updates
  - Install if available

## VPN Security Best Practices
- Always use VPN on public WiFi (coffee shops, airports)
- Disconnect VPN when done (closes potential vulnerabilities)
- Never give VPN credentials to colleagues
- If VPN credentials compromised: Contact IT immediately (P1)
- Two-factor authentication (MFA) required — enables detection of unauthorized attempts

## VPN FAQ
**Q: Can I use VPN from home?**
A: Yes, it's required to access company resources from home.

**Q: Why do I need VPN if using corporate WiFi?**
A: Technically not required on corporate WiFi (already encrypted), but can use for extra security.

**Q: Is my traffic private on VPN?**
A: Yes, encrypted end-to-end. IT can see destination but not content.

**Q: Can I use personal VPN service?**
A: No, violates security policy. Use company VPN only.

**Q: Why is VPN slow?**
A: Normal — encryption/decryption adds overhead. Expect 20-30% slower.

## When to Escalate
- Cannot connect after all troubleshooting (P2)
- VPN crashes repeatedly (P2)
- MFA reset needed (P2)
- Suspected unauthorized VPN use (P1 — URGENT)
- Large file transfers need optimization (escalate for compression)

## Resolution Rate: 82% resolved at L1
""",

"KB009_Monitor_Display_Issues.md": """# KB009 — Monitor & Display Issues
**Category:** Hardware | **Priority:** P3 — Medium | **Updated:** 2025-04-05

## Common Symptoms
- External monitor not detected
- Screen flickering or going black
- Wrong resolution / blurry display
- Only one of two monitors working
- No HDMI/DisplayPort signal
- Colors look washed out or incorrect
- Monitor enters sleep mode unexpectedly
- Laptop screen only, external not showing
- Multiple monitors competing for bandwidth

## Monitor Types & Connectors
- **HDMI**: Standard laptop connector (orange/gold, supports 4K@30Hz)
- **DisplayPort**: Smaller square connector, preferred (supports 4K@60Hz+)
- **USB-C**: Modern laptops, single cable for power + video + charging
- **VGA**: Older monitors (blue connector, max 1920x1080)
- **DVI**: Digital, less common
- **Docking Station**: Connects multiple displays via one cable

## Troubleshooting Steps

### Step 1: Check Physical Connections
- **Power check**:
  - Ensure monitor has power and is turned on
  - Check power LED on monitor (should be blue/green, not off)
  - Check power cable is securely plugged in
- **Cable inspection**:
  - Unplug cable from laptop
  - Unplug cable from monitor
  - Visually inspect for: bent pins, broken connectors, damage
  - Check both ends (sometimes damage on monitor end)
  - Gently blow to remove dust/debris
- **Reconnect firmly**:
  - DisplayPort cables: Push until you hear/feel **click**
  - HDMI cables: Firm push, slightly more resistance than USB
  - USB-C: Align and click (works from both orientations)
- **Try different cable**:
  - If available, test with known-good cable
  - If works with different cable: original cable is faulty
- **Try different monitor port**:
  - Some monitors have HDMI + DisplayPort
  - Try other port on same monitor
- **Docking station**:
  - Unplug dock from power, wait 30 seconds
  - Plug back in, watch for boot lights
  - Wait 2 minutes for full startup
  - Reconnect monitor to dock
  - Reconnect laptop to dock (use dock cable to laptop)

### Step 2: Detect Display Manually (Windows)
- Press **Win + P** to open projection menu:
  - **"Extend"**: Use second monitor with laptop screen
  - **"Duplicate"**: Mirror laptop screen on external
  - **"Second screen only"**: Use external only, laptop dark
  - **"PC screen only"**: Disable external, use laptop only
- If still not detected:
  - Click **Settings** → **System** → **Display**
  - Scroll down → **"Detect"** button
  - Wait 10-15 seconds (system scans for displays)
  - If multiple monitors: May find them one at a time
- **Advanced detection**:
  - Right-click desktop → **Display settings**
  - Bottom of page: **Advanced display settings**
  - Look for **"Unidentified display"** — click and configure

### Step 2 (Mac): Detect Display
- Click **Apple menu** → **System Preferences**
- Click **Displays**
- Hold **Option** key → click **"Detect Displays"**
- Wait 30 seconds while holding Option
- If monitor has internal speakers: Click **Audio** tab, select monitor

### Step 3: Update Graphics Drivers (Windows)
- Right-click **Start menu** → **Device Manager**
- Expand **Display adapters** section
- Right-click your GPU:
  - **NVIDIA** (GeForce/RTX series)
  - **AMD** (Radeon series)
  - **Intel** (Iris/UHD integrated)
- Click **Update driver**
- Choose **"Search automatically for updated drivers"**
- Windows downloads + installs
- When complete: **Restart computer**
- If update fails → Try manufacturer website:
  - nvidia.com/drivers
  - amd.com/drivers
  - intel.com/drivers

### Step 4: Check Display Settings (Windows)
- Right-click desktop → **Display settings**
- Under **Select and rearrange your displays**:
  - Make sure your monitor appears (numbered 1, 2, etc.)
  - If showing as **"Unidentified"**: Ignore, will work fine
- **Resolution**:
  - Click monitor you want to change
  - Find option labeled **"Recommended"** (in green)
  - Select recommended resolution
  - If no recommended showing: Driver needs update (Step 3)
- **Refresh rate**:
  - Click **Advanced display settings**
  - Look for **"Refresh rate"**
  - Select highest available (usually 60 Hz, can be 120+ for gaming)
- **Arrange multiple monitors**:
  - Drag monitor icons to match physical layout
  - Leftmost monitor on screen = left physically
  - This prevents cursor jumping
  - Click monitor → **"Make this my main display"**

### Step 5: Power Cycle Monitor
- Turn OFF monitor (physical power button on monitor itself)
- Unplug power cable from **wall outlet**
- Wait **60 full seconds** (crucial for draining capacitors)
- Plug back into wall
- Turn ON monitor
- Wait 30-45 seconds for full startup
- Try laptop again

### Step 6: Check Device Manager for Errors
- Right-click **Start** → **Device Manager**
- Look for any **yellow ⚠️ triangles** or **red X** marks
- Under **Display adapters**, if you see them:
  - Right-click → **Update driver**
  - If still showing error after update: → Escalate to IT
- Under **Universal Serial Bus controllers**:
  - Look for "Unknown Device" with warning
  - If found: Right-click → **Update driver**

### Step 7: BIOS/Firmware Update (Advanced)
**Use only if drivers updated but still not working**:
- Restart computer
- During startup (as computer boots), press **Del** or **F2** (varies by model)
  - Dell: Press **F2** repeatedly
  - HP: Press **F10** or **F2**
  - Lenovo: Press **F1** or **Del**
- Look for BIOS version/date
- Visit manufacturer website:
  - Dell.com, HP.com, Lenovo.com
  - Download latest BIOS for your model
  - Follow update wizard (usually auto-installs)
  - **Warning**: Do NOT interrupt BIOS update
  - Computer may not start if update is interrupted

## Flickering Screen Fix
- **Refresh rate wrong**:
  - Right-click desktop → Display settings → Advanced display settings
  - Change **Refresh rate** from 60 Hz to **59 Hz**
  - Test for 1 minute
  - If stops flickering: Use 59 Hz permanently
- **Cable issue**:
  - Try different cable (different DisplayPort/HDMI cable)
  - Shorter cable = more stable (less distance for signal)
- **Power saving conflicting**:
  - Settings → System → Power & sleep
  - Increase **Screen off time** to 20 minutes
- **Graphics performance**:
  - Right-click desktop → **GPU Control Panel** (NVIDIA/AMD)
  - Look for **Power settings** → change from **Battery saving** to **High performance**

## Monitor Not Turning Off
- Settings → System → Power & sleep
- Under **Sleep**, set **Turn off the display after** to desired time (e.g., 5 minutes)
- Click **Save**
- Ensure monitor itself supports sleep mode (check monitor manual)
- Disable screensaver if it's preventing sleep

## Colors Look Wrong / Washed Out
- Right-click desktop → **Display settings**
- Scroll down → **Advanced display settings**
- Look for **Color profile** or **ICC profile**
- Ensure set to **Default** (not custom profile)
- Monitor brightness/contrast:
  - Adjust buttons on monitor bezel (physical buttons on monitor)
  - Not software settings
  - Usually buttons on bottom/side of monitor
- For professionals needing color accuracy:
  - May need calibration → escalate to IT

## Multi-Monitor Setup

### For 3+ Monitors
- Each monitor needs dedicated DisplayPort or HDMI port
- Daisy-chaining NOT supported (can't daisy-chain monitors)
- Options:
  - Use docking station (supports 2-6 displays depending on model)
  - Use external USB-to-HDMI adapters
  - Ensure GPU supports it (most modern GPUs support 4+ displays)

### Verify GPU Supports Multi-Monitor
- Right-click desktop → **NVIDIA Control Panel** (if NVIDIA GPU)
- Look for **Set up multiple displays**
- Check maximum displays listed
- Most modern GPUs support 3-4 monitors minimum

### Arranging Monitors Properly
- Settings → Display → **Arrange your displays** section
- Drag monitor icons to match physical positions:
  - Left monitor: Drag icon to left in the arrangement
  - Right monitor: Drag icon to right
  - Stacked: Drag above/below
- **Test movement**: Move mouse from left to right monitor
  - Should flow smoothly without jumping
  - If jumps: Re-arrange the icons to match physical layout

### Different Resolutions on Multiple Monitors
- Allowed, but Windows will scale differently
- Example: 1920x1080 + 2560x1440 on same system works
- High DPI monitor + standard monitor may have scaling issues
- Windows should auto-scale, but may need manual adjustment

## Display Not Appearing After Wake

### Computer Goes to Sleep, Monitor Stays Black
- Cause: GPU or monitor not waking properly
- Fix:
  1. Move mouse or press key (should wake)
  2. If black still: Press power button on monitor
  3. If still black: Unplug display cable, plug back in
  4. Try different cable if available
  5. Update graphics driver (Step 3)

## When to Escalate
- Hardware failure suspected (lines on screen, dead pixels, permanent discoloration)
- Docking station replacement needed
- 4+ monitors configuration request
- Specialty display (4K, ultrawide 5K, HDR) configuration
- Cannot update drivers (driver errors)
- Persistent flickering after troubleshooting all steps
- New laptop model compatibility issues

## Monitor Cable Types — Quick Reference
| Type | Speed | Max Resolution | Connector |
|------|-------|-----------------|-----------|
| HDMI 2.0 | Medium | 4K@30Hz | Gold rectangular |
| DisplayPort 1.4 | Fast | 8K@60Hz | Square pin |
| USB-C | Medium | 4K@30Hz | Small reversible |
| Thunderbolt 3/4 | Very fast | 6K+ | USB-C shape |
| VGA | Slow | 1920x1080 | Blue 3-pin |

## Prevention Tips
- Use quality cables (avoid cheap adapters)
- Avoid bending cables sharply (can damage pins internally)
- Don't hot-swap connections while powered on
- Keep drivers updated (Enable automatic Windows Update)
- Use docking station for frequent connections
- Label cables if you have multiple monitors
- Keep documentation of monitor model + driver version

## Resolution Rate: 85% resolved at L1
""",

"KB010_Audio_Microphone_Issues.md": """# KB010 — Audio & Microphone Issues
**Category:** Hardware | **Priority:** P3 — Medium | **Updated:** 2025-04-05

## Common Symptoms
- No sound from speakers or headphones
- Microphone not working in Teams/Zoom
- Echo or feedback during calls
- Audio crackling or cutting out
- Bluetooth headset not connecting
- Wrong audio device selected
- Sound muted unexpectedly
- One ear not working
- Microphone too quiet

## Troubleshooting Steps

### Step 1: Check Volume & Mute Status
- Click the **speaker icon** in system tray (bottom right)
- Check if volume slider is set to **0** or **muted**
- If red X or mute symbol: Click to unmute
- Slide volume up to at least **50%**
- For laptops: Check physical **mute key** on keyboard
  - Often **F1** or **F4** key
  - May require pressing **Fn + F1**
- Check volume on the **device itself**:
  - Headphones may have volume knob
  - Speakers may have physical volume buttons
  - Adjust those too if available

### Step 2: Select Correct Audio Device
- Right-click speaker icon → **Open Sound settings**
- Under **Output** section:
  - Dropdown menu shows current output device
  - If showing "Speakers" but you want "Headphones": Change it
  - If showing "HDMI" but you want "Speakers": Change it
  - Don't see your device? Proceed to Step 4 (device recognition)
- Under **Input** section:
  - Select the correct microphone
  - Usually shows "Microphone" or "Built-in Microphone"
  - If multiple: Try each one to find working one
  - Hover over device name to see location (built-in, USB, etc.)
- **Test microphone**:
  - Click **"Test your microphone"**
  - Speak clearly
  - Green bar should move as you speak
  - If bar doesn't move: Microphone selected is not working

### Step 3: Restart Audio Service (Windows)
- Press **Win + R**, type `services.msc`, press **Enter**
- Find **"Windows Audio"** in the list
- Right-click → **Restart**
- Wait 5 seconds
- Also find and restart **"Windows Audio Endpoint Builder"**
- Right-click → **Restart**
- Try playing audio again

### Step 4: Reinstall Audio Driver (Windows)
- Right-click **Start** → **Device Manager**
- Expand **"Sound, video and game controllers"**
- Right-click your audio device (Realtek, IDT, etc.)
- Click **"Uninstall device"**
- Check box: **"Delete the driver software for this device"**
- Click **"Uninstall"**
- Restart computer
- Windows will automatically reinstall driver from system files
- If that doesn't work: 
  - Visit manufacturer website (your laptop brand)
  - Download latest audio driver
  - Install manually

### Step 5: Bluetooth Headset Issues
- Go to **Settings → Bluetooth & devices**
- Find your headset in the list
- Click **"Remove device"** (forget it)
- Put headset in **pairing mode**:
  - Usually hold power button for 5-10 seconds
  - Look for flashing blue light
  - Check headset manual for pairing button
- In Windows Bluetooth settings: Click **"Add device"**
- Select **"Bluetooth"** → choose your headset
- Wait for pairing to complete
- Test audio
- **If audio quality poor**:
  - Click your headset → **"Advanced"** options
  - Look for "Hands-Free" or "HFP" profile: Disable this
  - Keep only "A2DP Stereo" profile (better quality)
  - If phone audio needed: Re-enable HFP temporarily

### Step 6: Bluetooth Not Finding Device
- Make sure headset is in pairing mode (flashing light)
- Move headset closer to computer (within 3 feet)
- Disable then re-enable Bluetooth:
  - Windows Bluetooth settings → turn off Bluetooth
  - Wait 5 seconds → turn back on
- Restart Bluetooth service:
  - Services.msc → "Bluetooth Support Service" → Restart
- If still not found: Restart headset
  - Hold power button to turn off
  - Wait 10 seconds
  - Power back on
  - Try pairing again

### Step 7: Teams/Zoom Audio Settings
- **Microsoft Teams**:
  - Open Teams → Click profile (top right) → **Settings**
  - Go to **Devices** section
  - **Audio devices**: Select microphone and speaker
  - Click **"Make a test call"** (blue button)
  - Follow prompts to record message
  - You'll hear playback to verify both mic and speaker
  - Accept or redo until happy
- **Zoom**:
  - Open Zoom → Click profile → **Settings**
  - Click **Audio** in left menu
  - **Microphone**: Select correct device
  - **Speaker**: Select correct device
  - Click **"Test Speaker"** button
  - Speak into microphone to test

### Step 8: Echo During Calls
- Primary cause: Microphone picking up speaker audio
- **Fixes**:
  1. Use headphones (isolates mic from speakers)
  2. Mute microphone when not speaking
  3. In Teams/Zoom: Enable **Noise suppression**:
     - Teams: Settings → Devices → **Microphone** → Noise suppression set to **High**
     - Zoom: Settings → Audio → **Suppress background noise** → set to **High**
  4. Move microphone away from speakers
  5. Lower speaker volume
  6. Close other applications with audio

## Audio Crackling or Cutting Out

### Causes & Fixes
1. **Bluetooth interference**:
   - Bluetooth uses 2.4 GHz (same as WiFi)
   - Move away from WiFi router
   - Use 5 GHz WiFi instead of 2.4 GHz if available
   - Disable Bluetooth when not in use
2. **Low battery** (headphones):
   - Charge headphones completely
   - Most issues at <20% battery
3. **Too many devices**:
   - Disconnect other Bluetooth devices
   - Limit to 1 active Bluetooth connection
4. **Driver issue**:
   - Update audio driver (Step 4)
5. **Sample rate mismatch**:
   - Settings → Sound → Advanced → Speaker properties
   - Click **"Additional device properties"**
   - Go to **Advanced** tab
   - Change sample rate from 48 kHz to **44.1 kHz** (more compatible)

## Background Noise Reduction

### Built-in Windows Settings
- Settings → Sound → Volume mixer
- Find your microphone → Click **"Volume and device preferences"**
- Look for **Noise cancellation**: Enable if available
- Set to **High**

### Teams Specific
- Teams recognizes: Keyboard typing, background noise
- Settings → Devices → Microphone → **Noise suppression** → **High**

### Zoom Specific
- Settings → Audio → **Suppress background noise** → **High**

## Audio Not Working via HDMI (Monitor Speakers)

### Typical Setup
- Monitor has speakers
- Want sound through monitor speakers
- Currently no sound

**Fix**:
1. Right-click speaker icon → Sound settings
2. Under **Output**: Click dropdown
3. Select **"Speakers (HDMI)** or similar
4. Test audio
5. If doesn't appear:
   - Step 3: Restart audio service
   - Step 4: Reinstall audio driver
   - Make sure HDMI cable fully plugged in (see KB009)

## Microphone Not Working on Mac

### Mac Built-in Microphone
- System Preferences → Sound → **Input** tab
- Microphone should show "Built-in Microphone"
- Drag **Input volume** slider to middle
- Speak → bars should move
- If no movement: May be a hardware issue

### USB Microphone on Mac
- Plug in USB microphone
- Systemglass Preferences → Sound → Input
- Select your USB microphone from list
- Test volume

### Permission Issue (Common on Mac)
- Go to System Preferences → **Security & Privacy** → **Privacy**
- Click **Microphone** in left menu
- Your application (Teams, Zoom, etc.) should be **checked/enabled**
- If not listed: Click **+** and add the application
- Restart application after enabling

## When to Escalate
- Hardware failure (sounds distorted even after driver update)
- Multiple devices not being recognized
- Audio service won't restart
- Microphone missing from Device Manager
- Persistent echo/feedback with noise suppression enabled
- Conference room audio system not working
- Headset replacement needed
- Audio driver not available for your hardware

## Audio Hardware FAQ
**Q: Why does audio cut out over Bluetooth?**
A: Bluetooth has limited range and bandwidth. WiFi interference is common. Try moving closer or using wired.

**Q: Can I use headphones and speakers simultaneously?**
A: Windows: Yes, if plugged in (HDMI + USB + 3.5mm can work together)
Bluetooth: Only one device at a time

**Q: My microphone is too quiet even at 100%.**
A: Some mics have low sensitivity. Options:
- Use better microphone (external USB)
- Position microphone closer (within 6 inches)
- In Teams/Zoom: Increase mic input level (if option available)

## Resolution Rate: 76% resolved at L1
""",

"KB011_OneDrive_SharePoint_Issues.md": """# KB011 — OneDrive & SharePoint Issues
**Category:** Software & Apps | **Priority:** P3 — Medium | **Updated:** 2025-04-05

## Common Symptoms
- Files not syncing to cloud
- "Sync paused" message
- Cannot access shared SharePoint site
- "You don't have permission" error
- Files showing red X icon
- OneDrive icon missing from system tray
- Sync stuck on one file
- Blue circles instead of green checkmarks

## OneDrive vs SharePoint
- **OneDrive**: Personal cloud storage (1 TB limit)
- **SharePoint**: Team/Department storage (shared access)
- Both sync similar way, managed by same application

## Troubleshooting Steps

### Step 1: Check Sync Status
- Click the **OneDrive cloud icon** in system tray (bottom right)
  - If not visible: Search **"OneDrive"** in Start menu → launch
- Icon colors mean:
  - **Green checkmark**: Synced, all current
  - **Blue circles**: Syncing in progress (normal, wait)
  - **Red X**: Error (sync paused)
  - **Yellow icon**: Warning (some files can't sync)
- **Sync status** should show **"Up to date"** or **"Syncing..."**
- If shows **"Sync paused"**: Click → **Resume sync**
- If says **"Issues detected"**: Expand to see which files failed

### Step 2: Restart OneDrive
- Right-click OneDrive icon → **"Quit OneDrive"**
- Wait **10 full seconds** (let it fully close)
- Open Start menu → Search **"OneDrive"** → launch
- Sign in if prompted with company credentials
- OneDrive will restart syncing

### Step 3: Check Internet Connection
- Open browser → visit google.com
- If pages don't load: Fix internet first (see KB003 — Network)
- OneDrive needs internet to sync
- Once internet back, OneDrive resumes automatically

### Step 4: Reset OneDrive (Most Effective Fix)
**Important: This does NOT lose files**
- Press **Win + R**
- Type or paste: `%localappdata%\\Microsoft\\OneDrive\\onedrive.exe /reset`
- Press **Enter**
- OneDrive icon will disappear (30 seconds to 2 minutes)
- Computer may show "OneDrive is busy"
- **Wait for auto-restart** (icon reappears)
- If doesn't restart automatically:
  - Search "OneDrive" in Start → launch
  - May need to login with company credentials again
- OneDrive will re-sync all files (may take time for large folders)

### Step 5: Check File Path Length
- Windows has **260 character path limit**
- File path = full folder structure + filename
- Example: `C:\\Users\\john.doe\\OneDrive\\Documents\\Projects\\2025\\Q1\\Reports\\Finance\\Monthly Reports\\Pending Approvals\\file.xlsx` = 120+ characters
- **If too long**:
  - Move file closer to root: `C:\\Users\\john.doe\\OneDrive\\file.xlsx`
  - Or shorten folder names
  - Or move to SharePoint (no path limit)
- **Find long paths**:
  - Right-click file → Properties → Location
  - Count characters in path
  - If over 260: Reorganize

### Step 6: Fix Permission Issues
- **Can't access shared folder**:
  - Right-click folder → **Share** → check if you're listed
  - If not: Ask folder owner to add you
  - Owner: Click folder → **Share** → add your email
- **"You don't have permission" error**:
  - Verify your account has **"Can edit"** permission (not just "Can view")
  - Contact folder owner if needed
  - Wait 1 hour after permission change to take effect
- **For SharePoint sites**:
  - Go to the site → Click **Settings** → **Site permissions**
  - Check if you're in a group with access
  - Contact site owner if missing

### Step 7: Free Up Cloud Storage
- **Your quota**: 1 TB per user
- **Check usage**:
  - OneDrive icon → Settings → **Manage storage**
  - Shows GB used of 1 TB
- **Free up space**:
  - Delete very old files or duplicate files
  - Move large files to OneDrive shared archive
  - Use **Files On-Demand** (see below)
- **Files On-Demand** (don't count toward quota until synced):
  - Right-click file → **"Free up space"**
  - File becomes cloud-only (cloud icon, not downloaded)
  - Can open anytime online
  - Useful for large archived files
  - Re-enable: Right-click cloud icon → **"Always keep on this device"**

### Step 8: Sync Paused for Large Files
- OneDrive has limits:
  - File size: Max 15 GB per file (rare limit)
  - Filename: Max 255 characters
- **If file won't sync**:
  - Right-click file → Check name length
  - If over 255 characters: Rename shorter
  - If over 15 GB: Upload via SharePoint web instead
  - Contact IT if still failing

### Step 9: Selective Sync (Only Sync Some Folders)
- OneDrive icon → Settings (gear icon) → **Account**
- Click **"Choose folders"**
- Uncheck folders you don't need locally
- Keep checked only folders you use daily
- More free space = less disk used
- Unchecked folders still accessible online

## Common Error Messages

| Error | Cause | Fix |
|-------|-------|-----|
| "Sync paused" | Network issue or too many conflicts | Restart OneDrive (Step 2) |
| "You don't have permission" | Access not granted | Ask owner to share, wait 1 hour |
| "File is too large" | File exceeds 15 GB | Use SharePoint upload instead |
| "Filename too long" | Over 255 characters | Rename file shorter |
| "Sync fails on one file" | File locked by another user | Ask user to close file, wait 5 min |
| "Files showing red X" | Sync errors stacked | Reset OneDrive (Step 4) |

## SharePoint Specific Issues

### Can't Access SharePoint Site
- Site URL: example.sharepoint.com/sites/teamname
- If 403 Forbidden error:
  - You may not have access
  - Request access via site (button appears)
  - Or ask site owner to add you
- If 404 Not Found:
  - Site may have been deleted
  - Check if you have the right URL
  - Search site name in Outlook

### Shared File Locked by Another User
- Common in SharePoint
- Causes: Other person has file open
- **While locked**:
  - Can view file, but not edit
  - Can download copy and edit locally
  - Sync not possible while locked
- **Solution**:
  - Ask other user to close file
  - Wait 5-10 minutes
  - Then OneDrive resumes sync
- **For shared documents**:
  - Use **Office online** (edit in browser)
  - Prevents locking issues
  - Multiple people can edit simultaneously

## Version History & Recovery

### Restore Old Version of File
- **In OneDrive**:
  - Right-click file → **Version history**
  - Select a previous version
  - Click **"Restore"**
  - File reverts to that version
  - Original version moved to "Old versions"
- **In SharePoint**:
  - Click file → three dots **"..."** → **Version history**
  - Select version → **"Restore"**
  - May need restore permission

### Recover Deleted Files
- OneDrive deletes kept for **93 days**
- Click **Recycle Bin** in OneDrive
- Find file → Right-click → **Restore**
- File back in original location
- After 93 days: Permanently deleted (cannot recover)
- For older: Contact IT (may have backup copy) — requires P2 escalation

## Organizational Sharing Best Practices
- **Share with group, not individuals**: If whole team needs access
  - Right-click folder → Share → Add "Finance Team" group (not each person)
  - Easier to manage permissions
  - New team members auto-get access
- **Don't over-share**: Only share what's needed
- **Use SharePoint for team files**: Better than personal OneDrive for collaboration
- **Archive old files**: Move to "Archive" folder with limited access

## When to Escalate
- Tenant-wide sync issues (multiple people affected)
- Need file restoration from 90+ days ago
- SharePoint site provisioning needed
- External sharing permissions required
- Data loss suspected
- Sync won't complete even after reset (P2)
- Suspect account compromise

## OneDrive FAQ
**Q: How much storage do I get?**
A: 1 TB (1,000 GB) per user. Cannot purchase more (use SharePoint if need more).

**Q: Can I access OneDrive from phone?**
A: Yes, download "Microsoft OneDrive" app from App Store / Play Store.

**Q: Is my data backed up?**
A: Yes, backed up to regional data center. Multiple copies maintained.

**Q: How long are deleted files kept?**
A: 93 days in recycle bin. After 93 days permanently deleted.

**Q: Can I share with external people?**
A: Yes, but requires IT approval first. Contact IT for external sharing policy.

## Resolution Rate: 73% resolved at L1
""",

"KB013_MFA_Authentication_Issues.md": """# KB013 — MFA & Authentication Issues
**Category:** Account & Access | **Priority:** P2 — High | **Updated:** 2025-04-05

## Common Symptoms
- Not receiving MFA push notifications
- Authenticator app showing wrong code
- "Your sign-in was blocked" error
- Cannot login from new location/device
- Lost authenticator app / new phone
- Backup codes not working
- "Invalid code" error repeatedly
- Approving push notification does nothing

## MFA Methods Available
- **Microsoft Authenticator app** (Recommended)
- **TOTP code** (Time-based, 6 digits)
- **Backup codes** (One-time use)
- **SMS text message** (Backup)
- **Phone call** (Final fallback)

## Troubleshooting Steps

### Step 1: Check Authenticator App Setup
- Open **Microsoft Authenticator** app on your phone
- Look for your work account listed
- Should show account email (firstname.lastname@company.com)
- Tap account → **Check if account is healthy**
- If missing account: Proceed to Step 4 (re-enroll)

### Step 2: Verify Device Time is Correct
- **Most common cause of code errors**: Wrong device time
- Codes are time-based (valid only 30 seconds)
- If phone clock wrong: Codes invalid
- **Fix**:
  - iPhone: Settings → General → Date & Time → **Set Automatically** (toggle ON)
  - Android: Settings → System → Date & Time → **Set Automatically** (toggle ON)
  - Windows: Settings → Time & Language → **Set time automatically** (toggle ON)
- Wait 1 minute for time sync
- Try MFA again

### Step 3: Push Notifications Not Arriving
- **Check connectivity**: Phone must have internet (WiFi or cellular)
- **Open Authenticator first**: Before logging in
  - Open the app
  - Wait for notification
  - Then try login
- **Check permissions** (very common):
  - **iPhone**: 
    - Settings → Notifications → **Microsoft Authenticator** → Allow notifications
    - Make sure switch is GREEN/ON
  - **Android**:
    - Settings → Apps → Authenticator → **Notifications** → Toggle ON
    - Also check: Settings → Apps → **Notifications** → find Authenticator → allow
- **Disable battery optimization** (Android):
  - Settings → Battery → Optimization
  - Find **Microsoft Authenticator**
  - Select **"Don't optimize"**
- **Restart app**:
  - Force-close Authenticator (remove from recent apps)
  - Reopen fresh
  - Try login again

### Step 4: Manual Code Entry (If Push Fails)
- If push notification doesn't arrive:
  - Open **Authenticator app**
  - Find your account
  - Tap to see **6-digit code**
  - Copy the code (currently valid)
  - Go to login → enter code
  - **Important**: Codes expire every 30 seconds
  - Use immediately (within 10 seconds of copying)
  - Type carefully (no spaces)

### Step 5: Conditional Access Block
- Error message: **"Your sign-in has been blocked"** or similar
- Cause: Unusual location, unmanaged device, or risky activity detected
- **Solutions**:
  1. Try login from **corporate network** (office WiFi)
  2. Try login over **VPN** (even at home, connects through corporate)
  3. Use **corporate laptop** instead of personal device
  4. **Newer device**: Microsoft may require extra verification
  5. **Risky login**: Geographic change (different country)
     - Wait 24 hours for system to trust location again
     - Or login from recognized location (office)

### Step 6: Lost Authenticator (Most Urgent)
**If you've lost your phone or uninstalled the app without backup**:

**Option 1: Use Backup Codes** (if you saved them)
- You should have been given backup codes when MFA enabled
- Each code = single use
- Where to find: Should be in email or password manager
- For login:
  - Instead of entering MFA code, click **"Use a code instead"**
  - Enter backup code (long code with numbers/dashes)
  - Use entire code, including dashes

**Option 2: Use Alternate Verification Method**
- At MFA prompt, look for: **"Can't access authenticator app?"** link
- May have these options:
  - **SMS to phone**: Text message with code
  - **Phone call**: Ring phone, listen for code
  - **Email code**: Code sent to email address
- Use whichever method you enrolled in
- Check spam folder if email code doesn't arrive

**Option 3: Contact IT for Emergency Reset**
- **P2 Priority** (4-hour response time)
- If NO backup codes + alternative methods don't work
- Contact IT immediately with:
  - Your name
  - Employee ID
  - Your manager's name
  - Reason (lost phone, uninstalled app, etc.)
- IT will verify your identity
- Once verified: Can reset MFA
- Then set up MFA again on new device

### Step 7: MFA Reset After Getting New Phone
**Preparation** (BEFORE getting new phone):
- **Get temporary code**: Contact IT (P2) if urgent
- Or use backup codes if available
- **DO NOT wipe old phone yet** (need to set up on new phone first)

**Steps**:
1. On **NEW phone**: Download "Microsoft Authenticator" app
2. On **old phone**: Open Authenticator
   - Find your account
   - **Screenshot the QR code** (long-press account → see QR code) — might not show, use manual entry instead
   - Or note: Account ID (firstname.lastname@company.com)
3. On **new phone**: Authenticator app → **"Add account"** → **"Work or school account"**
4. Choose: **"Scan QR code"** (if you have screenshot) OR **"Enter manually"** (if no QR)
   - Manual entry: Enter email address
5. Complete setup, verify works
6. **NOW** you can wipe/dispose of old phone
7. If you already wiped old phone: See Step 6 (contact IT)

### Step 8: Set Up MFA for First Time
- You'll receive email: **"Complete your MFA setup"**
- Click link in email → **https://mfa.company.com/setup**
- Scan **QR code** with new phone using Authenticator app
- Or if camera not working: Click **"Can't scan?**" → Manual entry option
- **Verify works**: Authenticator shows 6-digit code
- Enter that code to confirm
- **Save backup codes**:
  - System shows 10 codes
  - **WRITE THESE DOWN** or screenshot
  - Store in password manager
  - Essential for if you lose phone
- Click **"Done"**
- MFA now enabled, required for all logins

## Backup Codes Management

### What Are Backup Codes?
- 10 one-time codes given when MFA enabled
- Each code = single use only
- Cannot reuse same code
- Look like: `SG-1234-5678-90AB`
- Valid for 1 year from issuance

### Where to Store Backup Codes
- **Secure options** (preferred):
  - Password manager (LastPass, Bitwarden, 1Password)
  - Locked drawer at home
  - Locked safe
- **NOT secure**:
  - Sticky note on monitor
  - Email (unencrypted)
  - Screenshot with no protection
  - Text document on computer

### Generate New Backup Codes
- If running low or lost originals:
  - https://mfa.company.com/backup-codes
  - Old codes expire when new codes generated
  - Save new codes same location as before

## Troubleshooting Invalid Code Error

| Situation | Fix |
|-----------|-----|
| Code shows as invalid immediately | Device time wrong — set automatically |
| Code accepted but still blocked | Conditional access triggered — use VPN/office |
| Backup code invalid | Already used — use next code |
| Backup code not working | Code expired (1 year old) — generate new ones |
| Push approved but still blocked | Additional verification needed — wait 24 hours |

## MFA Best Practices
- **Always have 2+ backup methods**:
  - Authenticator + SMS phone + backup codes
  - Not just one method
- **Save backup codes immediately** after setup
  - Don't procrastinate
  - Store secure location
- **Update MFA on new phone BEFORE wiping old**:
  - Set up on new, THEN wipe old
  - If you wipe first: Contact IT
- **Enroll backup phone number**:
  - If lose primary phone, can use backup
  - Settings → MFA → Add phone number
- **Never share MFA codes**: IT will NEVER ask for them
- **Recognize social engineering**: Scammers may say "give me code"
  - Always refuse
  - Report to security@company.com

## When to Escalate (P2 — 4 Hour SLA)
- MFA reset required
- Cannot access any backup methods
- Lost authenticator app without backup codes
- Suspect account compromise / unauthorized access
- Device enrolled twice in conflict
- Third-party app needs credential help

## Urgent Escalation (P1 — 1 Hour)
- Suspected account compromise or hacking attempt
- Cannot access security-critical account
- Need immediate emergency access to systems

## MFA FAQ
**Q: Why does company require MFA?**
A: It blocks 99% of hacking attempts. Worth the extra step.

**Q: Is Authenticator app really that secure?**
A: Yes, much safer than SMS (SMS can be intercepted).

**Q: What if someone has my backup codes?**
A: Each code single-use. Generate new codes, old ones become invalid.

**Q: Do I need MFA when on corporate WiFi?**
A: Yes, always required for login (even office network).

**Q: How long do backup codes last?**
A: 1 year from issuance. After 1 year, must generate new.

## Resolution Rate: 65% resolved at L1 (35% need MFA reset by IT)
""",

"KB012_Mobile_Device_Issues.md": """# KB012 — Mobile Device & MDM Issues
**Category:** Hardware | **Priority:** P3 — Medium | **Updated:** 2025-04-05

## Common Symptoms
- Cannot enroll device in Intune/MDM
- Company email not working on phone
- Apps not installing from Company Portal
- Phone marked as non-compliant
- Cannot access company resources from mobile
- Device keeps showing "Setup required" error

## Supported Devices
- **iOS**: iPhone 11 or newer, iOS 16+
- **Android**: Samsung, Google Pixel, OnePlus (Android 12+)
- **BYOD**: Personal device enrollment available

## MDM (Mobile Device Management)
- **What it does**: Manages mobile devices for security
- **Why required**: Ensures devices meet security standards
- **What IT can see**: Device model, OS version, compliance, work apps
- **What IT CANNOT see**: Personal photos, texts, apps, location, browsing

## Troubleshooting Steps

### Step 1: Check Device Compliance Status
- **iOS**:
  - Open **Company Portal** app
  - Tap **Devices** (bottom navigation)
  - Select your device
  - Check **Compliance** status (green = compliant, red = non-compliant)
  - If non-compliant: App lists what needs fixing
- **Android**:
  - Open **Company Portal** app
  - Tap hamburger menu (three lines) → **Devices**
  - Select your device
  - Check **Device health status**
  - Scroll down to see specific compliance issues
- **Common compliance issues**:
  - OS too old (e.g., iOS 15, needs iOS 16+)
  - No passcode/PIN
  - Device jailbroken/rooted (unauthorized)
  - Missing security patch
  - Encryption disabled
  - Unsigned app installed

### Step 2: Update Operating System
- **Compliance usually requires latest or latest-1 OS**
- **iOS**:
  - Settings → General → Software Update
  - If available: Tap "Install Now" or "Download and Install"
  - Will restart phone during install
  - Plug into power (won't work on battery)
  - Wait 20-30 minutes
- **Android**:
  - Settings → System → System update
  - Tap "Check for updates"
  - If available: Download → Install
  - May require restart
- After update: Recheck Company Portal compliance

### Step 3: Re-enroll Device
- **Most effective fix** for most issues
- **iOS**:
  1. Company Portal app → Tap device → **"Remove device"**
  2. Confirm removal
  3. Wait 5 minutes
  4. Open Company Portal → Tap **"Sign in"**
  5. Follow enrollment wizard (4-5 steps)
  6. Accept all permissions when prompted
  7. Verify compliance: green checkmark appears
- **Android**:
  1. Company Portal → Hamburger menu → Settings
  2. Tap your device → **"Remove from Company Portal"**
  3. Confirm removal
  4. Wait 5 minutes
  5. Open Company Portal → Sign in
  6. Re-enroll, accept permissions
  7. Verify compliance

### Step 4: Email Setup — Outlook Mobile
- **Install from App Store/Play Store**: Search "Microsoft Outlook"
- **Setup**:
  1. Open Outlook → Tap **"Add Account"** or **"Sign in"**
  2. Enter work email: **firstname.lastname@company.com**
  3. Tap **"Sign In"**
  4. Enter password (corporate password)
  5. Approve MFA:
     - Authenticator app opens on phone
     - Approve push notification, OR
     - Enter MFA code manually
  6. Email syncs within 5 minutes
  7. Calendar and contacts sync automatically

### Step 5: Authenticator Setup for MFA
- **Install**: "Microsoft Authenticator" from app store
- **For new setup**:
  1. Open Authenticator → **"Add account"** → **"Work or school"**
  2. Scan QR code when prompted
  3. Or enter manually: email address + password
  4. Approve push notification
  5. Verify works
- **On new phone**:
  1. Complete setup before wiping old phone (see KB013)
  2. If already wiped: Contact IT for MFA reset

### Step 6: Authenticator App Issues
- **Lost authenticator**:
  - Contact IT for P2 reset
  - Have manager name + employee ID ready
- **App shows multiple accounts**: Remove duplicates
  - Long-press account → **"Remove"** (keep only one)
- **Codes always invalid**: Check device time
  - Settings → Date & Time → **Set Automatically** toggle ON
  - Wait 1 minute
  - Try again

## Mobile App Installation from Company Portal

### Installing Work Apps
- **iOS**:
  - Company Portal → Apps (tab)
  - Tap app you want
  - Tap **"Get"** or **"Install"**
  - If prompted: Tap **"Open App Store"**
  - Confirm installation
  - Wait 1-2 minutes for install
- **Android**:
  - Company Portal → **Apps** (tab)
  - Find app → Tap **"Install"**
  - Confirm install
  - App downloads and installs

### Common Installation Issues
- **"Not available for your device"**:
  - Device doesn't meet minimum requirements
  - Usually: OS too old, or not enough storage
  - Update OS (Step 2)
  - Free up storage: Delete photos, old messages
- **"Installation failed"**:
  - Try again (often temporary)
  - Restart phone
  - Uninstall then reinstall
- **"Installation pending"**:
  - Can take 5-10 minutes
  - Keep Company Portal open
  - Don't force-quit the app
  - If still pending after 20 min: Restart phone

## Personal Device Privacy (BYOD)

### What IT Can See
✓ Device model and serial number
✓ Operating system version
✓ Compliance status (compliant/non-compliant)
✓ Installed company apps
✓ Device location (while accessing work resources)

### What IT CANNOT See
✗ Personal photos or videos
✗ Text messages or iMessages
✗ Phone calls or voicemails
✗ Personal apps (Facebook, Instagram, etc.)
✗ Passwords or private data
✗ Browsing history (personal apps)
✗ Personal location when not accessing work

### Work Data Isolation
- Company email/data stored separately from personal data
- If you remove device from MDM:
  - Work apps removed
  - Work email removed
  - Personal data remains untouched
  - No need for full factory reset

## Device Compliance

### Why Device Must Be Compliant
- Ensures security standards met
- Protects company data
- Prevents unauthorized users
- Required by company policy + industry standards

### Common Compliance Requirements
- **Passcode/PIN**: Must be set (min 6 characters)
- **Up-to-date OS**: Latest or latest-1 version
- **Security patches**: All available patches installed
- **Not jailbroken/rooted**: No unauthorized modifications
- **Encryption enabled**: Automatic on modern iOS/Android
- **Screen lock**: Auto-lock after 5 minutes of inactivity

### How to Maintain Compliance
- **Update OS promptly** when available
- **Update security patches** monthly
- **Use strong passcode** (not birthdate, sequential numbers)
- **Don't jailbreak or root** (removes security)
- **Disable unknown sources** (Android)
- **Review installed apps** (remove suspicious apps)

## Mobile Email Data Plan

### Email Downloaded vs. Synced
- Outlook mobile: **Syncs emails** (doesn't need full history)
- Reduces storage: Only current + recent emails on phone
- Cloud storage: All emails stored on Microsoft servers
- **Recommendation**: Set Outlook to sync last 3 months
  - Settings → Accounts → select account → Sync Settings
  - "Mail to sync" → 3 months (balances storage vs. access)

### Mobile Data Usage
- **Outlook email**: ~1-5 MB per day (varies by email volume)
- **Calendar/contacts**: Minimal (few KB per day)
- **Over WiFi preferred**: Reduces cellular data usage
- **Enable**: Settings → Accounts → Download only on WiFi (optional)

## Lost or Stolen Device

### URGENT — Do This Immediately
1. **Call IT**: 1-800-555-HELP (immediately!)
2. **Explain**: Device lost or stolen
3. **IT will**:
   - Remotely remove device from MDM
   - Wipe company data from device
   - Block access to company services
   - Personal data may remain (depends on settings)
4. **Time critical**: Do within 1 hour if possible

### After IT Removes Device
- Cannot access company email
- Cannot access company apps
- Cannot access file shares
- Company data removed (email, contacts, calendar)
- Personal data remains (varies by configuration)

## Setup Assistant (New Device)

### What Happens During Enrollment
1. You sign in with corporate account
2. Install security certificates (behind scenes)
3. Install Company Portal app
4. Verify device meets compliance requirements
5. Install company apps (if needed)
6. Setup complete, device ready for work

### Typical Time
- iOS: 10-15 minutes
- Android: 10-15 minutes
- If long setup: Check internet (slow WiFi causes delays)

## When to Escalate
- Cannot enroll after re-enroll attempts
- MFA reset needed
- Device lost or stolen (URGENT — P1)
- Replacement device provisioning
- Device doesn't meet minimum requirements (cannot upgrade)
- Company app crashes immediately after install

## Mobile FAQ
**Q: Can I use my personal phone for work?**
A: Yes, BYOD enrollment available. Meets security requirements.

**Q: Will IT see my personal photos?**
A: No, work and personal data are completely isolated.

**Q: What if I quit — can IT access my data?**
A: No, only removes work apps/data. Personal data stays.

**Q: Can I use iPhone + Android?**
A: Yes, most companies support both. May need to enroll both separately.

**Q: Do I need an authenticator app?**
A: Yes, required for MFA. Takes 2 minutes to setup.

## Resolution Rate: 70% resolved at L1
""",
}

for filename, content in articles.items():
    (KB_PATH / filename).write_text(content.strip(), encoding="utf-8")
    print(f"  ✅ {filename}")

print(f"\n  {len(articles)} KB articles generated in {KB_PATH}")
print(f"\n  Total articles: {len(list(KB_PATH.glob('*.md')))}")
print(f"\n  Re-index with: python scripts/load_kb.py")