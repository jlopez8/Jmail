# gmailer main.py

import argparse
import datetime as dt
import regex as re

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
        "-tp", "--to_path", type=str,
        help="Path to a receipients file (csv)."
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
        "-a", "--attachments_path", type=str,
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
    filepath (str): Filepath to csv. 

    Returns
    -------
    ([str]): List of values.
    
    """
    recipients = pd.read_csv(filepath, header=None)
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
            clearbit_response = get_response(url, username=username, password=password, api_key=api_key)
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


def build_text(text_path: str, text_vars=None) -> str:
    """
    Using passed-along dictionary of variable names to values, fill in the 
    text file located at text_path. May be passed on no variables to fill, in which case the text body is returned as-is.
    Ignores case (case-insensitive). 

    Parameters
    -------
    text_path (str): Path to text file.
    text_vars (dict): Dictionary of variables. Optional

    Returns
    -------
    query (str): Filled-in text body by value using the text_vars dictionary.
    """

    DEFAULT_FILL_IN = ""

    # Get the text.
    with open(text_path, "r+") as f:
        text = f.read() 
    f.close()
    if text_vars == None:
        return text

    # Extract variables from the text.
    variables_in_text = re.findall("\{(.*?)\}", text, flags=re.IGNORECASE)

    # do a replacement: each time call local_vars...
    for var in variables_in_text:
        replace_me = "\{" + var + "\}"
        replace_with = str(text_vars.get(var,DEFAULT_FILL_IN))
        text = re.sub(replace_me, replace_with, text)
    return text


def send_mail(
        sender: str, recipients: list, subject:str, 
        password: str,
        attachments=None,
        body=None, body_path=None, body_config=None
    ):
    """
    Send an email via SMTP. Recommended body is provided as HTML formatted text. Provide body or body_path and body_config but not both. 

    Parameters
    -------
    sender (str): Sender as a string.
    recipients ([str]): List of recipients. 
    subject (str): Email subject line.
    password (str): Gmail password as string.
    attachments ([str]): Optional. List of filepath(s) to attachment(s).
    body (str): Optional. Optional. Email body as string.
    body_path (str): Optional. Email body path to be parsed using the body config. Recommended to use HTML formatting.
    body_config (str): Optional. Email config for the body including variables that can be quickly parsed and replaced.
    
    Returns
    -------
    None
    """

    email = EmailMessage()
    email["Sender"] = sender
    email["Recipients"] = ", ".join(recipients)
    email["Subject"] = subject
    email.set_content(body)

    if attachments != None:
        for attachment_path in attachments:
            email = add_attachment(email, attachment_path)

    # Email failsafe.
    confirm_send = input(f"Are you sure you want to send to recipients? (Y/N) \n\n {recipients}\n")

    if confirm_send.lower() == "y":

        context = ssl.create_default_context()
        print("Sending email...")
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp_server:
            smtp_server.login(sender, password)

            # dev-NOTE: this is hacky. Definitely clean up the set_content and sendmail method here and 
            # break it out of this portion into 3 stages: That way you "set/configure an email", "login", 
            # "apply the body or bodies"
            
            if body != None:
                email.set_content(body)
                smtp_server.sendmail(sender, recipient, email.as_string())
            elif body_path != None or body_config != None:
                for recipient in recipients:
                    # Value 0 indicates first name, 1 is last name.
                    body_config["addressee"] = names_from_emails[to][0]
                    body = build_text(body_path, body_config)
                    email.set_content(body, subtype="html")
                    smtp_server.sendmail(sender, recipient, email.as_string())

        print("Message sent!")
    else:
        print("Message NOT sent!")
    return email


def jmailer():
    """Jmailer method."""

    inputs = parse_args()

    config_path = inputs.config_path
    sender = inputs.sender
    # recipients = inputs.to
    recipients_path = inputs.to_path
    subject = inputs.subject

    body = inputs.body
    body_path = inputs.body_path
    body_cfg_path = inputs.body_cfg_path
    if body != None and (body_path != None or body_cfg_path != None):
        print("Provide body or body_path and body_cfg_path but not both.")
        return
    
    attachments = inputs.attachments_path
    print("Parsed args flow complete.")

    config = yaml.safe_load(open(config_path))
    credentials = parse_config(config)
    print("Loaded credentials flow complete..")

    recipients = get_csv_as_list(recipients_path)

    password = credentials["gmail"]["app_password"]
    email = send_mail(
        sender, recipients, subject, password, 
        attachments=attachments,
        body_path=body_path, body_config=body_cfg_path

    )    
    print("Email send flow complete.")

    # write something here about a handling possible 
    # double-checking of receiving multiple unecessary args.



if __name__ == "__main__":
    jmailer()
    print("ran gmailer")

