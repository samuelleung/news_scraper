import os
import json
import base64
import gspread
import requests
import feedparser
from oauth2client.service_account import ServiceAccountCredentials

# Google Sheets 設定
SHEET_NAME = "Translated_News"
GOOGLE_SHEETS_CREDENTIALS_FILE = "google_sheets_credentials.json"

# RSS Feeds
RSS_FEEDS = {
    "GB News": "https://www.gbnews.com/feeds/news.rss",
    "Manchester Evening News": "https://www.manchestereveningnews.co.uk/news/?service=rss"
}

def load_google_sheets_client():
    """ 加載 Google Sheets API 客戶端 """
    print("📡 Connecting to Google Sheets...")
    
    if os.getenv("GITHUB_ACTIONS"):  # Detect if running in GitHub Actions
        encoded_creds = os.getenv("GOOGLE_SHEETS_CREDENTIALS")
        if encoded_creds:
            creds_json = json.loads(base64.b64decode(encoded_creds).decode("utf-8"))
            with open(GOOGLE_SHEETS_CREDENTIALS_FILE, "w") as f:
                json.dump(creds_json, f)
    
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name(GOOGLE_SHEETS_CREDENTIALS_FILE, scope)
    client = gspread.authorize(creds)
    print("✅ Connected successfully!")
    return client

def fetch_news_from_feeds():
    """從 RSS Feeds 獲取新聞"""
    news_articles = []
    for source, feed_url in RSS_FEEDS.items():
        print(f"📡 Fetching news from: {feed_url}")
        feed = feedparser.parse(feed_url)
        for entry in feed.entries:
            news_entry = {
                "source": source,
                "title": entry.get("title", "N/A"),
                "link": entry.get("link", "N/A"),
                "summary": entry.get("summary", "N/A"),
                "published": entry.get("published", "N/A"),
                "id": entry.get("id", entry.get("link", "N/A")),
                "media_content": str(entry.get("media_content", "N/A")),
                "media_thumbnail": str(entry.get("media_thumbnail", "N/A")),
                "authors": str(entry.get("authors", "N/A")) if "authors" in entry else entry.get("author", "N/A")
            }
            news_articles.append(news_entry)
    return news_articles

def save_news_to_google_sheets(news_articles):
    """將新聞寫入 Google Sheets，避免重複儲存"""
    client = load_google_sheets_client()
    sheet = client.open(SHEET_NAME).sheet1
    
    print("📝 Checking existing news to avoid duplicates...")
    existing_titles = set(sheet.col_values(2))  # 獲取已存儲的新聞標題
    
    print("📝 Writing fetched news to Google Sheets...")
    headers = ["Source", "Title", "Link", "Summary", "Published", "ID", "Media Content", "Media Thumbnail", "Authors"]
    if not sheet.row_values(1):
        sheet.append_row(headers)
    
    for entry in news_articles:
        if entry["title"] not in existing_titles:
            row = [
                entry["source"], entry["title"], entry["link"], entry["summary"],
                entry["published"], entry["id"], entry["media_content"], entry["media_thumbnail"], entry["authors"]
            ]
            sheet.append_row(row)
            print(f"✅ Written: {entry['title']}")
        else:
            print(f"⚠️ Skipped (duplicate): {entry['title']}")

def main():
    try:
        news_articles = fetch_news_from_feeds()
        print("✅ Fetched News Articles:")
        for entry in news_articles:
            print(f"🔹 {entry['title']}")
        
        save_news_to_google_sheets(news_articles)
        print("🎉 All new news saved successfully!")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()