# Author: Dr. Jaime Alexis Lopez-Merizalde
# tools.py

import datetime as dt
import regex as re

from Google import Google


def text_builder(text: str, text_vars=None) -> str:
    """
    Using passed-along dictionary of variable names to values, fill in the text where 
    keywords are specified. May be passed on no variables to fill, in which case the text body 
    is returned as-is. This ignores the case in the text, but it does not ignore case from the text_vars source.

    Parameters
    -------
    text_path (str): Text as string.
    text_vars (dict): Dictionary of variables. Optional.

    Returns
    -------
    query (str): Filled-in text body by value using the text_vars dictionary.
    """
    DEFAULT_FILL_IN = ""
    if text_vars == None:
        return text
    # Extract variables from the text.
    variables_in_text = re.findall("\{(.*?)\}", text, flags=re.IGNORECASE)
    # do a replacement: each time call local_vars...
    for var in variables_in_text:
        replace_me = "\{" + var + "\}"
        replace_with = str(text_vars.get(var, DEFAULT_FILL_IN))
        text = re.sub(replace_me, replace_with, text)
    return text


def get_records(records_path: str, credentials_path=None) -> list:
    """
    Get the records from a records source. This is configured to rely on Google sheets. 
    The returned dictionaries turn headers from the records source into keys.

    Parameters
    -------
    records_path (str): A path the the records. This is in the form of a Google sheet key.
    credentials_path (str): A path to credentials required by the fetcher. For Google sheets, this is a client secret .json file.

    Returns
    -------
     ([dict]): Returns a list of dictionaries with the record information.  Headers from the source are defined as dict keys.
    """
    _, gsheets = Google.Google().google_connect(credentials_path=credentials_path)
    return gsheets.open_by_key(records_path).sheet1.get_all_records(empty_value="", head=1, majdim="ROWS", numericise_data=True)
