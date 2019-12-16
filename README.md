# imap-notify

Hack to use imap's `NOTIFY` extension as an efficient
mechanism to update emails via PUSH.

```bash
while true; do 
  python imap-notify.py
  # or offlineimap/isync
  emacsclient --no-wait --eval '(mu4e-update-mail-and-index t)'
done
```
