# Local Data and Upload Checklist

- Check extension, declared MIME, size, non-empty content, and decoded image format before processing.
- Generate server-side safe filenames; never use a raw user filename in a path.
- Show specific friendly errors without stack traces or internal paths.
- Protect history read-modify-write with a lock and same-directory temporary file plus `os.replace`.
- Keep only the original and processed images required to reopen each saved result. Retain them with history until the local user manually clears the history and paired image files; do not send them off-device.
- Store no credentials, secrets, or unnecessary personal data in history.
