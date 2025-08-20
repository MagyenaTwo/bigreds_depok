from collections import defaultdict
import shutil
from typing import List
from uuid import uuid4
from fastapi import FastAPI, File, HTTPException, Query, Request, Form, UploadFile
from fastapi.responses import (
    FileResponse,
    HTMLResponse,
    JSONResponse,
    RedirectResponse,
    StreamingResponse,
)
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import httpx
import pytz
from sqlalchemy.orm import Session
from sqlalchemy import case, create_engine, func, select, union_all
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
import os
from typing import List
from supabase import StorageException, create_client
import models
from utils import format_datetime_indo
from database import SessionLocal
from models import (
    Berita,
    GalleryNobar,
    Game,
    Leaderboard,
    Match,
    PuzzleImage,
    PuzzleScore,
    QuizQuestion,
    ScorePrediction,
    TicketOrder,
)
from dotenv import load_dotenv
from starlette.middleware.sessions import SessionMiddleware
from fastapi import Depends
from werkzeug.security import check_password_hash
from models import User
from database import SessionLocal
from fastapi.responses import RedirectResponse
from werkzeug.security import generate_password_hash
from apscheduler.schedulers.background import BackgroundScheduler
import requests
from PIL import Image, ImageDraw, ImageFont
import io, qrcode
import random
import string
import cloudinary
import cloudinary.uploader

load_dotenv()

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="bigredsmantap", max_age=1800)

app.add_middleware(SessionMiddleware, secret_key="bigredsmantap")
app.mount("/static", StaticFiles(directory="frontend/static"), name="static")

templates = Jinja2Templates(directory="frontend")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
FONNTE_TOKEN = os.getenv("FONNTE_TOKEN")

cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
)


def datetimeformat(value, format="%d-%m-%Y %H:%M"):
    if isinstance(value, str):
        try:
            value = datetime.fromisoformat(value)
        except:
            return value

    # Jika datetime tanpa timezone (naive), anggap dari UTC
    if value.tzinfo is None:
        value = value.replace(tzinfo=pytz.UTC)

    # Konversi ke WIB
    wib = pytz.timezone("Asia/Jakarta")
    value = value.astimezone(wib)

    return value.strftime(format)


templates.env.filters["datetimeformat"] = datetimeformat


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def versioned_filter(filename):
    filepath = os.path.join("static", filename)
    if os.path.exists(filepath):
        timestamp = int(os.path.getmtime(filepath))
        return f"/static/{filename}?v={timestamp}"
    return f"/static/{filename}"


templates.env.filters["versioned"] = versioned_filter


def format_rupiah(value):
    if value is None:
        return "Rp 0"
    try:
        return "Rp {:,}".format(int(value)).replace(",", ".")
    except (ValueError, TypeError):
        return "Rp 0"


# Daftarkan filter ke environment Jinja2
templates.env.filters["rupiah"] = format_rupiah


@app.get("/robots.txt")
def robots():
    return FileResponse(os.path.join(os.path.dirname(__file__), "robots.txt"))


@app.get("/sitemap.xml")
def sitemap():
    return FileResponse(os.path.join(os.path.dirname(__file__), "sitemap.xml"))


@app.get("/", response_class=HTMLResponse)
async def read_form(request: Request):
    db: Session = SessionLocal()

    now = datetime.now()
    match = (
        db.query(Match)
        .filter(Match.match_datetime >= now)
        .order_by(Match.match_datetime.asc())
        .first()
    )
    berita_terbaru = (
        db.query(Berita).order_by(Berita.publish_date.desc()).limit(5).all()
    )
    db.close()

    formatted_datetime = format_datetime_indo(match.match_datetime) if match else None

    # Ambil galeri nobar dari Supabase (limit 6 terbaru)
    gallery_data = (
        supabase.table("gallery_nobar")
        .select("*")
        .in_("kategori", ["matchday", "event"])
        .order("tanggal", desc=True)
        .limit(10)
        .execute()
    )

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "match": match,
            "formatted_datetime": formatted_datetime,
            "gallery_items": gallery_data.data,
            "berita_items": berita_terbaru,
        },
    )


@app.get("/buy-ticket", response_class=HTMLResponse)
async def show_form(request: Request):
    db: Session = SessionLocal()
    now = datetime.now()
    match = (
        db.query(Match)
        .filter(Match.match_datetime >= now)
        .order_by(Match.match_datetime.asc())
        .first()
    )
    formatted_datetime = format_datetime_indo(match.match_datetime) if match else None
    db.close()

    return templates.TemplateResponse(
        "form.html",
        {
            "request": request,
            "match": match,
            "formatted_datetime": formatted_datetime,
            "datetime_now": now,
        },
    )


