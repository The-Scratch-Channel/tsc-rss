from flask import Flask, Response
from google.cloud import firestore
import os
import html
from datetime import datetime
import tempfile
from dotenv import load_dotenv
from xml.etree.ElementTree import Element, SubElement, tostring

# Load environment
load_dotenv()

firebase_key = os.environ.get("FIREBASE_KEY")
with tempfile.NamedTemporaryFile(mode='w+', delete=False) as f:
    f.write(firebase_key)
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = f.name

db = firestore.Client()

app = Flask(__name__)

def fetch_articles():
    articles_ref = db.collection("articles").order_by("date", direction=firestore.Query.DESCENDING)
    docs = articles_ref.stream()
    articles = []
    for doc in docs:
        data = doc.to_dict()
        articles.append({
            "title": data.get("title", "Untitled"),
            "content": data.get("content", ""),
            "author": data.get("author", "Unknown"),
            "date": data.get("date"),
            "url": data.get("url", "#")
        })
    return articles

def generate_rss_xml(articles):
    rss = Element("rss", version="2.0")
    channel = SubElement(rss, "channel")
    SubElement(channel, "title").text = "The Scratch Channel RSS Feed"
    SubElement(channel, "link").text = "https://thescratchchannel.vercel.app/"
    SubElement(channel, "description").text = "Latest articles"
    SubElement(channel, "lastBuildDate").text = datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT")

    for article in articles:
        item = SubElement(channel, "item")
        SubElement(item, "title").text = article["title"]
        SubElement(item, "link").text = article["url"]
        SubElement(item, "description").text = html.escape(article["content"])
        SubElement(item, "author").text = article["author"]
        SubElement(item, "pubDate").text = (
            article["date"].strftime("%a, %d %b %Y %H:%M:%S GMT")
            if isinstance(article["date"], datetime) else str(article["date"])
        )
    return tostring(rss, encoding='utf-8')

@app.route("/")
def rss_feed():
    articles = fetch_articles()
    rss_xml = generate_rss_xml(articles)
    return Response(rss_xml, mimetype="application/rss+xml")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
