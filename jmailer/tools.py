# Author: Dr. Jaime Alexis Lopez-Merizalde
# tools.py

import datetime as dt
import regex as re

class Timers():
    """A class for  Timing-stamping cell calls."""
    import datetime as dt

    def exec_time(self, msg="Completed task"):
        """
        Runtime message tracking cell progress. Prints an message and a timestamp.
        
        Parameters
        -------
        msg (str): User provided message. Defaults to a generic statement.
        
        Returns
        -------
        None
        """
        try:
            now = dt.datetime.now().strftime("%H:%M:%S - %Y-%m-%d")
            print(
                "{msg} Timestamp: {now}".format(msg=msg, now=now)
            )
        except Exception as e:
            print("Warning: unable to Run exec_time.\nRawmessage: {msg}.\n{error}".format(msg=msg, error=e))


def text_builder(text_path: str, text_vars=None) -> str:
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


class Searchers():
    """A class for finding things."""
    import pandas as pd

    def search_df_rows(df: pd.DataFrame, search_list: list) -> dict:
        """
        Find the rows matching values in a search list.

        Parameters
        -------
        df (pd.DataFrame): DataFrame to search.
        search_list (list): List of search terms to try.

        Returns
        -------
        filtered_df ({}}): Search dictionary with row(s) in original Data Frame matching the results.
        """
        df0 = df.copy(deep=True)


        def search_string(s, search):
            """
            Searches for term search in s. Ingores case.

            Parameters
            -------
            s (str): String to be searched. Ignores case.
            search (str): Term to search.

            Returns
            -------
            (bool): True if search is found in s. False otherwise.
            """
            return search in str(s).lower()


        def format_string(s):
            """
            Formats a string according to a fixed pattern criteria.

            Parameters
            -------
            s (any): To be formatted. If a string, will format. Otherwise, returns same.
            
            Returns
            -------
            (str): Formatted string.
            """
            PATTERN = r"_|\s+|-|:|/|\.|@"
            if not isinstance(s, str):
                return s
            else:
                return re.sub(PATTERN,"",s).lower()
            

        # Before we look through this dataframe with this processed list set,
        # we also have to process the damn dataframe the SAME WAY or we will not find anything.
        df_f = df0.applymap(format_string)

        for search in search_list:
            search = format_string(search) 
            # Search for the string find_this in all columns. True-False DataFrame.
            mask = df_f.applymap(lambda x: search_string(x, search))
            filtered_df = df0.loc[mask.any(axis=1)]
        return filtered_df
    