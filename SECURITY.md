# Security Policy

## Supported Versions

As an alpha game in active development, only the latest release receives security updates.

| Version | Supported          |
| ------- | ------------------ |
| 0.8.x   | :white_check_mark: |
| < 0.8   | :x:                |

## Reporting a Vulnerability

If you discover a security vulnerability in Rogue Signal Protocol, please report it privately:

### 📧 Email
**roguesignalprotocol@gmail.com**

Subject: "SECURITY: [Brief Description]"

### What to Include
- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if you have one)

### Response Timeline
- **Initial Response:** Within 48 hours
- **Status Update:** Within 7 days
- **Fix Timeline:** Varies by severity (critical issues prioritized)

## Security Scope

### In Scope
- **Code execution vulnerabilities** (arbitrary code execution, injection attacks)
- **Data exposure** (unauthorized access to save files, debug data, metrics)
- **Denial of service** (crashes, infinite loops, resource exhaustion)
- **File system vulnerabilities** (path traversal, arbitrary file write/read)

### Out of Scope
- **Gameplay exploits** (unless they enable code execution)
- **Save file manipulation** (players can edit their own saves)
- **Social engineering** (Discord phishing, impersonation)
- **Third-party dependencies** (report these upstream)

## Security Best Practices

### For Players
- Download only from official sources:
  - [Itch.io](https://dragynrain.itch.io/rogue-signal-protocol)
  - [GitHub Releases](https://github.com/Dragynrain/RogueSignalProtocol/releases)
- Verify file checksums if provided
- Keep game updated to latest version

### For Contributors
- Never commit secrets (API keys, passwords, tokens)
- Sanitize user input (save files, JSON configs)
- Validate file paths before file operations
- Use Python's built-in security features
- Run tests before submitting PRs

## Known Security Considerations

### Save File Validation
Save files are JSON and not cryptographically signed. Players can edit their own saves. This is intentional for modding/testing but means:
- Don't trust save file data blindly
- Validate bounds before array access
- Sanitize position coordinates

### Debug Mode
Alpha builds include debug logging (`debug_mode.flag`). This logs gameplay data to `logs/game_debug.log`. This is intentional for bug reporting but:
- Logs contain gameplay data (positions, stats, actions)
- Logs are stored locally only
- Don't include sensitive personal data

### Windows SmartScreen
Unsigned executables trigger Windows SmartScreen warnings. This is expected for indie games without code signing certificates ($300-800/year). The executable is built via GitHub Actions from public source code.

## Disclosure Policy

- **Private Disclosure:** Report vulnerabilities privately first
- **Coordinated Disclosure:** We'll work with you on timing
- **Public Disclosure:** After fix is released, we'll credit you (if desired)

## Credits

Security researchers who responsibly disclose vulnerabilities will be credited in:
- CHANGELOG.md
- GitHub release notes
- This SECURITY.md file (if desired)

---

**Thank you for helping keep Rogue Signal Protocol secure!**
