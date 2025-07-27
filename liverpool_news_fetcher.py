import requests
from sqlalchemy import create_engine, Column, String, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

# === DB setup ===
DATABASE_URL = "sqlite:///news.db"  # ganti dengan URL database kamu

Base = declarative_base()
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

class News(Base):
    __tablename__ = "news"
    slug = Column(String, primary_key=True)
    title = Column(String)
    teaser = Column(Text)
    image_url = Column(String)
    publish_date = Column(DateTime)

Base.metadata.create_all(bind=engine)

# === Ambil dan simpan berita ===
def fetch_and_save_news():
    url = "https://backend.liverpoolfc.com/lfc-rest-api/id/news?perPage=20"
    res = requests.get(url)
    data = res.json()

    session = SessionLocal()
    for item in data.get("news", []):
        slug = item["slug"]
        if session.query(News).filter_by(slug=slug).first():
            continue  # skip jika sudah ada

        news = News(
            slug=slug,
            title=item["title"],
            teaser=item["teaser"],
            image_url=item["hero"]["image"]["url"] if item.get("hero") else "",
            publish_date=datetime.fromisoformat(item["publishDate"].replace("Z", "+00:00"))
        )
        session.add(news)
    
    session.commit()
    session.close()

if __name__ == "__main__":
    fetch_and_save_news()
