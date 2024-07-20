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
        "-r", "--runme", type=str,
        help="""
        Path of runme file with arguments. If specified, this will 
        override any arguments provided on the CLI.
        """
    )
    args = parser.parse_args()
    return args


def build_body(
        body_path: str
) -> str:
    """
    Build a body text using a body path. The body path points to a plain text or HTML-formatted message.
    When building a body, variables can be provided as a dictionary to parameterize the given body text.

    Parameters
    -------
    body_path (str): Path to body file as a plain text or HTML-formatted file.

    Returns
    -------
    body (str): Message body formatted as string. 
    """
    body = None
    with open(body_path, "r+") as f:
        body = f.read() 
    f.close()
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
    if attachments_path != None:
        with open(attachments_path[0], "rb") as fp:
            data = fp.read()
        # guess encoding
        ctype, enconding = mimetypes.guess_type(attachments_path[0])
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
    """
    args = runme["arguments"]
    config_path = args.get("config_path", None)
    sender = args.get("sender", None)
    recipients = args.get("recipients", None)
    subject = args.get("subject", None)
    body = args.get("body", None)
    body_path = args.get("body_path", None)
    attachments_path = args.get("attachments_path", None)
    return config_path, sender, recipients, subject, body, body_path, attachments_path


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
    runme_path = inputs.runme
    print("Input args flow complete.")

    if runme_path != None:
        print("Loading runme file flow...")
        print("Warning: runme arguments override CLI arguments.")
        runme = yaml.safe_load(open(runme_path))
        config_path, sender, recipients, subject, body, body_path, attachments_path = parse_runme(runme)
        print("Loading runme file flow complete.")

    print("Loading credentials flow...")
    config = yaml.safe_load(open(config_path))
    credentials = config["credentials"]
    app_password = credentials["gmail"]["app_password"]
    print("Loading credentials flow complete.")

    print("Connecting to SMTP Gmail flow...")
    context = ssl.create_default_context()
    smtp_connection = smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) 
    smtp_connection.login(sender, app_password)
    print("Connecting to SMTP Gmail flow complete.")

    print("Message preview flow...")
    # Note: message preview flow requires temp file cleanup.
    confirm_preview = input(f"Do you want to preview the first message? (y - to confirm)")
    if confirm_preview == "y" or None:
        if body_path != None:
            body = build_body(body_path)
        msg = build_message(sender, recipients[0], subject, body, attachments_path)
        temp_filepath = preview_message(msg)
    else:
        temp_filepath = None
    print("Message preview flow complete.")

    print("Message send flow...")
    confirm_send = input(f"Are you sure you want to send emails to: \n {recipients}? (y - to confirm)")
    if confirm_send=="y":
        for recipient in recipients:
            if body_path != None:
                body = build_body(body_path)
            msg = build_message(sender, recipient, subject, body, attachments_path)
            smtp_connection.send_message(msg, from_addr=sender, to_addrs=recipient)
        print("Message sent!")
    else: 
        print("Message not sent!")
    print("Message send flow complete.")

    print("Cleanup flow...")
    if temp_filepath:
        os.remove(temp_filepath)
    print("Cleanup flow complete.")


if __name__=="__main__":

    jmailer()
    # delete me
    print("run main successful")
