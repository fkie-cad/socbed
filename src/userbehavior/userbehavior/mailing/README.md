# Mailing package

## mailing.py

class **Mailing**: Controls a mailing routine based on a *UserProfile*. Uses *Mailer* object to communicate with IMAP and SMTP servers.

## mailer.py

class **Mailer**: Interface to IMAP and SMTP servers. Uses *imaplib* and *smtplib*.

## exceptions.py

class **MailingException**: Basic Exception for this package.

## helpers.py

Implements useful functions for working with mails.
