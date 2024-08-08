import os
from dotenv import load_dotenv

import pandas as pd
import requests
from datetime import datetime


load_dotenv()

# Load the CSV file
csv_path = "nabla.csv"
data = pd.read_csv(csv_path)


# URL for the POST request
url = os.getenv('BASE_URL')
api_token = os.getenv('API_TOKEN')

headers = {
    'Authorization': f'Bearer {api_token}'
}


# Function to format datetime
def format_datetime(date, time):
    return datetime.strptime(f'{date} {time}', '%d/%m/%Y %H:%M:%S').isoformat()


def get_activity(activity):
    if activity == 'pm':
        return 196
    if activity == 'sales':
        return 191
    if activity == 'marketing':
        return 191
    if activity == 'development':
        return 192
    if activity == 'analyses':
        return 190

    return 192


# Iterate over each row in the DataFrame
for index, row in data.iterrows():
    # Create the request body
    request_body = {
        "begin": format_datetime(row['Start Date'], row['Start Time']),
        "end": format_datetime(row['End Date'], row['End Time']),
        "project": 70,
        "activity": get_activity(row['Tags']),
        "description": row['Description'],
        "user": 23
    }

    # Send POST request
    response = requests.post(url, json=request_body, headers=headers)
    if response.status_code == 200:
        print(f"Successfully uploaded data for row {index}")
    else:
        print(f"Failed to upload data for row {index}: {response.text}")

# Print completion message
print("All data uploaded.")
