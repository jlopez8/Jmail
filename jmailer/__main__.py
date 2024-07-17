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
        "-cfg", "--config_path", type=str,
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
        "-to", "--recipients", type=str, action="append",
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
        "-a", "--attachments_path", type=str,
        nargs='*',
        help="Path(s) to 0 or more attachment(s)."
    )
    args = parser.parse_args()
    return args


def jmailer():
    """Jmailer method."""

    print("Input args flow...")
    inputs = parse_args()
    config_path = inputs.config_path
    sender = inputs.sender
    recipients = inputs.recipients
    subject = inputs.subject
    body = inputs.body
    attachments_path = inputs.attachments_path
    print("Input args flow complete.")

    print("Loading credentials flow...")
    config = yaml.safe_load(open(config_path))
    credentials = config["credentials"]
    app_password = credentials["gmail"]["app_password"]
    print("Loading credentials flow complete.")

    print("Connecting to SMPT Gmail flow...")
    context = ssl.create_default_context()
    smpt_connection = smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) 
    smpt_connection.login(sender, app_password)
    print("Connecting to SMPT Gmail flow complete.")

    print("Message build flow...")
    msg = build_message(sender, recipients, subject, body, attachments_path)
    print("Message build flow complete.")

if __name__=="__main__":

    jmailer()
    # delete me
    print("run main successful")
