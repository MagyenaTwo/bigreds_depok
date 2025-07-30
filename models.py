from sqlalchemy import Column, Integer, LargeBinary, String, DateTime, Text, func
from database import Base


class Match(Base):
    __tablename__ = "matches"

    id = Column(Integer, primary_key=True, index=True)
    home_team = Column(String)
    away_team = Column(String)
    match_datetime = Column(DateTime)
    competition = Column(String)


class TicketOrder(Base):
    __tablename__ = "ticket_orders"

    id = Column(Integer, primary_key=True, index=True)
    nama = Column(String(100), nullable=False)
    status = Column(String(20), nullable=False)
    id_card = Column(String(50), nullable=True)
    jumlah = Column(Integer, nullable=False)
    whatsapp = Column(String(20), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    bukti_transfer_url = Column(String(255), nullable=False)
    tiket_file = Column(LargeBinary)  # simpan gambar tiket
    tiket_filename = Column(String(255))  # nama file tiket
    tiket_url = Column(String(255), nullable=True)
    total_harga = Column(Integer, nullable=False)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False)
    password = Column(String(255), nullable=False)  # hashed password


class GalleryNobar(Base):
    __tablename__ = "gallery_nobar"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    image_url = Column(String)
    tanggal = Column(DateTime)


class Berita(Base):
    __tablename__ = "berita"  # ✅ Ganti nama tabel di sini

    id = Column(Integer, primary_key=True, index=True)
    slug = Column(String, unique=True, index=True, nullable=False)
    title = Column(String, nullable=False)
    content = Column(Text, nullable=True)
    cover_image = Column(String, nullable=True)
    publish_date = Column(DateTime, nullable=True)
