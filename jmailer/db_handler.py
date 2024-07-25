# Author: Dr. Jaime Alexis Lopez-Merizalde
# db_handler.py

import os
import argparse
import shlex
from pathlib import Path

import datetime as dt
import regex as re

import yaml

import pandas as pd

import requests


from tools import Timers
import phonebooks


DB_CONFIG_PATH = "/Users/jaimemerizalde/Desktop/JOBS 2023/software/jmailer/db_config.yaml"

def parse_args():
    def convert_arg_line_to_args(arg_line):
        for arg in shlex.split(arg_line):
            if not arg.strip():
                continue
            yield arg

    parser = argparse.ArgumentParser(
        prog="db_handler.",
        description="A package for handling database interactions.",
        epilog="Thank you for using db_handler.",
        fromfile_prefix_chars="@",
    )

    parser.convert_arg_line_to_args = convert_arg_line_to_args

    parser.add_argument(
        "-c", "--credentials_path", type=str,
        help="Credentials path."
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
        "-r", "--recipients", type=str,
        nargs="*",
        help="List of recipients."
    )
    parser.add_argument(
        "-rp", "--recipients_path", type=str,
        help="Path to a receipients file (csv)."
    )
    parser.add_argument(
        "--local_phonebook_path", type=str,
        help="Path to local phonebook csv."
    )
    args = parser.parse_args()
    return args


