def da_carattere_speciale_ad_entity(input_string):
    # https://corsidia.com/materia/web-design/caratterispecialihtml
    transformation_map = {
        "°": "&deg;", "«": "&laquo", "»": "&raquo;", "–": "&ndash;", "—": "&mdash;",
        "¡": "&iexcl;", "¿": "&iquest;", '\"': '&quot;', "“": "&rdquo;", "‘": "&lsquo;",
        "’": "&rsquo;", " ": "&nbsp;", '&': '&amp;', '>': '&gt;', '<': '&lt;',
        "¢": "&cent;", "©": "&copy;", "÷": "&divide;", "µ": "&micro;", "·": "&middot;", "¶": "&para;",
        "±": "&plusmn;", "€": "&euro;", "£": "&pound;", "®": "&reg;", "§": "&sect;", "™": "&trade;",
        "¥": "&yen;", "Á": "&Aacute;", "à": "&agrave;", "À": "&Agrave;", "â": "&acirc;", "Â": "&Acirc;",
        "å": "&aring;", "Å": "&Aring;", "ã": "&atilde;", "Ã": "&Atilde;", "ä": "&auml;",
        "Ä": "&Auml;", "æ": "&aelig;", "Æ": "&AElig;", "ç": "&ccedil;", "Ç": "&Ccedil;", "é": "&eacute;",
        "á": "&aacute;", "É": "&Eacute;", "è": "&egrave;", "È": "&Egrave;", "ê": "&ecirc;",
        "Ê": "&Ecirc;", "ë": "&euml;", "Ë": "&Euml;", "í": "&iacute;", "Í": "&Iacute;", "ì": "&igrave;",
        "Ì": "&Igrave;", "î": "&icirc;", "Î": "&Icirc;", "ï": "&iuml;", "Ï": "&Iuml;",
        "ñ": "&ntilde;", "Ñ": "&Ntilde;", "ó": "&oacute;", "Ó": "&Oacute;", "ò": "&ograve;", "Ò": "&Ograve;",
        "ô": "&ocirc;", "Ô": "&Ocirc;", "ø": "&oslash;","Ø": "&Oslash;", "õ": "&otilde;",
        "Õ": "&Otilde;","ö": "&ouml;", "Ö": "&Ouml;", "ú": "&uacute;","Ú": "&Uacute;", "ù": "&ugrave;", "Ù": "&Ugrave;",
        "û": "&ucirc;", "Û": "&Ucirc;", "ü": "&uuml;", "Ü": "&Uuml;", "ß": "&szlig;", "ÿ": "&yuml;",
        "→": "&#8594;", "←": "&#8592;", "↑": "&#8593;", "↓": "&#8595;", "↔": "&#8596;", "↕": "&#8597;",
        "♥": "&hearts;",
    }

    transformation_table = str.maketrans(transformation_map)

    return input_string.translate(transformation_table)


def emailsender(subject, body, listTO, listCC, listBCC):
    # listTO = ['luca.calabro@unimib.it']
    # listCC = []
    # listBCC = []
    # documentazione consultata
    # https://stackoverflow.com/questions/1546367/python-how-to-send-mail-with-to-cc-and-bcc
    # https://docs.python.org/3/library/email.examples.html
    import smtplib
    EMAIL_SENDER_USERNAME = 'serviziwebsi@unimib.it'
    EMAIL_SENDER_PASSWORD = '?sciliam*15'

    # Import the email modules we'll need
    from email.message import EmailMessage

    msg = EmailMessage()
    msg.add_header('Content-Type', 'text/html')

    email_content = f"<html><head></head><body>{body}</body></html>"
    msg.set_payload(email_content)
    # msg.set_content(email_content)

    msg['Subject'] = subject
    #    msg['From'] = "serviziwebsi@unimib.it"
    msg['From'] = "noreplay@unimib.it"
    msg['To'] = ', '.join(listTO)
    msg['Cc'] = ', '.join(listCC)
    msg['Bcc'] = ', '.join(listBCC)

    # Send the message via our own SMTP server.
    s = smtplib.SMTP('smtp.gmail.com: 587')
    s.ehlo()  # protocollo per extended SMTP
    s.starttls()
    s.login(EMAIL_SENDER_USERNAME, EMAIL_SENDER_PASSWORD)
    s.send_message(msg)
    s.quit()


