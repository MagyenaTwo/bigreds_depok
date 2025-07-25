import shutil
from uuid import uuid4
from fastapi import FastAPI, File, Request, Form, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
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
from models import User  # pastikan model User sesuai dengan tabel users
from database import SessionLocal
from fastapi.responses import RedirectResponse
load_dotenv()

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="bigredsmantap")
# ⬇️ Perbaiki path ke folder frontend
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

@app.get("/cms/delete/{id}")
def delete_image(id: int):
    supabase.table("gallery_nobar").delete().eq("id", id).execute()
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
        return RedirectResponse(url="/cms", status_code=302)
    return templates.TemplateResponse("login.html", {
        "request": request,
        "error": "Username atau password salah."
    })

@app.get("/logout")
def logout(request: Request):
    request.session.clear() 
    return RedirectResponse(url="/login", status_code=302)