import smtplib
import socket
import logging
from time import time
from email.mime.text import MIMEText
from email.header import Header
from email import Utils

from flask import current_app
from flask.ext.babel import gettext

from openspending.views.helpers import url_for

log = logging.getLogger(__name__)


class MailerException(Exception):
    pass


def add_msg_niceties(recipient_name, body, sender_name):
    return gettext(u"Dear %(name)s,", name=recipient_name) \
        + u"\r\n\r\n%s\r\n\r\n" % body \
        + u"--\r\n%s" % sender_name


def mail_recipient(recipient_name, recipient_email,
                   subject, body, headers=None):
    mail_from = current_app.config.get(
        'MAIL_FROM',
        'noreply@openspending.org')
    body = add_msg_niceties(recipient_name, body,
                            current_app.config.get('SITE_TITLE'))
    msg = MIMEText(body.encode('utf-8'), 'plain', 'utf-8')
    if headers:
        msg.update(headers)
    subject = Header(subject.encode('utf-8'), 'utf-8')
    msg['Subject'] = subject
    msg['From'] = "%s <%s>" % (current_app.config.get('SITE_TITLE'), mail_from)
    recipient = u"%s <%s>" % (recipient_name, recipient_email)
    msg['To'] = Header(recipient, 'utf-8')
    msg['Date'] = Utils.formatdate(time())
    msg['X-Mailer'] = "OpenSpending"
    try:
        server = smtplib.SMTP(current_app.config.get('SMTP_SERVER', 'localhost'), 1025)
        server.sendmail(mail_from, [recipient_email], msg.as_string())
        server.quit()
    except (Exception, socket.gaierror) as e:
        msg = '%r' % e
        log.exception(msg)
        raise MailerException(msg)


def mail_account(recipient, subject, body, headers=None):
    if (recipient.email is None) or not len(recipient.email):
        raise MailerException("No recipient email address available!")
    mail_recipient(recipient.display_name, recipient.email, subject,
                   body, headers=headers)


def get_reset_body(account):
    reset_link = url_for('account.do_reset',
                         email=account.email,
                         token=account.token,
                         _external=True)
    d = {
        'reset_link': reset_link,
        'site_title': current_app.config.get('SITE_TITLE')
    }
    return gettext('''You have requested your password on %(site_title)s to be reset.

Please click the following link to confirm this request:

   %(reset_link)s
''', **d)


def send_reset_link(account):
    body = get_reset_body(account)
    mail_account(account, gettext('Reset your password'), body)
