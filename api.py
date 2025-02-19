import os
import requests
import time
from dotenv import load_dotenv
import matplotlib.pyplot as plt
import pandas as pd
from datetime import datetime, timedelta

# Load environment variables from .env file
load_dotenv()

# Get the API key from the environment variable
api_key = os.getenv('API_KEY')

if not api_key:
    raise ValueError("API_KEY is not set in the .env file")

# Dataset IDs
windId = 181
hydroId = 191
nuclearId = 188
co2Id = 266

# Define the API endpoints
wind_url = f"https://data.fingrid.fi/api/datasets/{windId}/data"
hydro_url = f"https://data.fingrid.fi/api/datasets/{hydroId}/data"
nuclear_url = f"https://data.fingrid.fi/api/datasets/{nuclearId}/data"
co2_url = f"https://data.fingrid.fi/api/datasets/{co2Id}/data"

# Set the headers with the API key
headers = {
    "x-api-key": api_key
}

# Function to fetch all data from an API endpoint with pagination

def fetch_all_data(url, start_time=None, end_time=None):
    all_data = []
    params = {
        'pageSize': 1000  # Set to a large page size to minimize the number of requests
    }
    if start_time:
        params['startTime'] = start_time
    if end_time:
        params['endTime'] = end_time

    page = 1
    while True:
        params['page'] = page
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            data = response.json().get('data', [])
            if not data:
                break  # Exit loop if no more data is returned
            all_data.extend(data)
            page += 1
        elif response.status_code == 429:
            print(f"Rate limit exceeded. Retrying in 1 second (Page {page})...")
            time.sleep(1)  # Wait before retrying
        else:
            print(f"Failed to fetch data from {url}. Status code: {response.status_code}")
            print("Error:", response.text)
            break
    return all_data

# Specify the time range (last 24 hours)
end_time = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
start_time = (datetime.utcnow() - timedelta(hours=24)).strftime("%Y-%m-%dT%H:%M:%SZ")

# Fetch data for each category within the specified time range
data_wind = fetch_all_data(wind_url, start_time, end_time)
data_hydro = fetch_all_data(hydro_url, start_time, end_time)
data_nuclear = fetch_all_data(nuclear_url, start_time, end_time)
data_co2 = fetch_all_data(co2_url, start_time, end_time)

# Convert data to Pandas DataFrames
def to_dataframe(data):
    df = pd.DataFrame(data)
    if 'startTime' in df.columns:
        df["startTime"] = pd.to_datetime(df["startTime"])
    else:
        print("Warning: Missing 'startTime' in data")
    return df

df_wind = to_dataframe(data_wind)
df_hydro = to_dataframe(data_hydro)
df_nuclear = to_dataframe(data_nuclear)
df_co2 = to_dataframe(data_co2)

# Plotting
fig, ax1 = plt.subplots(figsize=(12, 8))

# Plot clean energy sources on the primary y-axis
if not df_wind.empty and "startTime" in df_wind.columns:
    ax1.plot(df_wind["startTime"], df_wind["value"], label="Wind Power", color="blue", marker="o")
if not df_hydro.empty and "startTime" in df_hydro.columns:
    ax1.plot(df_hydro["startTime"], df_hydro["value"], label="Hydro Power", color="green", marker="o")
if not df_nuclear.empty and "startTime" in df_nuclear.columns:
    ax1.plot(df_nuclear["startTime"], df_nuclear["value"], label="Nuclear Power", color="purple", marker="o")

ax1.set_xlabel("Time")
ax1.set_ylabel("Power Output (MW)")
ax1.legend(loc="upper left")

# Create a secondary y-axis for CO2 emissions
ax2 = ax1.twinx()

if not df_co2.empty and "startTime" in df_co2.columns:
    ax2.plot(df_co2["startTime"], df_co2["value"], label="CO2 Emissions", color="red", linestyle="--", marker="x")

ax2.set_ylabel("CO2 Emissions (scaled)")
ax2.legend(loc="upper right")

# Title and layout
plt.title("Power Output vs CO2 Emissions Over Time")
plt.tight_layout()

# Show plot
plt.show()
