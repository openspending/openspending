import smtplib
import logging
import uuid
from time import time
from email.mime.text import MIMEText
from email.header import Header
from email import Utils
from urlparse import urljoin

from pylons.i18n.translation import _
from pylons import config, app_globals
from openspending.ui.lib import helpers as h

log = logging.getLogger(__name__)

class MailerException(Exception):
    pass

def add_msg_niceties(recipient_name, body, sender_name):
    return _(u"Dear %s,") % recipient_name \
           + u"\r\n\r\n%s\r\n\r\n" % body \
           + u"--\r\n%s" % sender_name

def mail_recipient(recipient_name, recipient_email,
        subject, body, headers={}):
    mail_from = config.get('openspending.mail_from', 'noreply@openspending.org')
    body = add_msg_niceties(recipient_name, body, app_globals.site_title)
    msg = MIMEText(body.encode('utf-8'), 'plain', 'utf-8')
    for k, v in headers.items(): msg[k] = v
    subject = Header(subject.encode('utf-8'), 'utf-8')
    msg['Subject'] = subject
    msg['From'] = _("%s <%s>") % (app_globals.site_title, mail_from)
    recipient = u"%s <%s>" % (recipient_name, recipient_email)
    msg['To'] = Header(recipient, 'utf-8')
    msg['Date'] = Utils.formatdate(time())
    msg['X-Mailer'] = "OpenSpending"
    try:
        server = smtplib.SMTP(config.get('smtp_server', 'localhost'))
        server.sendmail(mail_from, [recipient_email], msg.as_string())
        server.quit()
    except Exception, e:
        msg = '%r' % e
        log.exception(msg)
        raise MailerException(msg)

def mail_account(recipient, subject, body, headers={}):
    if (recipient.email is None) or not len(recipient.email):
        raise MailerException(_("No recipient email address available!"))
    mail_recipient(recipient.display_name, recipient.email, subject,
            body, headers=headers)


RESET_LINK_MESSAGE = _(
'''You have requested your password on %(site_title)s to be reset.

Please click the following link to confirm this request:

   %(reset_link)s
''')

def get_reset_body(account):
    reset_link = h.url_for(controller='account',
                           action='do_reset',
                           email=account.email,
                           token=account.token,
                           qualified=True)
    d = {
        'reset_link': reset_link,
        'site_title': app_globals.site_title
        }
    return RESET_LINK_MESSAGE % d

def send_reset_link(account):
    body = get_reset_body(account)
    mail_account(account, _('Reset your password'), body)


