# Author: Dr. Jaime Alexis Lopez-Merizalde
# phonebook_handler.py

import regex as re
import requests 
import db_handler


class Clearbit():
    """A class for working with Clearbit API."""
    def get_name(self, response: requests.models.Response) -> (str, str):
        """
        Parse response for HTTP request.

        Parameters
        -------
        response (requests.models.Response): Http response with person data.

        Returns
        -------
        name (str, str): Tuple of first and last name. 
        """
        if not isinstance(response, requests.models.Response):
            print("Not a request.")
            return 
        name = (None, None)
        data = response.json()
        person = data["person"]
        first_name = person["name"]["givenName"]
        last_name = person["name"]["familyName"]
        name = (first_name, last_name)
        return name


    def get_names_from_email_list(self, email_list:[str], username=None, password=None, api_key=None):
        """
        Given a list of recipients, use Clearbit to retreive their names. Other data may be retreieved but at a later stage. 
        The username is the api_key from Clearbit. Read their docs for more info.

        Parameters
        -------
        username (str): Optional. Username.
        password (str): Optional. Password.
        api_key (str): API key.
        email_list (list): List of email. 

        Returns
        -------
        names {}: Dict of emails to names.
        """
        names = {}
        # NOTE: may want to batch this in the future or too many requests will be attempted too quickly.
        for email in email_list:
            url = f"https://person.clearbit.com/v2/combined/find?email=:{email}"
            clearbit_response = requests.get(url, auth=(api_key, password))
            names[email] = self.get_name(clearbit_response)
        return names


class PeopleDataLabs():
    """A class for working with People Data Labs API."""

    def get_details(self, response: requests.models.Response) -> tuple:
        """
        Parse response for HTTP request.

        Parameters
        -------
        response (requests.models.Response): Http response with person data.

        Returns
        -------
        (tuple): Tuple of details.
        """
        if not isinstance(response, requests.models.Response):
            print("Not a request.")
            return 
        response_json = response.json()
        data = response_json["data"]
        first_name = self.format_name(data["first_name"])
        last_name = self.format_name(data["last_name"])
        company_name = self.format_name(data["job_company_name"])
        return (first_name, last_name, company_name)    

    
    def get_name(self, response: requests.models.Response) -> (str, str):
        """
        Parse response for HTTP request.

        Parameters
        -------
        response (requests.models.Response): Http response with person data.

        Returns
        -------
        name (str, str): Tuple of first and last name. 
        """
        if not isinstance(response, requests.models.Response):
            print("Not a request.")
            return 
        name = (None, None)
        response_json = response.json()
        data = response_json["data"]
        first_name = self.format_name(data["first_name"])
        last_name = self.format_name(data["last_name"])
        company_name = self.format_name(data["company"])
        name = (first_name, last_name)
        return name
    

    def format_name(self, name: str) -> str:
        """
        Takes a name with potential special characters and extra spaces to return a properly-formatted name. 
        Capitalizes first letters of place-value locations.

        Parameters
        -------
        name (str): Name with potential special characters or spaces. 

        Returns
        -------
        f_name (str): Formatted name.
        """
        remove_spaces = re.sub("^\s+|\s+$", "", name)

        # Capitolize across special characters.
        pattern = "(^|[^a-zA-Z0-9])([a-zA-Z0-9])"
        f_name = re.sub(pattern, lambda x: x.group(1) + x.group(2).upper(),remove_spaces)
        return f_name
    

    def get_names_from_email_list(self, email_list:[str], username=None, password=None, api_key=None):
        """
        Given a list of recipients, use People Data Labs to retreive their names. 
        Other data may be retreieved but at a later stage. 

        Parameters
        -------
        email_list (list): List of emails to retrieve data for. 
        username (str): Username.
        password (str): Password.
        api_key (str): API key.

        Returns
        -------
        names (dict): Dict of emails to names.
        """
        names = {}
        # NOTE: may want to batch this in the future or too many requests will be attempted too quickly.
        url = f"https://api.peopledatalabs.com/v5/person/enrich"
        for email in email_list:
            params = {
                "api_key": api_key,
                "email": email
            }
            response = requests.get(url, params=params)
            try:
                names[email] = self.get_name(response)
            except Exception as e:
                msg = str(e) + f"\nName fetching failed for: {email}. Skipping this name."
                db_handler.Timers().exec_time(msg)
        return names
    
    
    def get_details_from_email_list(self, email_list: [str], username=None, password=None, api_key=None):
        """
        Get multiple details from a response object returned by People Data Labs API.

        Parameters
        -------
        email_list (list): List of emails to retrieve data for. 
        username (str): Username.
        password (str): Password.
        api_key (str): API key.

        Returns
        -------
        details (dict): Dictionary with email as key and details retrieved as values.
        """
        details = {}
        # NOTE: may want to batch this in the future or too many requests will be attempted too quickly.
        url = f"https://api.peopledatalabs.com/v5/person/enrich"
        for email in email_list:
            params = {
                "api_key": api_key,
                "email": email
            }
            response = requests.get(url, params=params)
            try:
                details[email] = self.get_details(response)
            except Exception as e:
                msg = str(e) + f"\nName fetching failed for: {email}. Skipping this name."
                db_handler.Timers().exec_time(msg)
        return details
