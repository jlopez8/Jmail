# Author: Dr. Jaime Alexis Lopez-Merizalde
# Google.py
from pathlib import Path

import pandas as pd

from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import pygsheets

class Google():
    """"A class to connect to Google services."""

    import pickle
    SERVICE_ACCOUNT = None

    def google_connect(self, credentials_path=None, service_account_env_var=None) -> (any, pygsheets.client.Client):
        """
        Connects to google drive and spreadsheets. Requires '[...]/client_secrets[...].json" and or 
        a service account variable in the form of a name (str).
        Will create a token in '.' to track authentication. 
        Returns a service object to allow connections to google drive files.
        Warning: do not share your token or anyone will have access to all content on your drive.

        Parameters
        -------
        credentials_path (str): Path to client secrets json.
        service_account_env_var (str): Name of environment variable for google connection.
        
        Returns
        -------
        gdrive (googleapiclient.discovery.Resource): Resource object with connection to google drive.
        gsheets (pygsheets.client.Client): pygsheets client object to manipulate gsheets.
        """
        
        SCOPES = ["https://www.googleapis.com/auth/drive"]
        gdrive, gsheets = None, None

        if credentials_path != None: 
            creds = None 
            # Authentication flow.
            if Path("token.pickle").exists():
                with open("token.pickle", "rb") as token:
                    creds = self.pickle.load(token)
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
                    creds = flow.run_local_server(port=0)
                    # Save access token for future use.
                    with open("token.pickle", "wb") as token:
                        self.pickle.dump(creds, token)
            gdrive = build("drive", "v3", credentials=creds)
            gsheets = pygsheets.authorize(custom_credentials=creds)
        elif service_account_env_var != None:
            # dev note: not getting gdrive in this case yet.
            gsheets = pygsheets.authorize(service_account_env_var=service_account_env_var)
        return gdrive, gsheets
    

    def write_to_googlesheets(
        self, 
        data: pd.DataFrame, 
        gsheetkey: str,
        gsheets: pygsheets.client.Client,
        wks_title: str, 
        row_start="A1",
        
    ) -> None:
        """
        Push DataFrame to Googlesheet via key.

        Parameters
        -------
        data (pd.DataFrame): Dataframe with data to push.
        gsheetkey (str): Key to google sheet.
        gsheets (pygsheets.client.Client): Google sheets connection object.
        data (pd.DataFrame): Dataframe with data to push.
        wks_title (str): Worksheet title.
        row_start (str): Set where the dataframe starting cell will write. Use A1 formatting.
    
        Returns
        -------
        (None)
        """
        df0 = data.copy(deep=True) 
        sh = gsheets.open_by_key(gsheetkey)
        wks = sh.worksheet("title", wks_title)
        wks.clear(start=row_start, end=None)
        if wks.rows < len(df0):
            print("Warning: Data rows exceeds worksheet rows available. Expanding worksheet.")
            wks.resize(rows=len(df0))
        wks.set_dataframe(df0, start=row_start, copy_head=True)
        print(f"Pushed data to gsheet with key:{gsheetkey}")
