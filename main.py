from fastapi import FastAPI, UploadFile, File
import uuid
import shutil
import os
import cv2
import numpy as np

app = FastAPI()

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def extract_walls(image_path):

    image = cv2.imread(image_path)

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    edges = cv2.Canny(gray, 50, 150)

    lines = cv2.HoughLinesP(
        edges,
        1,
        np.pi / 180,
        threshold=100,
        minLineLength=50,
        maxLineGap=10
    )

    walls = []

    if lines is not None:
        for line in lines:
            x1, y1, x2, y2 = line[0]

            walls.append({
                "x1": int(x1),
                "y1": int(y1),
                "x2": int(x2),
                "y2": int(y2)
            })

    return walls


@app.post("/upload")
async def upload_blueprint(file: UploadFile = File(...)):

    file_id = str(uuid.uuid4())

    file_path = f"{UPLOAD_FOLDER}/{file_id}.png"

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    walls = extract_walls(file_path)

    return {
        "file_id": file_id,
        "walls": walls
    }


@app.get("/")
def root():
    return {"message": "ArchAI Backend Running"}
