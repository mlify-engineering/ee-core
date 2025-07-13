from fastapi import FastAPI
from apscheduler.schedulers.background import BackgroundScheduler
from azure.core.exceptions import ResourceExistsError
from azure.storage.blob import BlobServiceClient
from dotenv import load_dotenv
import aiohttp
import asyncio
import subprocess
from pathlib import Path
import os

# Load .env
load_dotenv()

app = FastAPI()
scheduler = BackgroundScheduler()
scheduler.start()

# ENV
AZURE_STORAGE_CONN = os.getenv("AZURE_STORAGE_CONN")
CONTAINER_NAME = os.getenv("AZURE_CONTAINER_NAME")
DATA_FETCH_URL = os.getenv("DATA_FETCH_URL")

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent

INPUT_FILE = BASE_DIR / "data" / "input.json"
OUTPUT_DIR = BASE_DIR / "data"
PROCESSOR_PATH = BASE_DIR / "src" / "immigration_processor.py"

FILES_TO_UPLOAD = [
    "processed_data_crs_trend.json",
    "processed_data_pool_trend.json",
    "processed_data_draw_size.json",
]

async def fetch_data():
    print(f"Fetching from {DATA_FETCH_URL}...")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(DATA_FETCH_URL) as response:
                response.raise_for_status()
                data = await response.text()
                INPUT_FILE.write_text(data, encoding='utf-8')
                print("Data written to", INPUT_FILE)
    except Exception as e:
        print("Data fetch error:", e)
        raise

def run_processor():
    print("Running immigration processor...")
    try:
        subprocess.run(["python3", str(PROCESSOR_PATH), str(INPUT_FILE), str(OUTPUT_DIR)], check=True)
        print("Processing completed.")
    except subprocess.CalledProcessError as e:
        print("Error running processor:", e)
        raise

def upload_to_blob():
    print("Uploading output to Azure Blob Storage...")
    blob_service = BlobServiceClient.from_connection_string(AZURE_STORAGE_CONN)
    container = blob_service.get_container_client(CONTAINER_NAME)
    try:
        container.create_container()
    except ResourceExistsError:
        pass  # It's okay if it already exists

    for file_name in FILES_TO_UPLOAD:
        file_path = OUTPUT_DIR / file_name
        if file_path.exists():
            with open(file_path, "rb") as f:
                blob_client = container.get_blob_client(file_name)
                blob_client.upload_blob(f, overwrite=True)
                print(f"Uploaded: {file_name}")
        else:
            print(f"Missing file: {file_name}")

async def orchestrate():
    await fetch_data()
    run_processor()
    upload_to_blob()

@app.on_event("startup")
def schedule_cron_job():
    scheduler.add_job(lambda: asyncio.run(orchestrate()), trigger="cron", hour=3, minute=0)  # Run daily at 3 AM

@app.get("/run-now")
async def manual_trigger():
    await orchestrate()
    return {"status": "Processing triggered manually"}