import os
import re
from dotenv import load_dotenv

import pandas as pd
import requests
from datetime import datetime

load_dotenv()

# ---- Project & Activity mapping ----
PROJECTS = {
    "lca": {
        "id": 78,
        "activities": {
            "pm": 222,
            "development": 223,
            "analyses": 423,
            "IT provoz - setup": 540,
            "IT provoz - provoz": 541,
            "Kalkulačka LCA v2": 542
        }
    },
    "nabla": {
        "id": 70,
        "activities": {
            "pm": 196,
            "development": 192,
            "sales": 191
        }
    },
    "xmarton": {
        "id": 112,
        "activities": {
            "development": 445,
            "analyses": 446,
        }
    },
    "viva": {
        "id": 124,
        "activities": {
            "mvp": 464
        }
    }
}

# ---- Load CSV ----
csv_path = "lca.csv"
data = pd.read_csv(csv_path)

# Get project key from filename (without extension, lowercase)
project_key = os.path.splitext(os.path.basename(csv_path))[0].lower()
if project_key not in PROJECTS:
    raise ValueError(f"Project '{project_key}' not found in PROJECTS mapping")

project_cfg = PROJECTS[project_key]
project_id = project_cfg["id"]
activity_map = project_cfg["activities"]

# Build a LOWER-CASED lookup so comparisons are case-insensitive
activity_map_lc = {k.lower(): v for k, v in activity_map.items()}

# ---- API setup ----
url = os.getenv('BASE_URL')
api_token = os.getenv('API_TOKEN')
headers = {'Authorization': f'Bearer {api_token}'}

# ---- Helpers ----
def format_datetime(date_str, time_str):
    """Convert dd/mm/YYYY HH:MM:SS to ISO 8601"""
    return datetime.strptime(f'{date_str} {time_str}', '%d/%m/%Y %H:%M:%S').isoformat()

_SPLIT_RE = re.compile(r'[|/,]+')

def normalize_tag(s: str) -> str:
    """lowercase, trim, collapse internal spaces"""
    s = str(s).strip()
    s = re.sub(r'\s+', ' ', s)
    return s.lower()

def get_activity_id(tags_value: str) -> int:
    """
    Try to map the Tags cell to an activity ID (case-insensitive).
    Supports multiple separators (',', '/', '|'). Tries each token in order.
    Fallback to 'development' if no token matches; if that doesn't exist,
    fallback to the first activity configured for the project.
    """
    raw = str(tags_value) if pd.notna(tags_value) else ""
    # split into potential tokens, or keep whole if no separator
    tokens = [t.strip() for t in _SPLIT_RE.split(raw)] if _SPLIT_RE.search(raw) else [raw.strip()]
    tokens = [t for t in tokens if t]  # drop empties

    # try direct matches (case-insensitive)
    for tok in tokens:
        key = normalize_tag(tok)
        if key in activity_map_lc:
            matched_id = activity_map_lc[key]
            print(f"ℹ️  Activity matched: '{tok}' → ID {matched_id}")
            return matched_id

    # fallback to 'development' for this project if present
    if 'development' in activity_map_lc:
        print(f"⚠️  Unknown activity '{raw}', defaulting to 'development' in project '{project_key}'")
        return activity_map_lc['development']

    # final fallback: first activity in the project's map
    fallback_id = next(iter(activity_map.values()))
    print(f"⚠️  Unknown activity '{raw}', no 'development' defined; defaulting to ID {fallback_id}")
    return fallback_id

# ---- Process CSV rows ----
for index, row in data.iterrows():
    activity_id = get_activity_id(row.get('Tags', ''))

    request_body = {
        "begin": format_datetime(row['Start Date'], row['Start Time']),
        "end": format_datetime(row['End Date'], row['End Time']),
        "project": project_id,
        "activity": activity_id,
        "description": row['Description'],
        "user": 23
    }

    response = requests.post(url, json=request_body, headers=headers)
    if response.status_code == 200:
        print(f"✅ Row {index} uploaded")
    else:
        print(f"❌ Row {index} failed: {response.status_code} {response.text}")

print("🎉 All data processed.")