@app.post("/submit")
async def submit_form(
    nama: str = Form(...),
    status: str = Form(...),
    id_card: str = Form(None),
    jumlah: int = Form(...),
    whatsapp: str = Form(...),
    bukti_transfer: UploadFile = File(...),
    total_harga: str = Form(...),
    metode_pembayaran: str = Form(...),
):
    ext = bukti_transfer.filename.split(".")[-1]
    filename_bukti = f"bukti/{uuid4()}.{ext}"
    content = await bukti_transfer.read()

    supabase.storage.from_("bukti").upload(
        path=filename_bukti,
        file=content,
        file_options={"content-type": bukti_transfer.content_type},
    )
    bukti_url = f"{SUPABASE_URL}/storage/v1/object/public/bukti/{filename_bukti}"

    db: Session = SessionLocal()
    new_order = TicketOrder(
        nama=nama,
        status=status,
        id_card=id_card if status == "member" else None,
        jumlah=jumlah,
        whatsapp=whatsapp,
        bukti_transfer_url=bukti_url,
        total_harga=total_harga,
        metode_pembayaran=metode_pembayaran,
    )
    db.add(new_order)
    db.commit()
    db.refresh(new_order)

    ticket_id = new_order.id

    def generate_alias(length=8):
        return "".join(random.choices(string.ascii_letters + string.digits, k=length))

    # Generate alias dan update tiket
    alias = generate_alias()
    db.query(TicketOrder).filter(TicketOrder.id == ticket_id).update(
        {"alias_url": alias}
    )
    db.commit()

    width, height = 600, 900
    img = Image.new("RGB", (width, height), color="#fdfdfc")
    draw = ImageDraw.Draw(img)

    try:
        font_title = ImageFont.truetype("frontend/static/fonts/DejaVuSans-Bold.ttf", 42)
        font_text = ImageFont.truetype("frontend/static/fonts/DejaVuSans.ttf", 28)
        font_small = ImageFont.truetype("frontend/static/fonts/DejaVuSans.ttf", 24)

    except:
        font_title = ImageFont.load_default()
        font_text = ImageFont.load_default()
        font_small = ImageFont.load_default()

    margin = 20
    draw.rectangle(
        [(margin, margin), (width - margin, height - margin)], outline="#999", width=3
    )

    # HEADER
    logo_size = 120
    try:
        logo_header = Image.open("frontend/static/img/logo.jpeg").resize(
            (logo_size, logo_size)
        )
        img.paste(logo_header, (width // 2 - 250, 50))
    except:
        pass
    draw.text(
        (width // 2 - 120, 80),
        "TIKET NOBAR\nBIGREDS DEPOK",
        fill="black",
        font=font_title,
        align="center",
    )

    header_bottom = 200
    draw.line(
        [(margin, header_bottom), (width - margin, header_bottom)], fill="#999", width=2
    )

    # INFO
    info_y = header_bottom + 40
    label_x = 60
    value_x = 240
    line_gap = 60

    draw.text((label_x, info_y), "Nama", fill="black", font=font_text)
    draw.text((label_x + 100, info_y), f": {nama}", fill="black", font=font_text)

    draw.text((label_x, info_y + line_gap), "Status", fill="black", font=font_text)
    draw.text(
        (label_x + 100, info_y + line_gap), f": {status}", fill="black", font=font_text
    )

    draw.text((label_x, info_y + line_gap * 2), "Jumlah", fill="black", font=font_text)
    draw.text(
        (label_x + 100, info_y + line_gap * 2),
        f": {jumlah} tiket",
        fill="black",
        font=font_text,
    )

    # Logo kecil di bawah jumlah
    try:
        logo_bottom = Image.open("static/img/logo.jpeg").resize((120, 120))
        logo_x = label_x + 40
        logo_y = info_y + line_gap * 2 + 80
        img.paste(logo_bottom, (logo_x, logo_y))
    except:
        pass

        # QR CODE posisinya di kanan sejajar info
    qr_data = f"TiketID:{ticket_id}|Nama:{nama}|Status:{status}|Jumlah:{jumlah}"
    qr = qrcode.QRCode(box_size=8, border=2)
    qr.add_data(qr_data)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white").resize((260, 260))

    qr_x = width - margin - 400
    qr_y = info_y + 200  # sejajar dengan nama
    img.paste(qr_img, (qr_x, qr_y))

    # LOGO BAWAH
    try:
        logo_bottom = Image.open("static/img/logo.jpeg").resize((180, 180))
        img.paste(logo_bottom, (margin + 40, qr_y))
    except:
        pass
    # FOOTER
    footer_top = height - 160
    draw.line(
        [(margin, footer_top), (width - margin, footer_top)], fill="#999", width=2
    )

    # Footer Text
    footer_text = (
        "Harap tunjukkan tiket ini\n"
        "kepada petugas tiket di lokasi acara.\n\n"
        "www.bigredsdepok.com"
    )

    bbox = draw.multiline_textbbox((0, 0), footer_text, font=font_small, align="center")
    w = bbox[2] - bbox[0]
    h = bbox[3] - bbox[1]
    draw.multiline_text(
        ((width - w) / 2, footer_top + 20),
        footer_text,
        fill="black",
        font=font_small,
        align="center",
    )

    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    filename_tiket = (
        f"qr/tiket_{ticket_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}.png"
    )

    supabase.storage.from_("tiket").upload(
        path=filename_tiket,
        file=buffer.getvalue(),
        file_options={"content-type": "image/png"},
    )
    ticket_url = f"{SUPABASE_URL}/storage/v1/object/public/tiket/{filename_tiket}"

    db.query(TicketOrder).filter(TicketOrder.id == ticket_id).update(
        {"tiket_filename": filename_tiket, "tiket_url": ticket_url}
    )
    db.commit()
    db.close()

    return JSONResponse({"status": "success", "tiket_url": ticket_url})


@app.get("/ticket/{ticket_id}")
def get_ticket(ticket_id: int):
    db = SessionLocal()
    order = db.query(TicketOrder).filter(TicketOrder.id == ticket_id).first()
    db.close()

    if not order or not order.tiket_file:
        raise HTTPException(status_code=404, detail="Tiket tidak ditemukan")

    return StreamingResponse(
        io.BytesIO(order.tiket_file),
        media_type="image/png",
        headers={
            "Content-Disposition": f'attachment; filename="{order.tiket_filename}"'
        },
    )


@app.get("/cms")
def cms_page(request: Request, page: int = 1):
    if not request.session.get("user_id"):
        return RedirectResponse(url="/login", status_code=302)

    per_page = 20
    start = (page - 1) * per_page
    end = start + per_page - 1

    # Ambil total jumlah data
    total_res = supabase.table("gallery_nobar").select("id", count="exact").execute()
    total_count = total_res.count or 0
    total_pages = (total_count + per_page - 1) // per_page

    # Ambil data sesuai range
    data = (
        supabase.table("gallery_nobar")
        .select("*")
        .order("tanggal", desc=True)
        .range(start, end)
        .execute()
    )

    return templates.TemplateResponse(
        "cms.html",
        {
            "request": request,
            "images": data.data,
            "current_page": page,
            "total_pages": total_pages,
        },
    )


@app.get("/login", response_class=HTMLResponse)
async def login_get(request: Request):
    return templates.TemplateResponse("login.html", {"request": request, "error": None})


@app.post("/login", response_class=HTMLResponse)
async def login_post(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.username == username).first()
    if user and check_password_hash(user.password, password):
        request.session["user_id"] = user.id
        return RedirectResponse(url="/cms/tiket", status_code=302)
    return templates.TemplateResponse(
        "login.html", {"request": request, "error": "Username atau password salah."}
    )


@app.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/login", status_code=302)


@app.get("/cms/tiket")
def halaman_tiket(request: Request, page: int = 1, db: Session = Depends(get_db)):
    if not request.session.get("user_id"):
        return RedirectResponse(url="/login", status_code=302)

    per_page = 20
    offset = (page - 1) * per_page

    total_items = db.query(func.sum(TicketOrder.jumlah)).scalar() or 0
    total_pages = (total_items + per_page - 1) // per_page

    daftar_tiket = (
        db.query(TicketOrder)
        .order_by(TicketOrder.created_at.desc())
        .offset(offset)
        .limit(per_page)
        .all()
    )

    total_pemesan = total_items

    # ✅ Hitung total pemasukan (gunakan func.sum untuk efisiensi)
    total_pemasukan = db.query(func.sum(TicketOrder.total_harga)).scalar() or 0
    total_gopay = (
        db.query(func.sum(TicketOrder.total_harga))
        .filter(TicketOrder.metode_pembayaran == "gopay")
        .scalar()
        or 0
    )
    total_bni = (
        db.query(func.sum(TicketOrder.total_harga))
        .filter(TicketOrder.metode_pembayaran == "bank_transfer")
        .scalar()
        or 0
    )
    return templates.TemplateResponse(
        "cms_tiket.html",
        {
            "request": request,
            "daftar_tiket": daftar_tiket,
            "current_page": page,
            "total_pages": total_pages,
            "total_pemesan": total_pemesan,
            "total_pemasukan": total_pemasukan,
            "total_gopay": total_gopay,
            "total_bni": total_bni,
        },
    )


@app.get("/proxy/news/{slug}")
async def proxy_news(slug: str):
    url = f"https://backend.liverpoolfc.com/lfc-rest-api/id/news/{slug}"

    async with httpx.AsyncClient() as client:
        try:
            res = await client.get(url)
            res.raise_for_status()
        except httpx.HTTPError as e:
            return JSONResponse(
                status_code=500, content={"error": "Gagal mengambil berita."}
            )

    return JSONResponse(content=res.json())


@app.get("/cms/laporan", response_class=HTMLResponse)
async def cms_laporan(request: Request):
    if not request.session.get("user_id"):
        return RedirectResponse(url="/login", status_code=302)

    return templates.TemplateResponse("cms_laporan.html", {"request": request})


@app.get("/cms/berita", response_class=HTMLResponse)
async def cms_berita(request: Request):
    if not request.session.get("user_id"):
        return RedirectResponse(url="/login", status_code=302)

    return templates.TemplateResponse("cms_berita.html", {"request": request})


@app.get("/cms/akun")
def form_akun(request: Request):
    if not request.session.get("user_id"):
        return RedirectResponse(url="/login", status_code=302)

    return templates.TemplateResponse("cms_akun.html", {"request": request})


@app.post("/cms/akun", response_class=HTMLResponse)
async def buat_akun_post(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    if not request.session.get("user_id"):
        return RedirectResponse(url="/login", status_code=302)

    existing_user = db.query(User).filter(User.username == username).first()
    if existing_user:
        return templates.TemplateResponse(
            "cms_akun.html",
            {"request": request, "error": "Username sudah digunakan. Coba yang lain."},
        )

    hashed_password = generate_password_hash(password)
    new_user = User(username=username, password=hashed_password)
    db.add(new_user)
    db.commit()

    return templates.TemplateResponse(
        "cms_akun.html", {"request": request, "success": "Akun berhasil dibuat!"}
    )


@app.post("/cms/upload")
async def upload_gallery_nobar(
    title: str = Form(...),
    tanggal: str = Form(...),
    kategori: str = Form(...),
    deskripsi: str = Form(...),
    image: List[UploadFile] = File(...),
):
    db: Session = SessionLocal()
    uploaded_urls = []

    try:
        tanggal_dt = datetime.strptime(tanggal, "%Y-%m-%dT%H:%M")
    except ValueError:
        return {"error": "Format tanggal tidak valid"}

    for media in image:
        file_bytes = await media.read()

        try:
            upload_res = cloudinary.uploader.upload(
                file_bytes, public_id=f"nobar/{uuid4()}", resource_type="auto"
            )
        except Exception as e:
            continue

        media_url = upload_res.get("secure_url")
        uploaded_urls.append(media_url)

        new_item = GalleryNobar(
            title=title,
            image_url=media_url,
            tanggal=tanggal_dt,
            kategori=kategori,
            deskripsi=deskripsi,
        )
        db.add(new_item)

    db.commit()
    db.close()

    return RedirectResponse(url="/cms", status_code=303)


@app.get("/pengurus", response_class=HTMLResponse)
async def pengurus(request: Request):
    return templates.TemplateResponse("pengurus.html", {"request": request})


@app.get("/gallery", response_class=HTMLResponse)
async def gallery(request: Request):
    db: Session = SessionLocal()
    images = db.query(GalleryNobar).order_by(GalleryNobar.tanggal.desc()).all()
    db.close()
    categories = list({img.kategori for img in images if img.kategori})

    return templates.TemplateResponse(
        "gallery.html", {"request": request, "images": images, "categories": categories}
    )


# Fungsi utama untuk sinkronisasi berita
def fetch_and_save_news():
    url = "https://backend.liverpoolfc.com/lfc-rest-api/id/news"
    headers = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}

    try:
        res = requests.get(url, headers=headers)
        data = res.json()
    except Exception as e:
        return 0

    db: Session = SessionLocal()
    inserted = 0

    for item in data.get("results", []):
        slug = item["slug"]
        exists = db.query(Berita).filter_by(slug=slug).first()
        if exists:
            continue

        berita = Berita(
            slug=slug,
            title=item["title"],
            content=item.get("byline", ""),
            cover_image=item.get("coverImage", {})
            .get("sizes", {})
            .get("md", {})
            .get("url"),
            publish_date=item.get("publishedAt"),
        )
        db.add(berita)
        inserted += 1

    db.commit()
    db.close()
    return inserted


# Endpoint manual
@app.get("/sync-news")
def sync_news():
    inserted = fetch_and_save_news()
    return {"message": f"✅ {inserted} berita baru disimpan."}


# Scheduler otomatis
scheduler = BackgroundScheduler(timezone=pytz.timezone("Asia/Jakarta"))
scheduler.add_job(fetch_and_save_news, "cron", hour=8, minute=0)
scheduler.start()


@app.get("/")
def root():
    return {"message": "API Berita BIGREDS aktif ✅"}


@app.get("/cek_member")
def cek_member(nama: str):
    db: Session = SessionLocal()
    existing = (
        db.query(TicketOrder)
        .filter(TicketOrder.nama.ilike(nama), TicketOrder.status == "member")
        .order_by(TicketOrder.id.desc())
        .first()
    )
    db.close()

    if existing and existing.id_card:
        return {"found": True, "id_card": existing.id_card}
    return {"found": False}


@app.get("/validate_ticket")
async def validate_ticket(q: str):
    db: Session = SessionLocal()

    try:
        data = dict(item.split(":", 1) for item in q.split("|"))
        ticket_id = int(data.get("TiketID", -1))

        order = db.query(TicketOrder).filter(TicketOrder.id == ticket_id).first()

        if not order:
            return JSONResponse({"status": "Tiket tidak ditemukan"}, status_code=404)

        # Cek apakah sudah dipakai maksimal
        if order.jumlah_terpakai >= order.jumlah:
            return JSONResponse(
                {"status": "Tiket sudah habis dipakai"}, status_code=403
            )

        # Tambah jumlah terpakai
        order.jumlah_terpakai += 1
        db.commit()

        return JSONResponse(
            {
                "status": "Tiket valid",
                "nama": order.nama,
                "status_pengguna": order.status,
                "jumlah": order.jumlah,
                "dipakai_ke": order.jumlah_terpakai,
            }
        )

    except Exception as e:
        return JSONResponse({"status": f"Error: {str(e)}"}, status_code=400)
    finally:
        db.close()


@app.get("/scan")
def serve_scan_page():
    return FileResponse("frontend/scan.html", media_type="text/html")


@app.post("/update-status/{tiket_id}")
def update_status(tiket_id: int, db: Session = Depends(get_db)):
    tiket = db.query(TicketOrder).filter(TicketOrder.id == tiket_id).first()
    if not tiket:
        raise HTTPException(status_code=404, detail="Tiket tidak ditemukan")

    tiket.sudah_dikirim = True
    db.commit()
    db.refresh(tiket)
    return {"success": True}


@app.post("/kirim-tiket/{tiket_id}")
def kirim_tiket(tiket_id: int, db: Session = Depends(get_db)):
    tiket = db.query(TicketOrder).filter(TicketOrder.id == tiket_id).first()
    if not tiket:
        raise HTTPException(status_code=404, detail="Tiket tidak ditemukan")

    pesan = f"""*🔴 BIGREDS DEPOK 🔴*

Hallo *{tiket.nama}* 👋
Terima kasih telah melakukan pembelian tiket *NOBAR* Bigreds Depok.

📄 *Detail Tiket Anda:*
• _Status_: *{tiket.status.capitalize()}*
• _Jumlah Tiket_: *{tiket.jumlah}*
• _Total Pembayaran_: *Rp {tiket.total_harga:,.0f}*
• _Tiket Nobar_: https://bigredsdepok.com/tiket/{tiket.alias_url}
🔁 *Jangan lupa tunjukkan tiket ini saat masuk lokasi ke penjaga tiket.*

_Ayu Tingting makan pisang gepok._
_Siapa kamu gak penting, yang penting kita Kopites dari Depok!_

www.bigredsdepok.com"""

    response = requests.post(
        "https://api.fonnte.com/send",
        headers={"Authorization": FONNTE_TOKEN},
        data={
            "target": f"62{tiket.whatsapp[1:]}",
            "message": pesan,
        },
    )

    try:
        res_data = response.json()
    except Exception:
        res_data = {"error": response.text}

    if not res_data.get("status", True):
        raise HTTPException(
            status_code=500, detail=f"Gagal mengirim WhatsApp: {res_data}"
        )

    if response.status_code != 200:
        raise HTTPException(status_code=500, detail="Gagal mengirim WhatsApp")

    tiket.sudah_dikirim = True
    db.commit()

    return {"success": True}


@app.get("/tiket/{alias}")
def tiket_proxy(alias: str, db: Session = Depends(get_db)):
    tiket = db.query(TicketOrder).filter(TicketOrder.alias_url == alias).first()
    if not tiket:
        raise HTTPException(status_code=404, detail="Tiket tidak ditemukan")

    url_asli = tiket.tiket_url

    r = httpx.get(url_asli)
    if r.status_code != 200:
        raise HTTPException(status_code=404, detail="Gambar tiket tidak ditemukan")

    return StreamingResponse(io.BytesIO(r.content), media_type="image/png")


@app.get("/events", response_class=HTMLResponse)
async def events(request: Request):
    db: Session = SessionLocal()
    images = (
        db.query(GalleryNobar)
        .filter(GalleryNobar.kategori == "event")
        .order_by(GalleryNobar.id.asc())  # urut berdasarkan id terkecil dulu
        .all()
    )

    unique_events_dict = {}
    for img in images:
        if img.title not in unique_events_dict:
            unique_events_dict[img.title] = img

    unique_events = list(unique_events_dict.values())

    db.close()

    categories = list({img.kategori for img in unique_events if img.kategori})

    return templates.TemplateResponse(
        "events.html",
        {
            "request": request,
            "images": unique_events,
            "categories": categories,
            "now": datetime.now(),
        },
    )


@app.get("/event-details")
async def event_details(title: str = Query(...)):
    db: Session = SessionLocal()
    events = db.query(GalleryNobar).filter(GalleryNobar.title == title).all()
    db.close()

    if not events:
        return JSONResponse(
            status_code=404, content={"message": "Event tidak ditemukan"}
        )
    deskripsi = events[0].deskripsi if events[0].deskripsi else None

    images = [{"image_url": ev.image_url} for ev in events]

    return {
        "title": title,
        "deskripsi": deskripsi,
        "images": images,
    }


@app.post("/cms/delete/{event_id}")
async def delete_event(event_id: int):
    db: Session = SessionLocal()
    try:
        event = db.query(GalleryNobar).filter(GalleryNobar.id == event_id).first()
        if not event:
            return {"error": "Event tidak ditemukan"}

        db.delete(event)
        db.commit()
        return RedirectResponse(url="/cms", status_code=303)
    except Exception as e:
        db.rollback()
        return {"error": str(e)}
    finally:
        db.close()


@app.get("/fans-corner")
def fans_corner(request: Request, db: Session = Depends(get_db)):
    has_open = db.query(Game).filter(Game.status == "open").count() > 0

    if has_open:
        games = (
            db.query(Game)
            .order_by(case((Game.status == "open", 0), else_=1), Game.id.asc())
            .all()
        )
    else:
        games = db.query(Game).order_by(Game.id.asc()).all()

    # --- gabungan ScorePrediction + PuzzleScore ---
    q1 = select(
        func.lower(ScorePrediction.full_name).label("full_name"), ScorePrediction.points
    )
    q2 = select(
        func.lower(PuzzleScore.full_name).label("full_name"), PuzzleScore.points
    )

    union_q = union_all(q1, q2).subquery()

    total_points = (
        db.query(union_q.c.full_name, func.sum(union_q.c.points).label("points"))
        .group_by(union_q.c.full_name)
        .order_by(func.sum(union_q.c.points).desc())
        .limit(10)
        .all()
    )

    leaderboard = [
        {"name": name.title(), "score": points} for name, points in total_points
    ]

    return templates.TemplateResponse(
        "fans_corner.html",
        {
            "request": request,
            "games": games,
            "leaderboard": leaderboard,
        },
    )


@app.post("/leaderboard")
def add_leaderboard(
    name: str = Query(...), score: int = Query(...), db: Session = Depends(get_db)
):
    entry = Leaderboard(name=name, score=score)
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return {"message": "Score berhasil disimpan"}


@app.get("/cms/games")
def admin_games(request: Request, db: Session = Depends(get_db)):
    if not request.session.get("user_id"):
        return RedirectResponse(url="/login", status_code=302)

    games = db.query(Game).order_by(Game.id.asc()).all()
    predictions = db.query(ScorePrediction).all()
    matches = db.query(Match).order_by(Match.match_datetime.asc()).all()
    total_points = (
        db.query(
            func.lower(ScorePrediction.full_name).label("full_name"),
            func.sum(ScorePrediction.points).label("points"),
        )
        .group_by(func.lower(ScorePrediction.full_name))
        .all()
    )

    # Biar tampilannya rapi, convert ke list dict dan title-case namanya
    total_points_list = [
        {"full_name": name.title(), "points": pts} for name, pts in total_points
    ]

    return templates.TemplateResponse(
        "cms_games.html",
        {
            "request": request,
            "games": games,
            "predictions": predictions,
            "matches": matches,
            "total_points": total_points_list,
        },
    )


@app.post("/cms/games/{game_id}/toggle")
def toggle_game(game_id: int, db: Session = Depends(get_db)):
    game = db.query(Game).filter(Game.id == game_id).first()
    if game:
        game.status = "open" if game.status == "locked" else "locked"
        db.commit()

        return RedirectResponse(url="/cms/games", status_code=303)
    return RedirectResponse(url="/cms/games", status_code=303)


@app.post("/fans-corner/check-or-save-name")
def check_or_save_name(
    game_key: str = Form(...), name: str = Form(...), db: Session = Depends(get_db)
):
    existing = (
        db.query(Leaderboard)
        .filter(Leaderboard.game_key == game_key, Leaderboard.name == name)
        .first()
    )

    if existing:
        return {"exists": True}
    entry = Leaderboard(game_key=game_key, name=name, score=0)
    db.add(entry)
    db.commit()

    return {"exists": False}


@app.get("/games/{game_key}")
def get_game(game_key: str):
    file_path = os.path.join("frontend", f"{game_key}.html")
    if not os.path.exists(file_path):
        return {"error": "File not found"}
    return FileResponse(file_path)


@app.get("/api/match")
def get_match():
    db: Session = SessionLocal()
    now = datetime.now()
    match = (
        db.query(Match)
        .filter(Match.match_datetime >= now)
        .order_by(Match.match_datetime.asc())
        .first()
    )
    db.close()

    if not match:
        return {"error": "No upcoming match found"}

    return {
        "id": match.id,
        "home_team": match.home_team,
        "away_team": match.away_team,
        "competition": match.competition,
        "datetime": format_datetime_indo(match.match_datetime),
    }


@app.post("/api/prediction")
async def create_prediction(request: Request, db: Session = Depends(get_db)):
    try:
        data = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON format")

    required_fields = [
        "match_id",
        "full_name",
        "predicted_home_score",
        "predicted_away_score",
    ]
    for field in required_fields:
        if field not in data:
            raise HTTPException(status_code=400, detail=f"Missing field: {field}")

    match = db.query(Match).filter(Match.id == data["match_id"]).first()
    if not match:
        raise HTTPException(status_code=404, detail="Match tidak ditemukan")

    # Konversi ke WIB
    wib = pytz.timezone("Asia/Jakarta")
    now_wib = datetime.now(wib)

    match_dt = match.match_datetime
    if match_dt.tzinfo is None:
        match_dt = pytz.UTC.localize(match_dt)  # Anggap UTC jika tanpa timezone
    match_time_wib = match_dt.astimezone(wib)

    # Cutoff waktu
    cutoff_before = match_time_wib - timedelta(hours=1)
    cutoff_after = match_time_wib + timedelta(hours=2)

    if cutoff_before <= now_wib <= cutoff_after:
        raise HTTPException(
            status_code=400,
            detail="Tebak skor sudah ditutup mulai 1 jam sebelum hingga 2 jam setelah pertandingan",
        )

    # Cek prediksi sebelumnya
    existing = (
        db.query(ScorePrediction)
        .filter(
            ScorePrediction.match_id == data["match_id"],
            func.lower(ScorePrediction.full_name) == data["full_name"].lower(),
        )
        .first()
    )

    if existing:
        raise HTTPException(status_code=400, detail="Anda sudah mengirim Tebak Skor")

    # Simpan prediksi baru
    new_pred = ScorePrediction(
        match_id=data["match_id"],
        full_name=data["full_name"],
        predicted_home_score=data["predicted_home_score"],
        predicted_away_score=data["predicted_away_score"],
    )

    db.add(new_pred)
    db.commit()
    db.refresh(new_pred)

    return {"status": "success", "prediction_id": new_pred.id}


@app.post("/cms/matches/{match_id}/set_score")
def set_match_score(
    match_id: int,
    home_score: int = Form(...),
    away_score: int = Form(...),
    db: Session = Depends(get_db),
):
    # 1. Update skor pertandingan
    match = db.query(Match).filter(Match.id == match_id).first()
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")

    match.actual_home_score = home_score
    match.actual_away_score = away_score
    db.commit()

    predictions = db.query(ScorePrediction).all()
    for pred in predictions:
        if (
            pred.match.actual_home_score is not None
            and pred.match.actual_away_score is not None
        ):
            if (
                pred.predicted_home_score == pred.match.actual_home_score
                and pred.predicted_away_score == pred.match.actual_away_score
            ):
                pred.points = 10
            else:
                pred.points = 0
    db.commit()

    return RedirectResponse(url="/cms/games", status_code=302)


@app.get("/cms/games/puzzle", response_class=HTMLResponse)
async def get_upload_puzzle(request: Request):
    return templates.TemplateResponse("cms_puzzle.html", {"request": request})


@app.post("/cms/games/puzzle")
async def post_upload_puzzle(
    request: Request,
    title: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    try:
        # upload ke cloudinary
        result = cloudinary.uploader.upload(file.file, folder="puzzle_images")
        filename = result.get("public_id")
        image_url = result.get("secure_url")

        # simpan ke database
        new_image = PuzzleImage(title=title, filename=filename)
        db.add(new_image)
        db.commit()
        db.refresh(new_image)

        return templates.TemplateResponse(
            "cms_puzzle.html",
            {"request": request, "success": True, "filename": filename},
        )
    except Exception as e:
        return templates.TemplateResponse(
            "cms_puzzle.html", {"request": request, "error": str(e)}
        )


@app.get("/api/puzzle_images")
def get_puzzle_images():
    db: Session = SessionLocal()
    images = db.query(PuzzleImage).all()
    result = []
    for img in images:
        image_url = f"https://res.cloudinary.com/{cloudinary.config().cloud_name}/image/upload/c_fill,w_450,h_450/{img.filename}.jpg"
        result.append({"id": img.id, "title": img.title, "image_url": image_url})
    return JSONResponse(result)


@app.post("/api/claim_puzzle_point")
def claim_puzzle_point(full_name: str = Form(...), db: Session = Depends(get_db)):
    existing = (
        db.query(PuzzleScore).filter(PuzzleScore.full_name.ilike(full_name)).first()
    )
    if existing:
        return {
            "message": f"❌ Nama {full_name} sudah pernah klaim poin, tidak bisa main lagi.",
            "total_points": existing.points,
        }
    new_score = PuzzleScore(full_name=full_name, points=10)
    db.add(new_score)
    db.commit()
    db.refresh(new_score)

    return {
        "message": f"✅ Poin berhasil ditambahkan untuk {full_name}",
        "total_points": new_score.points,
    }


@app.get("/games/penalti", response_class=HTMLResponse)
async def penalti_game():
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <title>Game Penalti</title>
      <style>
        body {
          font-family: Arial, sans-serif;
          text-align: center;
          background-color: #4caf50;
          margin: 0;
          padding: 0;
        }

        .game-container {
          max-width: 400px;
          margin: 0 auto;
          padding: 20px;
        }

        .field {
          position: relative;
          width: 100%;
          height: 300px;
          margin: 20px 0;
          background-color: #87ceeb;
          border: 2px solid #fff;
          border-radius: 10px;
          overflow: hidden;
        }

        .goal {
          position: absolute;
          bottom: 0;
          left: 50%;
          transform: translateX(-50%);
          width: 80%;
        }

        .keeper {
          position: absolute;
          bottom: 40px;
          left: 50%;
          transform: translateX(-50%);
          width: 60px;
          transition: left 0.5s;
        }

        .player {
          position: absolute;
          bottom: 0;
          left: 50%;
          transform: translateX(-50%);
          width: 60px;
        }

        .controls button {
          margin: 10px;
          padding: 10px 20px;
          font-size: 16px;
          cursor: pointer;
        }

        #result {
          font-size: 18px;
          margin-top: 15px;
          font-weight: bold;
        }
      </style>
    </head>
    <body>
      <div class="game-container">
        <h2>Penalti Challenge</h2>
        <div class="field">
          <img src="https://via.placeholder.com/300x100?text=Goal" alt="Gawang" class="goal">
          <img src="https://via.placeholder.com/60x60?text=Keeper" alt="Kiper" class="keeper" id="keeper">
          <img src="https://via.placeholder.com/60x60?text=Player" alt="Pemain" class="player" id="player">
        </div>
        <div class="controls">
          <button onclick="shoot('left')">Kiri</button>
          <button onclick="shoot('center')">Tengah</button>
          <button onclick="shoot('right')">Kanan</button>
        </div>
        <div id="result"></div>
      </div>

      <script>
        function shoot(direction) {
          const keeper = document.getElementById('keeper');
          const result = document.getElementById('result');

          const keeperMoves = ['left', 'center', 'right'];
          const randomMove = keeperMoves[Math.floor(Math.random() * keeperMoves.length)];

          if (randomMove === 'left') keeper.style.left = '20%';
          if (randomMove === 'center') keeper.style.left = '50%';
          if (randomMove === 'right') keeper.style.left = '80%';

          if (direction === randomMove) {
            result.innerText = "❌ Kiper Menangkap Bola!";
          } else {
            result.innerText = "⚽ Gol!";
          }
        }
      </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


@app.get("/cms/games/trivia")
def cms_quiz(request: Request, db: Session = Depends(get_db)):
    questions = db.query(QuizQuestion).order_by(QuizQuestion.id.desc()).all()
    return templates.TemplateResponse(
        "cms_trivia.html",
        {"request": request, "questions": questions},
    )


@app.get("/cms/quiz/add", name="add_quiz_page")
def add_quiz_page(request: Request):
    return templates.TemplateResponse("add_quiz.html", {"request": request})


# Proses simpan soal
@app.post("/cms/quiz/add", name="add_quiz")
def add_quiz(
    request: Request,
    question: str = Form(...),
    option_a: str = Form(...),
    option_b: str = Form(...),
    option_c: str = Form(...),
    option_d: str = Form(...),
    correct_option: str = Form(...),
    db: Session = Depends(get_db),
):
    new_q = QuizQuestion(
        question=question,
        option_a=option_a,
        option_b=option_b,
        option_c=option_c,
        option_d=option_d,
        correct_option=correct_option.upper(),
    )
    db.add(new_q)
    db.commit()
    db.refresh(new_q)
    # redirect balik ke daftar soal
    return RedirectResponse(url=request.url_for("cms_quiz"), status_code=303)


@app.post("/cms/games/trivia/delete/{quiz_id}")
def delete_quiz(quiz_id: int, db: Session = Depends(get_db)):
    quiz = db.query(QuizQuestion).filter(QuizQuestion.id == quiz_id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Soal tidak ditemukan")

    db.delete(quiz)
    db.commit()
    return RedirectResponse(url="/cms/games/trivia", status_code=303)


@app.get("/api/trivia")
def get_trivia(db: Session = Depends(get_db)):
    questions = db.query(QuizQuestion).all()
    if len(questions) > 5:
        questions = random.sample(questions, 5)

    questions_list = [
        {
            "id": q.id,
            "question": q.question,
            "option_a": q.option_a,
            "option_b": q.option_b,
            "option_c": q.option_c,
            "option_d": q.option_d,
            "correct_option": q.correct_option,
        }
        for q in questions
    ]
    return JSONResponse(content=questions_list)
