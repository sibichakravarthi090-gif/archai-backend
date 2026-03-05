from fastapi import FastAPI, UploadFile, File
import cv2
import numpy as np
from PIL import Image
import io

app = FastAPI()


def detect_walls(image):

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    edges = cv2.Canny(gray, 50, 150)

    lines = cv2.HoughLinesP(
        edges,
        1,
        np.pi/180,
        threshold=100,
        minLineLength=50,
        maxLineGap=10
    )

    walls = []

    if lines is not None:
        for line in lines:
            x1, y1, x2, y2 = line[0]

            walls.append({
                "x1": float(x1/50),
                "z1": float(y1/50),
                "x2": float(x2/50),
                "z2": float(y2/50)
            })

    return walls


@app.get("/")
def home():
    return {"status": "server running"}


@app.post("/upload")
async def upload(file: UploadFile = File(...)):

    contents = await file.read()

    image = Image.open(io.BytesIO(contents))

    image = np.array(image)

    walls = detect_walls(image)

    return {
        "walls": walls
    }
