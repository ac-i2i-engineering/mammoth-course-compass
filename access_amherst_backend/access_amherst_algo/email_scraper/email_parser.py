import imaplib
import email
from email.header import decode_header
import json
import os
import re
from datetime import datetime
from dotenv import load_dotenv
import requests  # Use requests for API calls

# Load environment variables
load_dotenv()

# LLaMA API endpoint
LLAMA_API_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# System instruction for extracting events and generating valid JSON format
instruction = """
    You will be provided an email containing many events.
    Extract detailed event information and provide the result as a list of event JSON objects. Make sure to not omit any available information.
    Ensure all fields are included, even if some data is missing (set a field to null (with no quotations) if the information is not present).
    Use this format for each event JSON object:

    {{
        "title": "Event Title",
        "pub_date": "YYYY-MM-DD",
        "starttime": "HH:MM:SS",
        "endtime": "HH:MM:SS",
        "location": "Event Location",
        "event_description": "Event Description",
        "host": ["Host Organization"],
        "link": "Event URL",
        "picture_link": "Image URL",
        "categories": ["Category 1", "Category 2"],
        "author_name": "Author Name",
        "author_email": "author@email.com"
    }}

    Ensure all fields follow the exact format above. Only return the list of event JSON objects. START WITH [{. END WITH }].
"""


# Function to connect to Gmail and fetch the latest email from a specific sender
def connect_and_fetch_latest_email(
    app_password, subject_filter, mail_server="imap.gmail.com"
):
    """
    Connect to the email server and fetch the latest email matching a subject filter.

    This function connects to the specified IMAP email server (default is Gmail),
    logs in using the provided app password, and searches for the most recent email
    with a subject matching the `subject_filter`. It returns the email message object 
    of the latest matching email.

    Args:
        app_password (str): The app password used for logging into the email account.
        subject_filter (str): The subject filter used to search for specific emails.
        mail_server (str, optional): The IMAP email server address (default is 'imap.gmail.com').

    Returns:
        email.message.Message or None: The latest email message matching the filter, or None if no matching email is found or login fails.

    Example:
        >>> email = connect_and_fetch_latest_email("amherst_college_password", "Amherst College Daily Mammoth for Sunday, November 3, 2024")
        >>> if email:
        >>>     print(email["From"])
        'noreply@amherst.edu'
    """
    mail = imaplib.IMAP4_SSL(mail_server)
    try:
        mail.login(os.getenv("EMAIL_ADDRESS"), app_password)
        print("Logged in successfully")
    except imaplib.IMAP4.error as e:
        print(f"Login failed: {e}")
        return None

    mail.select("inbox")
    status, messages = mail.search(None, f'SUBJECT "{subject_filter}"')
    if status != "OK":
        print(f"Failed to fetch emails: {status}")
        return None

    for msg_num in messages[0].split()[-1:]:  # Only fetch the latest message
        res, msg = mail.fetch(msg_num, "(RFC822)")
        for response_part in msg:
            if isinstance(response_part, tuple):
                msg = email.message_from_bytes(response_part[1])
                return msg
    return None


# Function to extract the email body
def extract_email_body(msg):
    """
    Extract the body of an email message.

    This function extracts and returns the plain-text body of the given email message.
    It handles both multipart and non-multipart emails, retrieving the text content from 
    the message if available. If the email is multipart, it iterates over the parts to find 
    the "text/plain" part and decodes it. If the email is not multipart, it directly decodes 
    the payload.

    Args:
        msg (email.message.Message): The email message object from which to extract the body.

    Returns:
        str: The decoded plain-text body of the email, or None if no text content is found.

    Example:
        >>> email_body = extract_email_body(email_msg)
        >>> print(email_body)
        'This is information about Amherst College events on Sunday, November 3, 2024.'
    """
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            if content_type == "text/plain":
                return part.get_payload(decode=True).decode("utf-8")
    else:
        return msg.get_payload(decode=True).decode("utf-8")


