# Author: Dr. Jaime Alexis Lopez-Merizalde
# jmailer main.py

import os 
import argparse
import shlex

import yaml

import smtplib
import ssl
import mimetypes
from email.message import EmailMessage
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart

import tempfile
import webbrowser

from Tools.tools import text_builder
from Tools.tools import get_records


def parse_args():
    def convert_arg_line_to_args(arg_line):
        """
        Custom-defined method input of a file with multiple arguments to be input as coherent arguments to
        argparser.

        Parameters
        -------
        arg_line (str): The entire line in a text file to be converted to arguments.
        
        Returns
        -------
        (?): Yields args which is uitlized by argsparse.ArgumentParser object.
        """

        for arg in shlex.split(arg_line):
            if not arg.strip():
                continue
            yield arg

    parser = argparse.ArgumentParser(
        prog="Jmail",
        description="A super-charged Gmail accessor.",
        epilog="Thank you for using Jmail.",
        fromfile_prefix_chars="@",
    )

    # Apply the defined arg line parser.
    parser.convert_arg_line_to_args = convert_arg_line_to_args

    # See documentation for arg definitions.
    parser.add_argument(
        "-c", "--config_path", type=str,
        help="""
        Path to configuration `.yaml` file. 
        Hosts key information like app word and other 
        sensitive information required to access sensitive 
        resources. This file is located in the top-level 
        directorywhere Jmail is installed.
        """
    )
    parser.add_argument(
        "-s", "--sender", type=str,
        help="Email address of sender."
    )
    parser.add_argument(
        "-to", "--recipients", type=str,
        nargs="*",
        help="""
        Comma-separated emails of recipients. 
        Single-recipients do not need a comma.
        """
    )
    parser.add_argument(
        "-sub", "--subject", type=str,
        help="Email subject."
    )
    parser.add_argument(
        "-b", "--body", type=str,
        default="",
        help="Email body as string."
    )
    parser.add_argument(
        "-bp", "--body_path", type=str,
        help="Path to body text or html-formatted file. If body path provided, it will overwrite body provided."
    )
    parser.add_argument(
        "-a", "--attachments_path", type=str,
        nargs='*',
        help="Path(s) to 0 or more attachment(s)."
    )
    parser.add_argument(
        "-cp", "--callsheet_path", type=str,
        help="Path to a callsheet of recipients to be emailed. Overrides recipients provided via the CLI or the runme file."
    )
    parser.add_argument(
        "-r", "--runme", type=str,
        help="""
        Path of runme file with arguments. If specified, this will 
        override any arguments provided on the CLI.
        """
    )
    args = parser.parse_args()
    return args


def body_from_path(
        body_path: str,
        text_vars=None,
) -> str:
    """
    Build a body text using a body path. The body path points to a plain text or HTML-formatted message.
    When building a body, variables can be provided as a dictionary to parameterize the given body text.

    Parameters
    -------
    body_path (str): Path to body file as a plain text or HTML-formatted file.
    text_vars (dict): Dictionary of variables. Optional.

    Returns
    -------
    body (str): Message body formatted as string. 
    """
    with open(body_path, "r+") as f:
        body = f.read() 
    f.close()
    body = text_builder(body, text_vars)
    return body


def build_message(
        sender: str, recipient: list, subject: str, 
        body: str, attachments_path=None
    ) -> EmailMessage:
    """
    Build an email message using the relevant email parameters defined in arguments. 

    Parameters
    -------
    sender (str): Sender as a string.
    recipient (str): Recipient. 
    subject (str): Optional. Email subject line.
    body (str): Body of message.
    attachments_path ([str]): Optional. List of filepath to attachments.

    Returns
    -------
    msg (EmailMessage): EmailMessage object defined with prescribed arguments.
    """
    msg = EmailMessage()
    msg["Subject"] = subject 
    msg["From"] = sender
    msg["To"] = recipient
    # body
    msg.set_content(body, subtype="html")

    # attachments
    if attachments_path:
        for attachment in attachments_path:
            with open(attachment, "rb") as fp:
                data = fp.read()
            # guess encoding
            ctype, enconding = mimetypes.guess_type(attachment)
            if ctype is None or enconding is not None:
                ctype = "application/octet-stream"
            maintype, subtype = ctype.split("/", 1)
            msg.add_attachment(data, maintype=maintype, subtype=subtype)

    return msg


