import shutil
from typing import List
from uuid import uuid4
from fastapi import FastAPI, File, HTTPException, Request, Form, UploadFile
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
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
import os
from typing import List
from supabase import StorageException, create_client
from utils import format_datetime_indo
from database import SessionLocal
from models import Berita, GalleryNobar, Match, TicketOrder
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

load_dotenv()

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="bigredsmantap", max_age=1800)

app.add_middleware(SessionMiddleware, secret_key="bigredsmantap")
app.mount("/static", StaticFiles(directory="frontend/static"), name="static")

templates = Jinja2Templates(directory="frontend")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


def datetimeformat(value, format="%d-%m-%Y"):
    if isinstance(value, str):
        try:
            value = datetime.fromisoformat(value)
        except:
            return value
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


@app.get("/form", response_class=HTMLResponse)
async def show_form(request: Request):
    return templates.TemplateResponse("form.html", {"request": request})


@app.post("/submit")
async def submit_form(
    nama: str = Form(...),
    status: str = Form(...),
    id_card: str = Form(None),
    jumlah: int = Form(...),
    whatsapp: str = Form(...),
    bukti_transfer: UploadFile = File(...),
    total_harga: str = Form(...),
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
    )
    db.add(new_order)
    db.commit()
    db.refresh(new_order)
    ticket_id = new_order.id

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
    footer_top = height - 140
    draw.line(
        [(margin, footer_top), (width - margin, footer_top)], fill="#999", width=2
    )
    footer_text = "Harap tunjukkan tiket ini\n ke petugas tiket"
    bbox = draw.multiline_textbbox((0, 0), footer_text, font=font_small, align="center")
    w = bbox[2] - bbox[0]
    h = bbox[3] - bbox[1]
    draw.multiline_text(
        ((width - w) / 2, footer_top + 30),
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

    total_items = db.query(func.count(TicketOrder.id)).scalar()
    total_pages = (total_items + per_page - 1) // per_page

    daftar_tiket = (
        db.query(TicketOrder)
        .order_by(TicketOrder.nama.asc())
        .offset(offset)
        .limit(per_page)
        .all()
    )

    total_pemesan = total_items

    # ✅ Hitung total pemasukan (gunakan func.sum untuk efisiensi)
    total_pemasukan = db.query(func.sum(TicketOrder.total_harga)).scalar() or 0

    return templates.TemplateResponse(
        "cms_tiket.html",
        {
            "request": request,
            "daftar_tiket": daftar_tiket,
            "current_page": page,
            "total_pages": total_pages,
            "total_pemesan": total_pemesan,
            "total_pemasukan": total_pemasukan,
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
    tanggal: str = Form(...),  # Tanggal dari input HTML
    kategori: str = Form(...),  # Tambahkan kategori
    image: List[UploadFile] = File(...),
):
    db: Session = SessionLocal()
    uploaded_urls = []

    try:
        tanggal_dt = datetime.strptime(tanggal, "%Y-%m-%dT%H:%M")
    except ValueError:
        return {"error": "Format tanggal tidak valid"}

    for media in image:
        ext = media.filename.split(".")[-1]
        filename = f"nobar/{uuid4()}.{ext}"
        content = await media.read()

        try:
            upload_res = supabase.storage.from_("nobar").upload(
                path=filename,
                file=content,
                file_options={"content-type": media.content_type},
            )
        except StorageException as e:
            print("UPLOAD ERROR:", e.message)
            continue

        media_url = f"{SUPABASE_URL}/storage/v1/object/public/nobar/{filename}"
        uploaded_urls.append(media_url)

        new_item = GalleryNobar(
            title=title,
            image_url=media_url,
            tanggal=tanggal_dt,
            kategori=kategori,  # simpan kategori
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
        print("❌ Gagal ambil data dari API:", e)
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
    print(f"✅ {inserted} berita baru disimpan. Waktu: {datetime.now()}")
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
