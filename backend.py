import imaplib
import re

from django.conf import settings
from django.contrib.auth import get_user_model

User = get_user_model()
EMAIL_ADDR_FORMAT = re.compile('^([^@]+)@([^@]+)$')

class IMAPBackend(object):
    def authenticate(self, username=None, password=None):
        login_valid = False

        if (username is None) or (password is None):
            return None

        (user_id, domain) = self._parse_email_addr(username)

        if domain in settings.AUTH_IMAP_SERVER_CONFIG:
            uri = settings.AUTH_IMAP_SERVER_CONFIG[domain]['URI']
            if settings.AUTH_IMAP_SERVER_CONFIG[domain]['USE_SSL']:
                _connect = imaplib.IMAP4_SSL
            else:
                _connect = imaplib.IMAP4
        else:
            return None

        try:
            imap_instance = _connect(uri)
        except imaplib.IMAP4.error as e:
            print e
            return None

        try:
            imap_instance.login(user_id, password)
            if imap_instance.state is 'AUTH':
                login_valid = True
        except imaplib.IMAP4.error as e:
            login_valid = False
            print e
        else:
            imap_instance.logout()

        if login_valid:
            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                user = User(username=username, password=None)
                user.set_unusable_password()
                user.save()
            return user

        return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None

    def _parse_email_addr(self, email_addr):
        match = EMAIL_ADDR_FORMAT.match(email_addr)
        if match:
            return (match.group(1), match.group(2))
        else:
            return (None, None)
