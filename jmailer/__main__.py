# Author: Dr. Jaime Alexis Lopez-Merizalde
# jmailer main.py

import os
import argparse
import shlex
import datetime as dt
import regex as re

import yaml

import requests
import smtplib
import ssl
import mimetypes
from email.message import EmailMessage

import webbrowser

import pandas as pd

import db_handler
from phonebooks import Clearbit as cb
from phonebooks import PeopleDataLabs as pdl
from phonebooks import LocalPhoneBook as lpb
from tools import Timers, text_builder


def parse_args():

    def convert_arg_line_to_args(arg_line):
        for arg in shlex.split(arg_line):
            if not arg.strip():
                continue
            yield arg

    parser = argparse.ArgumentParser(
        prog="Jmail",
        description="A super-charged Gmail access.",
        epilog="Thank you for using Jmail.",
        fromfile_prefix_chars="@",
    )
    
    parser.convert_arg_line_to_args = convert_arg_line_to_args

    parser.add_argument(
        "-cfg", "--config_path", type=str,
        help="Configuration path."
    )
    parser.add_argument(
        "-db", "--db_identifier", type=str,
        help="Database key identifier. Possibly a name."
    )
    parser.add_argument(
        "-dt", "--db_table", type=str,
        help="Database table identifier."
    )
    parser.add_argument(
        "-s", "--sender", type=str,
        help="Email sender."
    )
    parser.add_argument(
        "-to", "--recipients", type=str, action="append",
        nargs="*",
        help="Email recipients."
    )
    parser.add_argument(
        "-rp", "--recipients_path", type=str,
        help="Path to a receipients file (csv)."
    )
    parser.add_argument(
        "-sub", "--subject", type=str,
        help="Email subject."
    )
    parser.add_argument(
        "-b", "--body", type=str,
        help="Email body as string."
    )
    parser.add_argument(
        "-bp", "--body_path", type=str,
        help="Path to prepared email body. Recommend HTML."
    )
    parser.add_argument(
        "-ecp", "--email_config_path", type=str,
        help="Path to config path for email config YAML."
    )
    parser.add_argument(
        "-a", "--attachments_path", type=str,
        nargs='*',
        help="Path(s) to 0 or more attachment(s)."
    )
    parser.add_argument(
        "-cp", "--credentials_path", type=str,
        help="Path to credentials file."
    )
    parser.add_argument(
        "--local_phonebook_path", type=str,
        help="Path to local phonebook csv."
    )
    parser.add_argument(
        "-t", "--test_mode", action="store_true",
        help="If passed then emails sent to sender only."
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


def get_recipients_from_path(filepath: str) -> list:
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

    email.add_attachment(data, maintype=maintype, subtype=subtype, filename=os.path.basename(filepath))
    print(f"Successfully attached: {filepath}")
    return email


def build_bodies(details, body_path, body_config):
    """
    Builds email bodies based off full names and corresponding email addresses.

    Parameters
    -------
    details (dict): Dictionary of person details including first, last names and company name.
    body_path (str): Email body path to be parsed using the body config. Recommended to use HTML formatting.
    body_config (str): Email config for the body including variables that can be quickly parsed and replaced.

    Returns
    -------
    bodies (dict): Dictionary recipient email addresses and formatted body text from script.
    """
    bodies = {}
    for recipient, detail in details.items():
        body_config["addressee"] = detail["first_name"]
        bodies[recipient] = text_builder(body_path, body_config)
    return bodies


def message_previewer(body: str) -> str:
    """
    Allows preview message with a browser.

    Parameters
    -------
    body (str): String with HTML formatted content.

    Returns
    -------
    filepath (str): Filepath temporary for message previewer.
    """
    PREVIEW_FILENAME = "./preview_body.html"
    f = open(PREVIEW_FILENAME, "w")
    f.write(body)
    f.close()

    filepath = os.getcwd() + "/" + PREVIEW_FILENAME
    web_path = "file:///" + filepath
    webbrowser.open_new_tab(web_path)
    return filepath


def send_email(
        sender: str, 
        recipients: list, 
        smpt_connection, 
        subject="", 
        body="", 
        attachments=None, 
        test_mode=True
    ):
    """
    Send an email via SMTP. Recommended body is provided as HTML formatted text.

    Parameters
    -------
    sender (str): Sender as a string.
    recipients ([str]): List of recipients. 
    smpt_connection (smtplib.SMTP_SSL): SMPT SSL connection object.
    subject (str): Optional. Email subject line.
    body (str): Optional. Body of message.
    attachments ([str]): Optional. List of filepath(s) to attachment(s).

    Returns
    -------
    email (EmailMessage): Email that was sent.
    """
    email = EmailMessage()
    email["Sender"] = sender
    email["Recipients"] = " ,".join(recipients)
    email["Subject"] = subject

    email.set_content(body, subtype="html")
    if attachments != None:
        for attachment in attachments:
            email = add_attachment(email, attachment)

    if test_mode:
        print("Sending email in test mode.")
        recipients = [sender]
    
    smpt_connection.sendmail(sender, recipients, email.as_string())
    print("Message sent!")
    return email


def send_emails(
        sender: str, 
        recipients: list, 
        smpt_connection, 
        bodies={}, 
        subject=None, 
        attachments=None, 
        test_mode=True
    ):
    """
    Sends emails with different bodies (can be).
    
    Parameters
    -------
    sender (str): Sender as a string.
    recipients ([str]): List of recipients. 
    smpt_connection (smtplib.SMTP_SSL): SMPT SSL connection object.
    subject (str): Optional. Email subject line.
    bodies ({str}): Optional. Dictionary condtaining bodies of separate messages.
    attachments ([str]): Optional. List of filepath(s) to attachment(s).
    test_mode (bool): Sends to sender-inbox only if true.

    Returns
    -------
    None
    """
    for recipient in recipients:
        body = bodies.get(recipient, "")
        send_email(sender, [recipient], smpt_connection, subject=subject, body=body, attachments=attachments, test_mode=test_mode)
    print("Sent some emails!")


def jmailer():
    """Jmailer method."""

    inputs = parse_args()

    config_path = inputs.config_path
    db_identifier = inputs.db_identifier
    db_table = inputs.db_table
    sender = inputs.sender
    recipients = inputs.recipients
    recipients_path = inputs.recipients_path
    email_config_path = inputs.email_config_path
    subject = inputs.subject
    credentials_path = inputs.credentials_path
    body = inputs.body
    body_path = inputs.body_path
    attachments_path = inputs.attachments_path
    local_phonebook_path = inputs.local_phonebook_path
    test_mode = inputs.test_mode

    if body != None and (body_path != None or email_config_path != None):
        print("Error: Provide body or body_path and email_config_path but not both. Defaulting to body provided.")
        return
    
    if test_mode:
        print(f"Running in test mode. Emails will be sent to {sender}")
    
    print("Parsed args flow complete.")

    config = yaml.safe_load(open(config_path))
    credentials = parse_config(config)
    print("Loaded credentials flow complete.")

    gmail_password = credentials["gmail"]["app_password"]
    print("Get passwords flow complete.")

    if not (recipients_path is None) and (recipients is None):
        recipients = db_handler.DB_handler().get_recipients_from_path(recipients_path)
    Timers().exec_time("Get recipients flow complete.")


    if email_config_path != None:
        email_config = yaml.safe_load(open(email_config_path))
        print("Load email config flow complete.")

    clearbit_api_key = credentials["clearbit"]["api_key"]
    print("Clearbit user flow complete.")

    api_key = credentials["peopledatalab"]["api_key"]
    print("People Data Labs user flow complete.")

    context = ssl.create_default_context()
    smpt_connection = smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) 
    smpt_connection.login(sender, gmail_password)
    print("SMPT connection flow complete.")
 
    msg = "Clearbit connect reached quota. Trying People Data Labs instead."
    Timers().exec_time(msg)
    # NOTE; this should really be a try statement.
    phonebook = lpb()
    # names = cb().get_names_from_email_list(recipients, username=clearbit_api_key)
    # recipient_details = phonebook.get_details_from_email_list(recipients, api_key=api_key)
    recipient_details = phonebook.get_details_from_email_list(recipients, local_phonebook_path)
    print("Recipient details fetching complete.")

    ### Start the Meat of the Message.
    if subject is None:
        subject = email_config["subject"]

    if body != None:
        bodies = dict(zip(recipients, body))
    else:
        bodies = build_bodies(recipient_details, body_path, email_config)
        
    # Warn about emails you've already sent.
    google = db_handler.Google()
    _, gsheets = google.google_connect(credentials_path=credentials_path)
    reduced_recipients, repeated_recipients = db_handler.DB_handler().cross_check_emails(recipients, gsheets, db_identifier, db_table)

    if len(repeated_recipients) != 0: 
        msg = f"Found {str(len(repeated_recipients))} emails already in the database."
        msg += f"\nThey are\n{repeated_recipients}"
        Timers().exec_time(msg)
        confirm_exclusions = input(f"\nDo you want to exclude these recipients? y - to exclude from send?")
        if confirm_exclusions == "y":
            recipients = reduced_recipients

    # Preview Message.
    temp_filepath = message_previewer(bodies[list(bodies.keys())[0]])

    confirm_send = input(f"Are you sure you want to send emails to: \n {recipients}? (y - to confirm)")
    if confirm_send=="y":
        send_emails(sender, recipients, smpt_connection, bodies, subject=subject, attachments=attachments_path, test_mode=test_mode)
    else:
        msg = "Messages not sent!"
        Timers().exec_time(msg)

    # Update Contacts db.
    if confirm_send=="y" and not test_mode:
        try:
            msg = "Updating database."
            Timers().exec_time(msg)

            db_handler.DB_handler().db_contacts_updater(
                credentials_path,
                db_identifier,
                db_table,
                recipient_details,
            )
        except Exception as e:
            msg = "Something went wrong with writing to the db. " + str(e)
            Timers().exec_time(msg)
    else:
        msg = "Database not updated."
        Timers().exec_time(msg)
    
    # Cleanup.
    os.remove(temp_filepath)
    return


if __name__ == "__main__":
    jmailer()
    print("Completed running Jmailer.")