def preview_message(msg: EmailMessage) -> str:
    """
    Allows preview message with a browser. Uses tempfile file management to create a 
    tempfile for explicit deletion.

    Parameters
    -------
    msg (EmailMessage): EmailMessage object.

    Returns
    -------
    f.name (str): Filepath temporary for message previewer.
    """
    body = ''.join(msg.get_body(preferencelist=('plain', 'html')).get_content().splitlines(keepends=True))
    with tempfile.NamedTemporaryFile("w", delete=False, suffix=".html") as f:
        url = "file://" + f.name
        f.write(body)
    webbrowser.open_new_tab(url)
    return f.name


def parse_runme(runme: dict) -> dict:
    """Parses a runme file into it's individual usable components.

    Parameters
    -------
    runme (dict): Filepath for runme file provided.

    Returns
    -------
    config_path (str): Path to configuration `.yaml` file.
    sender (str): Email address of sender. 
    recipients (list): List of recipients. If single recipient, this is a list of one string.
    subject (str): Email subject.
    body (str): Email body.
    attachments_path (str): Path to attachment to be included in email.
    callsheet_path (str): Path to callsheet with dictionary of contacts.
    """
    args = runme["arguments"]
    config_path = args.get("config_path", None)
    sender = args.get("sender", None)
    recipients = args.get("recipients", None)
    subject = args.get("subject", None)
    body = args.get("body", None)
    body_path = args.get("body_path", None)
    attachments_path = args.get("attachments_path", None)
    callsheet_path = args.get("callsheet_path", None)
    return config_path, sender, recipients, subject, body, body_path, attachments_path, callsheet_path


def jmailer():
    """Jmailer method."""

    print("Input args flow...")
    inputs = parse_args()
    config_path = inputs.config_path
    sender = inputs.sender
    recipients = inputs.recipients
    subject = inputs.subject
    body = inputs.body
    body_path = inputs.body_path
    attachments_path = inputs.attachments_path
    callsheet_path: inputs.callsheet
    runme_path = inputs.runme
    print("Input args flow complete.")

    if runme_path:
        print("Loading runme file flow...")
        print("Warning: runme arguments override CLI arguments.")
        runme = yaml.safe_load(open(runme_path))
        config_path, sender, recipients, subject, body, body_path, attachments_path, callsheet_path = parse_runme(runme)
        print("Loading runme file flow complete.")

    print("Loading credentials flow...")
    config = yaml.safe_load(open(config_path))
    credentials = config["credentials"]
    print("Loading credentials flow complete.")

    print("Connecting to SMTP Gmail flow...")
    context = ssl.create_default_context()
    smtp_connection = smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) 
    smtp_connection.login(sender, credentials["gmail"]["app_password"])
    print("Connecting to SMTP Gmail flow complete.")

    # Decide with build_body method to use.
    if body_path is None:
        build_body = lambda : body
    else:
        build_body = lambda text_vars: body_from_path(body_path, text_vars=text_vars)
    
    if callsheet_path:
        print("Callsheet path provided. Retrieving callsheet...")
        callsheet = get_records(callsheet_path, credentials_path=credentials["app"]["gsheets_secrets_path"])
        print("Retrieving callsheet complete.")

    print("Message preview flow...")
    confirm_preview = input(f"Do you want to preview the first message? (y - to confirm)")
    if confirm_preview == "y":
        if callsheet_path:
            body = build_body(callsheet[0])
            msg = build_message(sender, callsheet[0]["EMAIL"], subject, body, attachments_path)
        else:
            body = build_body(text_vars=None)
            msg = build_message(sender, recipients[0], subject, body, attachments_path)
        temp_filepath = preview_message(msg)
    else:
        temp_filepath = None
    print("Message preview flow complete.")

    print("Message send flow...")
    confirm_send = input(f"Are you sure you want to send emails to: \n {recipients}? (y - to confirm)")
    if confirm_send=="y":
        for recipient in recipients:
            if body_path:
                text_vars = None
                body = build_body(body_path, text_vars=text_vars)
            msg = build_message(sender, recipient, subject, body, attachments_path)
            smtp_connection.send_message(msg, from_addr=sender, to_addrs=recipient)
        print("Message sent!")
    else: 
        print("Message not sent!")
    print("Message send flow complete.")

    # print("Cleanup flow...")
    # if temp_filepath:
    #     os.remove(temp_filepath)
    # print("Cleanup flow complete.")


if __name__=="__main__":

    jmailer()
