from fastapi import FastAPI, UploadFile, File, Form, Request, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os, shutil
from datetime import datetime
from db import init_db, SessionLocal, Log, Test, DriverEnum, CarEnum, MissionEnum, LogTypeEnum
from analysis import analyze_log
from starlette.middleware.sessions import SessionMiddleware
from authlib.integrations.starlette_client import OAuth
from dotenv import load_dotenv
import logging
logger = logging.getLogger("uvicorn")

load_dotenv()

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key=os.getenv("SECRET_KEY"))
templates = Jinja2Templates(directory="templates")

# --- Configurar OAuth con Google ---
oauth = OAuth()
oauth.register(
    name="google",
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)

ALLOWED_USERS = [u.strip() for u in os.getenv("ALLOWED_USERS", "").split(",") if u]


UPLOAD_DIR = "uploads"
GRAPH_DIR = "static"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(GRAPH_DIR, exist_ok=True)

app.mount("/static", StaticFiles(directory="static"), name="static")

init_db()



# Aux functions
def require_auth(request: Request):
    user = request.session.get("user")
    if not user:
        # Lanzamos una excepción para cortar el flujo
        raise HTTPException(
            status_code=status.HTTP_303_SEE_OTHER,
            detail="Necesitas iniciar sesión",
            headers={"Location": "/login"},
        )
    email = user.get("email")
    if email not in ALLOWED_USERS:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para esta acción"
        )
    return user


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    db = SessionLocal()
    logs = db.query(Log).all()
    tests = db.query(Test).all()
    db.close()
    user = request.session.get("user")
    return templates.TemplateResponse("index.html", 
            {"request": request,
             "logs": logs, 
             "tests": tests, 
             "user": user,
             "allowed_users": ALLOWED_USERS})


# --- Formulario para añadir TEST ---
@app.get("/add_test", response_class=HTMLResponse)
def add_test_form(request: Request, user=Depends(require_auth)):
    return templates.TemplateResponse("add_test.html", {
        "request": request
    })


@app.post("/add_test")
def add_test(
    name: str = Form(...),
    description: str = Form(...),
    date: datetime = Form(...),
    user=Depends(require_auth)
):
    db = SessionLocal()
    test = Test(name=name, description=description, date=date)
    db.add(test)
    db.commit()
    db.close()
    return RedirectResponse(url="/", status_code=303)


# --- Formulario para añadir LOG ---
@app.get("/add_log", response_class=HTMLResponse)
def add_test_form(request: Request, user=Depends(require_auth)):
    db = SessionLocal()
    tests = db.query(Test).all()
    db.close()
    return templates.TemplateResponse("add_log.html", 
    {"request": request,
     "tests": tests,
     "drivers": [d.value for d in DriverEnum],
     "vehicles": [v.value for v in CarEnum],
     "log_types": [t.value for t in LogTypeEnum],
     "missions": [m.value for m in MissionEnum]})


@app.post("/add_log")
async def add_log(
    test_id: int = Form(...),
    file: UploadFile = File(...),
    mission: str = Form(...),
    driver: str = Form(...),
    log_type: str = Form(...),
    vehicle: str = Form(...),
    description: str = Form(...),
    user=Depends(require_auth)
):
    db = SessionLocal()

    save_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(save_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    new_log = Log(
        test_id=test_id,
        filename=file.filename,
        filepath=save_path,
        mission=mission or None,
        driver=driver or None,
        log_type=log_type or None,
        vehicle=vehicle or None,
        description=description,
        uploaded_at=datetime.utcnow()
    )

    db.add(new_log)
    db.commit()
    db.close()

    return RedirectResponse(url="/", status_code=303)


@app.get("/download/{log_id}")
def download_log(log_id: int):
    db = SessionLocal()
    log = db.query(Log).filter(Log.id == log_id).first()
    db.close()
    if not log:
        return {"error": "Archivo no encontrado"}
    
    file_path = log.filepath
    if not os.path.exists(file_path):
        return {"error": "El archivo no existe en el servidor"}
    
    filename = os.path.basename(file_path)
    return FileResponse(path=file_path, filename=filename, media_type='application/octet-stream')


@app.get("/login")
async def login(request: Request):
    redirect_uri = request.url_for("auth_callback")
    return await oauth.google.authorize_redirect(
        request,
        redirect_uri,
        prompt="select_account"  # fuerza el selector de cuentas
    )


@app.get("/auth/callback")
async def auth_callback(request: Request):
    token = await oauth.google.authorize_access_token(request)
    user_info = token.get("userinfo")

    if user_info:
        request.session["user"] = dict(user_info)
    return RedirectResponse(url="/")


@app.get("/logout")
async def logout(request: Request):
    request.session.pop("user", None)
    return RedirectResponse(url="/")



