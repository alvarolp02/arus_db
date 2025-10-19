from fastapi import FastAPI, UploadFile, File, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os, shutil
from db import init_db, SessionLocal, Log, Test, DriverEnum, CarEnum, MissionEnum, LogTypeEnum
from analysis import analyze_log

app = FastAPI()

UPLOAD_DIR = "uploads"
GRAPH_DIR = "static"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(GRAPH_DIR, exist_ok=True)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

init_db()

@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    db = SessionLocal()
    logs = db.query(Log).all()
    db.close()
    return templates.TemplateResponse("index.html", {"request": request, "logs": logs})

@app.post("/upload", response_class=HTMLResponse)
async def upload(request: Request, file: UploadFile = File(...), vehicle_id: str = Form(...)):
    filename = f"{vehicle_id}_{file.filename}"
    path = os.path.join(UPLOAD_DIR, filename)
    with open(path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    db = SessionLocal()
    log = Log(filename=filename, filepath=path,
                  description="")
    db.add(log)
    db.commit()
    db.close()

    return templates.TemplateResponse("upload_success.html",
        {"request": request, "filename": filename})