import base64  # for base64.urlsafe_b64decode
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from httplib2 import Http
from oauth2client import client, file, tools
from oauth2client.clientsecrets import InvalidClientSecretsError

import requests


class Gmail(object):
    """
    The Gmail class which serves as the entrypoint for the Gmail service API.
    Args:
        client_secret_file (str): Optional. The name of the user's client
            secret file. Default 'client_secret.json'.
    Attributes:
        service (googleapiclient.discovery.Resource): The Gmail service object.
    """

    # Allow Gmail to read and write emails, and access settings like aliases.
    SCOPES = [
        'https://www.googleapis.com/auth/gmail.modify',
        'https://www.googleapis.com/auth/gmail.settings.basic'
    ]

    # If you don't have a client secret file, follow the instructions at:
    # https://developers.google.com/gmail/api/quickstart/python
    # Make sure the client secret file is in the root directory of your app.
    # CLIENT_SECRETS_FILE = 'client_secret.json'
    CREDENTIALS_FILE = 'gmail-token.json'

    def __init__(self, client_secret_file='client_secret.json'):
        self.client_secret_file = client_secret_file
        try:
            # The file gmail-token.json stores the user's access and refresh
            # tokens, and is created automatically when the authorization flow
            # completes for the first time.
            store = file.Storage(self.CREDENTIALS_FILE)
            creds = store.get()

            if not creds or creds.invalid:
                # Will ask you to authenticate an account in your browser.
                flow = client.flow_from_clientsecrets(self.client_secret_file, self.SCOPES)
                creds = tools.run_flow(flow, store)

            self.service = build('gmail', 'v1', http=creds.authorize(Http()), cache_discovery=False)

        except InvalidClientSecretsError:
            raise FileNotFoundError(
                "Your 'client_secrets.json' file is nonexistent. Make sure "
                "the file is in the root directory of your application. If "
                "you don't have a client secrets file, go to https://"
                "developers.google.com/gmail/api/quickstart/python, and "
                "follow the instructions listed there."
            )

    def _create_message(self, sender, to, subject, message, cc=None, bcc=None):
        """
        Creates the raw email message to be sent.
        Args:
            sender (str): The email address the message is being sent from.
            to (str): The email address the message is being sent to.
            cc (List[str]): The list of email addresses to be Cc'd.
            bcc (List[str]): The list of email addresses to be Bcc'd
            subject (str): The subject line of the email.
            message (str): The HTML message of the email.

        Returns:
            The message dict.
        """

        msg = MIMEMultipart('alternative')
        msg['To'] = to
        msg['From'] = sender
        msg['Subject'] = subject

        if cc:
            msg['Cc'] = ', '.join(cc)

        if bcc:
            msg['Bcc'] = ', '.join(bcc)

        attach_html = msg
        attach_html.attach(MIMEText(message, 'html'))

        return {
            'raw': base64.urlsafe_b64encode(msg.as_string().encode()).decode()
        }

    def send_message(self, sender, to, subject, message, cc=None, bcc=None, user_id='me'):
        """
        Sends an email.
        Args:
            sender (str): The email address the message is being sent from.
            to (str): The email address the message is being sent to.
            subject (str): The subject line of the email. Default ''.
            msg_html (str): The HTML message of the email. Default None.
            msg_plain (str): The plain text alternate message of the email (for
                slow or old browsers). Default None.
            cc (List[str]): The list of email addresses to be Cc'd. Default
                None.
            bcc (List[str]): The list of email addresses to be Bcc'd.
                Default None.
            user_id (str): Optional. The address of the sending account.
                Default 'me'.
        Returns:
            (dict) The dict response of the message if successful.
            (str) "Error" if unsuccessful.
        """

        body = self._create_message(sender=sender, to=to, subject=subject, message=message, cc=cc, bcc=bcc)

        try:
            request = self.service.users().messages().send(userId=user_id, body=body)
            message_reference = request.execute()
            return message_reference

        except HttpError as error:
            print(f"An error has occurred: {error}")
            return "Error"


# def main_mail():
#     gmail = Gmail()
#     message = gmail.send_message(sender="noreply@unimib.it", to="luca.calabro@unimib.it",
#                                  subject='test subject', message="<p>testo HTML test</p>")
#     print(message)
#     return
#
#
# if __name__ == '__main__':
#     main_mail()
