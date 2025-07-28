import shutil
from typing import List
from uuid import uuid4
from fastapi import FastAPI, File, Request, Form, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
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
    request: Request,
    nama: str = Form(...),
    status: str = Form(...),
    id_card: str = Form(None),
    jumlah: int = Form(...),
    whatsapp: str = Form(...),
    bukti_transfer: UploadFile = File(...),
):
    ext = bukti_transfer.filename.split(".")[-1]
    filename = f"bukti/{uuid4()}.{ext}"
    content = await bukti_transfer.read()

    upload_res = supabase.storage.from_("bukti").upload(
        path=filename,
        file=content,
        file_options={"content-type": bukti_transfer.content_type},
    )

    bukti_url = f"{SUPABASE_URL}/storage/v1/object/public/bukti/{filename}"

    # 2. Simpan data ke DB
    db: Session = SessionLocal()
    new_order = TicketOrder(
        nama=nama,
        status=status,
        id_card=id_card if status == "member" else None,
        jumlah=jumlah,
        whatsapp=whatsapp,
        bukti_transfer_url=bukti_url,
    )
    db.add(new_order)
    db.commit()
    db.refresh(new_order)
    db.close()

    # 3. Redirect ke halaman QR atau sukses
    return RedirectResponse(url="/success", status_code=302)


@app.get("/success", response_class=HTMLResponse)
async def success_page(request: Request):
    return templates.TemplateResponse("sukses.html", {"request": request})


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

    return templates.TemplateResponse(
        "cms_tiket.html",
        {
            "request": request,
            "daftar_tiket": daftar_tiket,
            "current_page": page,
            "total_pages": total_pages,
            "total_pemesan": total_pemesan,
        },
    )


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
    image: List[UploadFile] = File(...),
):
    db: Session = SessionLocal()
    uploaded_urls = []

    try:
        tanggal_dt = datetime.strptime(
            tanggal, "%Y-%m-%dT%H:%M"
        )  # Format dari input type datetime-local
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

        new_item = GalleryNobar(title=title, image_url=media_url, tanggal=tanggal_dt)
        db.add(new_item)

    db.commit()
    db.close()

    return RedirectResponse(url="/cms", status_code=303)


@app.get("/pengurus", response_class=HTMLResponse)
async def pengurus(request: Request):
    return templates.TemplateResponse("pengurus.html", {"request": request})


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
