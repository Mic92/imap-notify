imap-notify
===========

Hack to use imap’s ``NOTIFY`` extension as an efficient mechanism to update
emails via PUSH. Most IMAP PUSH implementation rely on the ``IDLE`` extension
to check for changes in a mailbox.

However using it requires maintaining one TCP connection per IMAP folder. This
is not only inefficient and complex but also some IMAP servers limit the number
of connections per client. This project instead relies on a newer IMAP extension
called ``NOTIFY``, which can watch on all global changes with a single command.
It requires support in the IMAP server as well. Dovecot provides this feature since
xxxx.

Installation
============

This project has no dependencies except for python itself::

   $ pip install "git+https://github.com/Mic92/imap-notify"

Configuration
=============

Unless imap-notify receives the configuration file as a first argument it will
look it up in ``~/.config/imap-notify/imap-notify.ini`` assuming that
``$XDG_CONFIG_HOME`` is unset or equals to ``~/.config``.
To get started copy and modify the ``imap-notify.ini`` template from this
repository to that path.

usage::

   while true; do 
     python imap-notify.py
     # or offlineimap/isync
     emacsclient --no-wait --eval '(mu4e-update-mail-and-index t)'
   done
