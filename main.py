import shutil
from uuid import uuid4
from fastapi import FastAPI, File, Request, Form, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
import os

from supabase import create_client
from utils import format_datetime_indo
from database import SessionLocal
from models import Match, TicketOrder
from dotenv import load_dotenv
from starlette.middleware.sessions import SessionMiddleware
from fastapi import Depends
from werkzeug.security import check_password_hash
from models import User 
from database import SessionLocal
from fastapi.responses import RedirectResponse
from werkzeug.security import generate_password_hash
load_dotenv()

app = FastAPI()
app.add_middleware(
    SessionMiddleware,
    secret_key="bigredsmantap",  
    max_age=1800 
)

app.add_middleware(SessionMiddleware, secret_key="bigredsmantap")
app.mount("/static", StaticFiles(directory="frontend/static"), name="static")

templates = Jinja2Templates(directory="frontend")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
@app.get("/", response_class=HTMLResponse)
async def read_form(request: Request):
    db: Session = SessionLocal()

    now = datetime.now()  # waktu sekarang
    match = (
        db.query(Match)
        .filter(Match.match_datetime >= now)  # hanya match di masa depan
        .order_by(Match.match_datetime.asc())
        .first()
    )

    db.close()

    formatted_datetime = format_datetime_indo(match.match_datetime) if match else None

    return templates.TemplateResponse("index.html", {
        "request": request,
        "match": match,
        "formatted_datetime": formatted_datetime
    })



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
    bukti_transfer: UploadFile = File(...)
):
    ext = bukti_transfer.filename.split('.')[-1]
    filename = f"bukti/{uuid4()}.{ext}"
    content = await bukti_transfer.read()

    upload_res = supabase.storage.from_("bukti").upload(
        path=filename,
        file=content,
        file_options={"content-type": bukti_transfer.content_type}
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
        bukti_transfer_url=bukti_url
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
def cms_page(request: Request):
    if not request.session.get("user_id"):
        return RedirectResponse(url="/login", status_code=302)
    
    data = supabase.table("gallery_nobar").select("*").order("created_at", desc=True).execute()
    return templates.TemplateResponse("cms.html", {
        "request": request,
        "images": data.data
    })


@app.post("/cms/upload")
async def upload_image(title: str = Form(...), image: UploadFile = File(...)):
    filename = image.filename
    file_path = f"frontend/static/img/{filename}"
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(image.file, buffer)

    image_url = f"/static/img/{filename}"
    supabase.table("gallery_nobar").insert({
        "title": title,
        "image_url": image_url
    }).execute()

    return RedirectResponse(url="/cms", status_code=303)


@app.get("/login", response_class=HTMLResponse)
async def login_get(request: Request):
    return templates.TemplateResponse("login.html", {"request": request, "error": None})


@app.post("/login", response_class=HTMLResponse)
async def login_post(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.username == username).first()
    if user and check_password_hash(user.password, password):
        request.session['user_id'] = user.id
        return RedirectResponse(url="/cms/tiket", status_code=302)
    return templates.TemplateResponse("login.html", {
        "request": request,
        "error": "Username atau password salah."
    })

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

    return templates.TemplateResponse("cms_tiket.html", {
        "request": request,
        "daftar_tiket": daftar_tiket,
        "current_page": page,
        "total_pages": total_pages
    })


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
    db: Session = Depends(get_db)
):
    if not request.session.get("user_id"):
        return RedirectResponse(url="/login", status_code=302)

    existing_user = db.query(User).filter(User.username == username).first()
    if existing_user:
        return templates.TemplateResponse("cms_akun.html", {
            "request": request,
            "error": "Username sudah digunakan. Coba yang lain."
        })

    hashed_password = generate_password_hash(password)
    new_user = User(username=username, password=hashed_password)
    db.add(new_user)
    db.commit()

    return templates.TemplateResponse("cms_akun.html", {
        "request": request,
        "success": "Akun berhasil dibuat!"
    })