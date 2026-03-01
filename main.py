from fastapi import FastAPI, UploadFile, File, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from enum import Enum
from typing import Optional, Dict
import shutil
import os
import uuid
import time

app = FastAPI(title="ArchAI Backend", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


class ProcessingStatus(str, Enum):
    processing = "processing"
    completed = "completed"
    failed = "failed"


class UploadResponse(BaseModel):
    success: bool
    file_id: str
    message: str


class StatusResponse(BaseModel):
    status: ProcessingStatus
    result: Optional[str] = None


class InMemoryStorage:
    def __init__(self):
        self._data: Dict[str, StatusResponse] = {}

    def create(self, file_id: str):
        self._data[file_id] = StatusResponse(status=ProcessingStatus.processing)

    def update(self, file_id: str, status: ProcessingStatus, result: Optional[str] = None):
        self._data[file_id] = StatusResponse(status=status, result=result)

    def get(self, file_id: str) -> StatusResponse:
        if file_id not in self._data:
            raise KeyError("File ID not found")
        return self._data[file_id]


storage = InMemoryStorage()


@app.get("/")
async def root():
    return {"status": "ArchAI Backend Running"}


@app.post("/upload", response_model=UploadResponse)
async def upload_blueprint(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    file_id = str(uuid.uuid4())
    extension = file.filename.split(".")[-1]
    saved_filename = f"{file_id}.{extension}"
    file_path = os.path.join(UPLOAD_DIR, saved_filename)

    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to save file")

    storage.create(file_id)
    background_tasks.add_task(process_blueprint, file_id, file_path)

    return UploadResponse(
        success=True,
        file_id=file_id,
        message="Upload successful. Processing started."
    )


@app.get("/status/{file_id}", response_model=StatusResponse)
async def check_status(file_id: str):
    try:
        return storage.get(file_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Invalid file ID")


def process_blueprint(file_id: str, file_path: str):
    try:
        time.sleep(8)

        result_path = f"/models/{file_id}.glb"

        storage.update(
            file_id,
            ProcessingStatus.completed,
            result=result_path
        )

    except Exception:
        storage.update(file_id, ProcessingStatus.failed)
