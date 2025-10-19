from fastapi import FastAPI, UploadFile, File, Form, Request
from fastapi.responses import HTMLResponse, FileResponse
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
    tests = db.query(Test).all()
    db.close()
    return templates.TemplateResponse("index.html", {"request": request, "logs": logs, "tests": tests})


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
