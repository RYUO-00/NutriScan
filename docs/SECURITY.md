# Local Data and Upload Checklist

## Optional LAN access

- The default `python app.py` binding is `127.0.0.1:5000`. `python app.py --lan` opts in to `0.0.0.0:5000` and prints a warning because other devices on the network may access this single-user prototype and its local scan results.
- Use LAN mode only on a trusted private network. The app has no authentication; do not expose it to the public internet, configure router port forwarding, or use tunnels or cloud hosting.
- Debug mode and the interactive debugger stay disabled in both modes. Python does not change Windows Firewall settings. If needed, README.md documents a manual inbound TCP 5000 rule limited to the Private profile and its removal command. Remove that rule when LAN access is no longer required.
- Keep both devices on the trusted Wi-Fi network and stop the Flask process when access is no longer needed.

- Check extension, declared MIME, size, non-empty content, and decoded image format before processing.
- Generate server-side safe filenames; never use a raw user filename in a path.
- Show specific friendly errors without stack traces or internal paths.
- Protect history read-modify-write with a lock and same-directory temporary file plus `os.replace`.
- Keep only the original and processed images required to reopen each saved result. Retain them with history until the local user manually clears the history and paired image files; do not send them off-device.
- Store no credentials, secrets, or unnecessary personal data in history.
