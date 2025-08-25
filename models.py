from datetime import datetime
from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    ForeignKey,
    Integer,
    LargeBinary,
    String,
    DateTime,
    Text,
    func,
)
from database import Base
from sqlalchemy.orm import relationship


class Match(Base):
    __tablename__ = "matches"

    id = Column(Integer, primary_key=True, index=True)
    home_team = Column(String)
    away_team = Column(String)
    match_datetime = Column(DateTime)
    competition = Column(String)
    actual_home_score = Column(Integer, nullable=True)
    actual_away_score = Column(Integer, nullable=True)


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
    jumlah_terpakai = Column(Integer, default=0)
    metode_pembayaran = Column(String(50), nullable=False)
    sudah_dikirim = Column(Boolean, default=False)
    alias_url = Column(String, unique=True, index=True, nullable=True)


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
    kategori = Column(String, default="event")
    deskripsi = Column(Text)


class Berita(Base):
    __tablename__ = "berita"  # ✅ Ganti nama tabel di sini

    id = Column(Integer, primary_key=True, index=True)
    slug = Column(String, unique=True, index=True, nullable=False)
    title = Column(String, nullable=False)
    content = Column(Text, nullable=True)
    cover_image = Column(String, nullable=True)
    publish_date = Column(DateTime, nullable=True)


class Leaderboard(Base):
    __tablename__ = "leaderboard"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    score = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    game_key = Column(String, ForeignKey("games.game_key"), nullable=False)


class Game(Base):
    __tablename__ = "games"

    id = Column(Integer, primary_key=True, index=True)
    game_key = Column(String(50), unique=True, nullable=False)
    title = Column(String(100), nullable=False)
    description = Column(Text)
    icon = Column(String(10))
    status = Column(String(10), nullable=False, default="locked")

    __table_args__ = (
        CheckConstraint("status IN ('open','locked')", name="check_status"),
    )


class ScorePrediction(Base):
    __tablename__ = "score_predictions"

    id = Column(Integer, primary_key=True, index=True)
    match_id = Column(
        Integer, ForeignKey("matches.id", ondelete="CASCADE"), nullable=True
    )
    full_name = Column(String(100), nullable=False, unique=True)
    predicted_home_score = Column(Integer, nullable=True)
    predicted_away_score = Column(Integer, nullable=True)
    points = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    match = relationship("Match", backref="predictions")


class PuzzleImage(Base):
    __tablename__ = "puzzle_game"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    filename = Column(String(255), nullable=False)
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())


class PuzzleScore(Base):
    __tablename__ = "puzzle_scores"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(100), nullable=False)
    points = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())


class QuizScore(Base):
    __tablename__ = "quiz_scores"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(100), nullable=False)
    points = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())


class QuizQuestion(Base):
    __tablename__ = "quiz_questions"

    id = Column(Integer, primary_key=True, index=True)
    question = Column(String, nullable=False)
    option_a = Column(String, nullable=False)
    option_b = Column(String, nullable=False)
    option_c = Column(String, nullable=False)
    option_d = Column(String, nullable=False)
    correct_option = Column(String(1), nullable=False)
    created_at = Column(DateTime, server_default=func.now())


class MemoryCard(Base):
    __tablename__ = "memory_cards"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    image_url = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class MemoryScore(Base):
    __tablename__ = "memory_scores"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(100), nullable=False)
    points = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())
