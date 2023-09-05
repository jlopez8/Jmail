# gmailer main.py

import argparse
import datetime as dt

import yaml

import requests
import smtplib
import ssl
import mimetypes
from email.message import EmailMessage


import pandas as pd


def parse_args():
    parser = argparse.ArgumentParser(
        prog="Jmail",
        description="Super-charged Gmail.",
        epilog="Thank you for using Jmail.",
        fromfile_prefix_chars="@",
    )
    parser.add_argument(
        "-cfg", "--config_path", type=str,
        help="Configuration path."
    )
    parser.add_argument(
        "-s", "--sender", type=str,
        help="Email sender."
    )
    parser.add_argument(
        "--to", type=str,
        nargs="+",
        help="Email recipients."
    )
    parser.add_argument(
        "-sub", "--subject", type=str,
        help="Email subject."
    )
    parser.add_argument(
        "-b", "--body", type=str,
        help="Email body."
    )
    parser.add_argument(
        "-bp", "--body_path", type=str,
        help="Path to prepared email body. Recommend HTML."
    )
    parser.add_argument(
        "-bfg", "--body_cfg_path", type=str,
        help="Path to config path for email body YAML."
    )
    parser.add_argument(
        "-a", "--attachment_path", type=str,
        nargs='*',
        help="Path(s) to 0 or more attachment(s)."
    )

    args = parser.parse_args()
        
    return args


def parse_config(config: dict):
    """
    Parse the configuration yaml.

    Parameters
    -------
    config (dict{any}): Dictionary of congiruations.

    Returns
    -------
    credentials (dict(any)): Dictionary of credentials.
    """
    credentials = config["credentials"]
    ...
    return credentials


def get_csv_as_list(filepath: str) -> list:
    """
    Get list using a path to a csv.

    Parameters
    -------
    filepath (str): filepath. 

    Returns
    -------
    ([str]): List of values.
    
    """
    import pandas as pd
    recipients = pd.read_csv(recipients_csv_path, header=None)
    return recipients[0].values.tolist()


class Clearbit():
    """A class for working with Clearbit API."""
    def get_name(response: requests.models.Response) -> (str, str):
        """
        Parse response for HTTP request.

        Parameters
        -------
        response (requests.models.Response): Http response with person data.

        Returns
        -------
        name (str, str): Tuple of first and last name. 
        """
        if not isinstance(y, requests.models.Response):
            print("Not a request.")
            return 
        name = (None, None)
        data = response.json()
        person = data["person"]
        first_name = person["name"]["givenName"]
        last_name = person["name"]["familyName"]
        name = (first_name, last_name)
        return name


    def get_names_from_email_list(recipients_list:[str], username=None, password=None, api_key=None):
        """
        Given a list of recipients, use Clearbit to retreive their names. Other data may be retreieved but at a later stage. 
        The username is the api_key from Clearbit. Read their docs for more info.

        Parameters
        -------
        username (str): Optional. Username.
        password (str): Optional. Password.
        api_key (str): API key.

        Returns
        -------
        names {}: Dict of emails to names.
        """
        names = {}
        # NOTE: may want to batch this in the future or too many requests will be attempted too quickly.
        for email in recipients_list:
            url = f"https://person.clearbit.com/v2/combined/find?email=:{email}"
            clearbit_response = get_response(url, username=clearbit_api_key, password=None, api_key=None)
            names[email] = get_name(clearbit_response)
        return names


def get_response(url: str, username=None, password=None, api_key=None):
    """
    Get a response from API using HTTP.

    Parameters
    -------
    url (str): Url for API request.
    username (str): Optional. Username.
    password (str): Optional. Password.
    api_key (str): API key.

    Returns
    -------
    api_response (requests.models.Response): Response.
    """
    api_response = None
    api_response = requests.get(url, auth=(username, password))
    return api_response


def send_mail(sender: str, recipients: list, subject:str, body: str, password: str, attachment_path=None):
    """
    Send an email via SMTP.

    Parameters
    -------
    sender (str): Sender as a string.
    recipients ([str]): List of recipients. 
    subject (str): Email subject line.
    body (str): Email body as string.
    password (str): Gmail password as string.
    attachment_path (str): Optional. Filepath to attachment. 
    
    Returns
    -------
    None
    """
    def add_attachment(email: EmailMessage, filepath: str) -> EmailMessage:
        """
        Given original email message. May or may not include an attachment already.

        Parameters:
        -------
        email (EmailMessage): EmailMessage.
        filepath (str): Filepath to attachment.

        Returns
        -------
        email (EmailMessage): Mail message with new attachment.
        """
        # Attachments
        with open(filepath, "rb") as fp:
            data = fp.read()

        # guess encoding
        ctype, encoding = mimetypes.guess_type(filepath)
        if ctype is None or encoding is not None:
            # No guess could be made, or the file is encoded (compressed), so
            # use a generic bag-of-bits type.
            ctype = "application/octet-stream"
        maintype, subtype = ctype.split("/", 1)

        email.add_attachment(data, maintype=maintype, subtype=subtype)
        print(f"Successfully attached: {filepath}")
        return email


    email = EmailMessage()
    email["Sender"] = sender
    email["Recipients"] = ", ".join(recipients)
    email["Subject"] = subject
    email.set_content(body)
    if attachment_path != None:
        email = add_attachment(email, attachment_path)

    # Email failsafe.
    confirm_send = input(f"Are you sure you want to send to recipients? (Y/N) \n\n {recipients}\n")

    if confirm_send.lower() == "y":
        context = ssl.create_default_context()
        print("Sending email...")
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp_server:
            smtp_server.login(sender, password)
            smtp_server.sendmail(sender, recipients, email.as_string())
        print("Message sent!")
    else:
        print("Message NOT sent!")
    return email


def jmailer():
    """Jmailer method."""

    inputs = parse_args()

    config_path = inputs.config_path
    sender = inputs.sender
    recipients = inputs.to
    subject = inputs.subject

    body = inputs.body
    body_path = inputs.body_path
    body_config_path = inputs.body_cfg_path

    attachment_path = inputs.attachment_path

    # write something here about a handling possible 
    # double-checking of receiving multiple unecessary args.
    


    print("Parsed args.")


if __name__ == "__main__":
    jmailer()
    print("ran gmailer")