# Function to extract event info using LLaMA API
def extract_event_info_using_llama(email_content):
    """
    Extract event info from the email content using the LLaMA API.

    This function sends the provided email content to the LLaMA API for processing. 
    It sends the email content along with an instruction to extract event details.
    If the API response is valid, the function parses and returns the extracted 
    event information as a list of event JSON objects.

    Args:
        email_content (str): The raw content of the email to be processed by the LLaMA API.

    Returns:
        list: A list of event data extracted from the email content in JSON format.
              If extraction fails, an empty list is returned.

    Example:
        >>> events = extract_event_info_using_llama("We're hosting a Literature Speaker Event this Tuesday, November 5, 2024 in Keefe Campus Center!")
        >>> print(events)
        [{"title": "Literature Speaker Event", "date": "2024-11-05", "location": "Keefee Campus Center"}]
    """

    # API payload for LLaMA
    payload = {
        "model": "meta-llama/llama-3.1-405b-instruct:free",
        "messages": [
            {"role": "system", "content": instruction},
            {"role": "user", "content": email_content},
        ],
    }

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }

    # Send the API request
    response = requests.post(LLAMA_API_URL, headers=headers, json=payload)

    # Check for a valid response
    if response.status_code == 200:
        try:
            # Parse the JSON response
            response_data = response.json()
            print(response_data)

            # Extract the content of the message
            extracted_events_json = response_data["choices"][0]["message"][
                "content"
            ]

            # Now parse the extracted content as JSON
            events_data = json.loads(
                extracted_events_json
            )  # Convert the content to a list of event JSON objects
            return events_data
        except (json.JSONDecodeError, KeyError) as e:
            print(f"Failed to parse LLaMA API response: {e}")
            return []
    else:
        print(f"Failed to fetch data from LLaMA API: {response.status_code}")
        return []


# Function to save the extracted events to a JSON file
def save_to_json_file(data, filename, folder):
    """
    Save the extracted events to a JSON file.

    This function checks if the specified folder exists, creates it if it does not,
    and saves the provided event datato a JSON file with the specified filename.
    The data is saved with indentation for readability and structure.

    Args:
        data (dict or list): The data to be saved in JSON format. Typically, this would 
                              be a list or dictionary containing event data.
        filename (str): The name of the file where the data will be saved (e.g., 'extracted_events_20241103_124530.json').
        folder (str): The folder where the JSON file will be stored (e.g., 'json_outputs').

    Returns:
        None: This function does not return any value. It prints a message upon success 
              or failure.

    Example:
        >>> events = [{"title": "Literature Speaker Event", "date": "2024-11-05", "location": "Keefee Campus Center"}]
        >>> save_to_json_file(events, "extracted_events_20241103_124530.json", "json_outputs")
        Data successfully saved to json_outputs/extracted_events_20241103_124530.json
    """
    # Ensure the folder exists
    if not os.path.exists(folder):
        os.makedirs(folder)

    # Construct the full file path
    file_path = os.path.join(folder, filename)

    try:
        with open(file_path, "w") as json_file:
            json.dump(
                data, json_file, indent=4
            )  # Save data with indentation for readability
        print(f"Data successfully saved to {file_path}")
    except Exception as e:
        print(f"Failed to save data to {file_path}: {e}")


# Main function to parse the email and extract events
def parse_email(subject_filter):
    """
    Parse the email and extract event data.

    This function connects to an email account, fetches the latest email based on the 
    provided subject filter, extracts event information from the email body using the 
    LLaMA API, and saves the extracted events to a JSON file. The file is saved with 
    a timestamped filename in the 'json_outputs' directory.

    Args:
        subject_filter (str): The subject filter to identify the relevant email to fetch.

    Returns:
        None: This function does not return any value. It prints status messages 
              for each stage of the process (success or failure).

    Example:
        >>> parse_email("Amherst College Daily Mammoth for Sunday, November 3, 2024")
        Email fetched successfully.
        Events saved successfully to extracted_events_20231107_150000.json.
    """
    app_password = os.getenv("EMAIL_PASSWORD")

    # Fetch the latest email
    msg = connect_and_fetch_latest_email(app_password, subject_filter)
    if msg:
        email_body = extract_email_body(msg)
        print("Email fetched successfully.")

        # Extract the event information from the email body using LLaMA API
        all_events = extract_event_info_using_llama(email_body)
        print(all_events)

        if all_events:  # Ensure data exists
            try:
                # Generate a timestamped filename
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"extracted_events_{timestamp}.json"

                # Get current directory
                curr_dir = os.path.dirname(os.path.abspath(__file__))

                # Define the relative path to the json_outputs directory
                output_dir = os.path.join(curr_dir, "json_outputs")

                # Ensure the directory exists
                if not os.path.exists(output_dir):
                    os.makedirs(output_dir)

                # Save the modified events data to a JSON file
                save_to_json_file(all_events, filename, output_dir)

                print(f"Events saved successfully to {filename}.")
            except json.JSONDecodeError as e:
                print(f"Failed to parse JSON: {e}")
        else:
            print("No event data extracted or extraction failed.")
    else:
        print("No emails found or login failed.")
