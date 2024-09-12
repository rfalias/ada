import requests
import json
import urllib3
import os
import re

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
headers = {
    "Content-Type": "application/json"
}

url = "https://127.0.0.1:7777/api/v1"
def post_request(url, function, data, token=None):
    headers = {
        "Content-Type": "application/json",
    }
    
    if token:
        headers["Authorization"] = f"Bearer {token}"

    payload = {
        "function": function,
        "data": data
    }
    
    response = requests.post(url, headers=headers, data=json.dumps(payload), verify=False)
    return response.json()

def health_check(client_custom_data):
    data = {
        "ClientCustomData": client_custom_data
    }
    return post_request(url, "HealthCheck", data)


def query_server_state():
    data = {}
    return post_request(url, "QueryServerState", data)

def enumerate_sessions():
    data = {}
    return post_request(url, "EnumerateSessions", data)



def get_server_options():
    data = {}
    return post_request(url, "GetServerOptions", data)


def extract_strings_from_file(file_path, min_length=4):
    # Open the binary file in read mode
    with open(file_path, 'rb') as f:
        content = f.read()

    # Define a regex pattern to match sequences of printable ASCII characters
    pattern = rb'[ -~]{' + str(min_length).encode() + rb',}'  # Printable ASCII chars

    # Find all sequences of printable characters in the file
    matches = re.findall(pattern, content)

    # Convert bytes to strings and return them
    return [match.decode('ascii') for match in matches]
#FactoryGame-LinuxServer.utoc_Export/FactoryGame/Content/FactoryGame/Narrative/Tier4/MSG_Tier4_Schematic_4-4.uasset


def find_file(start_dir, partial_name):
    matching_files = []
    # Walk through the directory tree
    for dirpath, dirnames, filenames in os.walk(start_dir):
        for filename in filenames:
            # Check if the partial name is in the filename
            if partial_name in filename:
                matching_files.append(os.path.join(dirpath, filename))
    return matching_files


def get_current_milestone():
    s = query_server_state()
    milestone = s['data']['serverGameState']['activeSchematic']
    milestone_schematic = milestone.split('/')[-1].split('.')[0]
    narrative_base = "FactoryGame-LinuxServer.utoc_Export/FactoryGame/Content/FactoryGame/Narrative/"
    info_file = find_file(narrative_base, milestone_schematic)[0]
    tier_from_info = info_file.split('/')
    tier_number = 0
    for part in tier_from_info:
        if "Tier" in part:
            tier_number = part[-1]
            break
    details = extract_strings_from_file(info_file)
    milestone_name = ""
    for d in details:
        if f"Tier {tier_number} -" in d:
            milestone_name = d
            continue
    return milestone_name

