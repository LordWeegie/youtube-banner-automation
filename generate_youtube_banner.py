import requests
from PIL import Image, ImageDraw, ImageFont
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import os

# API setup for YouTube Data API (use environment variables)
API_KEY = os.getenv("YOUTUBE_API_KEY")
CHANNEL_ID = os.getenv("YOUTUBE_CHANNEL_ID")

# Validate environment variables
if not API_KEY or not CHANNEL_ID:
    raise ValueError("Missing required environment variables: YOUTUBE_API_KEY or YOUTUBE_CHANNEL_ID")

# Fetch subscriber count
url = f"https://www.googleapis.com/youtube/v3/channels?part=statistics&id={CHANNEL_ID}&key={API_KEY}"
response = requests.get(url).json()

# Check if the API request was successful
if "items" not in response:
    print("Error fetching subscriber count. API response:", response)
    if "error" in response:
        print("API Error Details:", response["error"])
    raise KeyError("Failed to fetch subscriber count: 'items' not found in API response")

subscriber_count = int(response["items"][0]["statistics"]["subscriberCount"])

# Goal and progress calculation
GOAL = 100
progress = min(subscriber_count / GOAL, 1.0)
progress_percentage = progress * 100

# Create banner image
banner = Image.new("RGB", (2560, 1440), color=(50, 50, 50))
draw = ImageDraw.Draw(banner)

# Load font
try:
    font = ImageFont.truetype("roboto-bold.ttf", 100)
except:
    font = ImageFont.truetype("arial.ttf", 100)

# Draw subscriber count text
text = f"{subscriber_count} / {GOAL} Subscribers"
bbox = draw.textbbox((0, 0), text, font=font)
text_width = bbox[2] - bbox[0]
text_height = bbox[3] - bbox[1]
text_position = (1280 - text_width // 2, 600 - text_height // 2)
draw.text(text_position, text, font=font, fill=(255, 255, 255))

# Draw progress bar
bar_width = 1000
bar_height = 50
bar_x = (2560 - bar_width) // 2
bar_y = 720
draw.rectangle(
    [bar_x, bar_y, bar_x + bar_width, bar_y + bar_height],
    fill=(150, 150, 150),
    outline=(255, 255, 255)
)
filled_width = bar_width * progress
draw.rectangle(
    [bar_x, bar_y, bar_x + filled_width, bar_y + bar_height],
    fill=(0, 255, 0)
)

# Draw percentage text
small_font = ImageFont.truetype("arial.ttf", 50)
percentage_text = f"{progress_percentage:.1f}%"
percentage_bbox = draw.textbbox((0, 0), percentage_text, font=small_font)
percentage_width = percentage_bbox[2] - percentage_bbox[0]
percentage_height = percentage_bbox[3] - percentage_bbox[1]
percentage_position = (1280 - percentage_width // 2, bar_y + bar_height + 20)
draw.text(percentage_position, percentage_text, font=small_font, fill=(255, 255, 255))

# Save the banner
banner_file = "youtube_banner_with_progress.png"
banner.save(banner_file)

# Google Drive API setup
SCOPES = ["https://www.googleapis.com/auth/drive.file"]
creds = None
token_path = "token.json"

# Check if credentials.json exists
if not os.path.exists("credentials.json"):
    raise FileNotFoundError("credentials.json not found. Please download it from Google Cloud Console and place it in the script's directory.")

# Load or generate credentials
if os.path.exists(token_path):
    creds = Credentials.from_authorized_user_file(token_path, SCOPES)
if not creds or not creds.valid:
    flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
    creds = flow.run_local_server(port=0)
    with open(token_path, "w") as token:
        token.write(creds.to_json())

# Build Drive API service
drive_service = build("drive", "v3", credentials=creds)

# Upload banner to Google Drive (use environment variable for folder ID)
folder_id = os.getenv("DRIVE_FOLDER_ID")
if not folder_id:
    raise ValueError("Missing required environment variable: DRIVE_FOLDER_ID")

file_metadata = {
    "name": "youtube_banner_with_progress.png",
    "parents": [folder_id]
}
media = MediaFileUpload(banner_file)
file = drive_service.files().create(
    body=file_metadata,
    media_body=media,
    fields="id"
).execute()

print("Banner generated and uploaded to Google Drive:", file.get("id"))