class DB_handler():
    """
    A class for handling my database connections.
    """

    def __init__(self):
        self.dB_config_path = DB_CONFIG_PATH


    def _load_config(
        self,
        credentials_path: str, 
    ):
        """
        Load configurations for database.

        Parameters
        -------
        credentials_path (str): Path to credentials.

        Returns
        -------
        ((list)): Tuple of columns.
        """
        db_configs = yaml.safe_load(open(self.dB_config_path))
        merge_columns = db_configs["column_configs"]["merge_columns"]
        fixed_columns = db_configs["column_configs"]["fixed_columns"]
        update_columns = db_configs["column_configs"]["update_columns"]
        sort_by = db_configs["column_configs"].get("sort_by", None)
        return merge_columns, fixed_columns, update_columns, sort_by
    

    def get_recipients_from_path(self, filepath: str) -> list:
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
    

    def cross_check_emails(self, recipients: list, gsheets: pygsheets.client.Client, db_identifier: str, db_table: str) -> (list, list):
        """
        Takes a list of emails and returns those that do not already exist in the (gsheet) database.
        
        Parameters
        -------
        recipients ([str]): List of emails to be cross-checked.
        gsheets (pygsheets.client.Client): pygsheets client object to manipulate gsheets.
        db_identifier (str): Key identifying location of database. 
        db_table (str): Table identifier.

        Returns
        -------
        reduced_recipients ([str]): Reduced list of emails.
        repeated_recipients ([str]): List of recipients that have already been recorded.
        """
        reduced_recipients = []
        repeated_recipients = []

        # Get the table data.
        sh = gsheets.open_by_key(db_identifier)
        worksheets = sh.worksheets()
        wks = sh.worksheet("title", db_table)
        original_df = wks.get_as_df()

        # Cross-check.
        existing_emails = original_df["EMAIL"].to_list()
        reduced_recipients = [col for col in recipients if not col in existing_emails]
        repeated_recipients = [col for col in recipients if col in existing_emails]
        return reduced_recipients, repeated_recipients

    
    def details_to_df(self, data: dict) -> dict: 
        """
        Given a dictionary of data including the key as the detail id and the values as details such as first and last name and company name. 
        return collect this information into one single DataFrame.

        Parameters
        -------
        data (dict): Dictionary of detail id and details.

        Returns
        -------
        response_df (dict): Dataframe of collection of respones.
        """
        response_df = None
        json_data = {}
        for key, detail in data.items():
            try: 
                json_data[key] = {
                    "CREATEDATETIME":  dt.datetime.today().strftime("%Y-%m-%d"),
                    "FIRST_NAME": detail.get("first_name", ""),
                    "LAST_NAME": detail.get("last_name", ""),
                    "EMAIL": key,
                    "COMPANY": detail.get("company_name", ""),
                    "LAST_OUTREACH":  dt.datetime.today().strftime("%Y-%m-%d"),
                    "FIRST_OUTREACH": dt.datetime.today().strftime("%Y-%m-%d"),
                }
            except Exception as e:
                msg = f"No response recorded for {key}. " + str(e)
                Timers().exec_time(msg)

        if len(json_data) > 0:
            response_df = pd.DataFrame.from_dict(json_data, orient="index")
            response_df.reset_index(drop=True, inplace=True)
        return response_df


    def clean_df(self, df, drop_columns, pattern, permuted_columns=None) -> pd.DataFrame:
        """
        Drops columns from frame. 
        Cleans up columns using regex pattern matching. 
        If permuted_columns is provided, will re-arrange dataframe columns accordingly.

        Parameters
        -------
        df (pd.DataFrame): Dataframe to process.
        drop_columns ([any]): List of columns to drop.
        pattern (str): Regex expression for column-renaming.
        permuted_columns ([any]): Column re-arrangement list. 

        Returns
        -------
        df (pd.DataFrame): DataFrame.
        """
        df.drop(columns=drop_columns, inplace=True)
        original_columns = df.columns.to_list()
        new_columns = list(map(lambda x: re.sub(pattern, "", x), original_columns))
        columns_dict = dict(zip(original_columns, new_columns))
        df.rename(columns=columns_dict, inplace=True)
        if permuted_columns != None:
            df = df[permuted_columns]
        return df


    def update_dataframe_conditionally(
        self,
        new_df: pd.DataFrame, 
        original_df: pd.DataFrame,
        merge_columns: list,
        fixed_columns: list,
        update_columns: list,
        sort_by=None,
        ascending=False,
    ) -> pd.DataFrame:
        """
        Update using provided conditions as lists.

        Parameters
        -------
        new_df (pd.DataFrame): Dataframe with new data.
        original_df (pd.DataFrame): Dataframe with original data.
        merge_columns (['str']): Columns to merge data on. 
        fixed_columns (['str']): Columns to preserve data.
        update_columns (['str']): Columns to update data.
        sort_by (any): Column(s) to sort returning DataFrame. 
        ascending (bool): Direction to sort. Defaults to descending order.

        Returns
        -------
        updated_df (pd.DataFrame): Returns updated DataFrame
        """
        SUFFIXES = ("_new", "_old")
        updated_df = None

        # Reg ex pattern.
        pattern = r"|".join(SUFFIXES)

        # Double-check that update_columns does not conflict with merge columns.
        update_columns = [col for col in update_columns if not col in merge_columns]

        # Start flow.
        original_columns = original_df.columns.to_list()
        merged_df = new_df.merge(original_df, how="outer", on=merge_columns, suffixes=SUFFIXES)
        update_data = new_df.merge(original_df, how="inner", on=merge_columns, suffixes=SUFFIXES)

        # New data.
        drop_columns = [col + SUFFIXES[1] for col in fixed_columns + update_columns]
        new_data = merged_df[merged_df[drop_columns].isna().all(axis=1)]
        new_data = self.clean_df(new_data, drop_columns, pattern, permuted_columns=original_columns)

        # No-change data.
        drop_columns = [col + SUFFIXES[0] for col in fixed_columns + update_columns]
        no_change_data = merged_df[merged_df[drop_columns].isna().all(axis=1)]
        no_change_data = self.clean_df(no_change_data, drop_columns, pattern, permuted_columns=original_columns)

        # Update data.
        drop_columns = [col + SUFFIXES[0] for col in fixed_columns] + [col + SUFFIXES[1] for col in update_columns]
        update_data = self.clean_df(update_data, drop_columns, pattern, permuted_columns=original_columns)

        updated_df = pd.concat([new_data, no_change_data, update_data])
        if sort_by != None:
            updated_df.sort_values(sort_by, ascending=ascending)

        return updated_df


    def db_contacts_updater(
        self, 
        credentials_path: str,
        db_identifier: str, 
        table: str,
        details: dict,
    ):
        """
        Updates a given database by an identifier. Usually some key. 

        Parameters
        -------
        credentials_path (str): Path to credentials.
        db_identifier (str): Key identifying location of database. 
        table (str): Table to write to.
        details (dict): Dictionary of detail id and details to cross-check and update with the specified table.

        Returns
        -------
        (none)
        """
        # NOTE: This is a good start for a general database updater.
        sort_by = ["CREATEDATETIME"]

        merge_columns, fixed_columns, update_columns, sort_by = self._load_config(credentials_path)

        # Open a connection to Google.
        google = Google()
        _, gsheets = google.google_connect(credentials_path=credentials_path)

        # Get the original data.
        sh = gsheets.open_by_key(db_identifier)
        worksheets = sh.worksheets()
        wks = sh.worksheet("title", table)
        original_df = wks.get_as_df()

        new_data = self.details_to_df(details)

        if not new_data is None:
            updated_data = self.update_dataframe_conditionally(new_data, original_df, merge_columns, fixed_columns, update_columns, sort_by=sort_by, ascending=False,)
            google.write_to_googlesheets(updated_data, db_identifier, gsheets, table, row_start="A1")
        else:
            msg = "No new data to update!"
            Timers().exec_time(msg)
        return 


def main():
    inputs = parse_args()
    credentials_path = inputs.credentials_path
    db_identifier = inputs.db_identifier
    db_table = inputs.db_table
    recipients = inputs.recipients
    recipients_path = inputs.recipients_path
    local_phonebook_path = inputs.local_phonebook_path

    msg = "Parsed args flow complete."
    Timers().exec_time(msg)

    msg = "Fetching phonebook."
    Timers().exec_time(msg)
    # phonebook = phonebooks.PeopleDataLabs()
    phonebook = phonebooks.LocalPhoneBook()

    if not (recipients_path is None) and (recipients is None):
        recipients = DB_handler().get_recipients_from_path(recipients_path)
    msg = "Get recipients flow complete."
    Timers().exec_time(msg)

    details = phonebook.get_details_from_email_list(recipients, local_phonebook_path)

    msg = "Updating database."
    Timers().exec_time(msg)
    DB_handler().db_contacts_updater(
        credentials_path,
        db_identifier,
        db_table,
        details
    )
    return

    
if __name__ == "__main__":
    main()
    Timers().exec_time(f"Completed db_handler run.")
