from fastapi import FastAPI, UploadFile, File
import uvicorn
import os
import cv2
import numpy as np

app = FastAPI()

UPLOAD_FOLDER = "uploads"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def process_blueprint(image_path):

    img = cv2.imread(image_path)

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    edges = cv2.Canny(gray, 50, 150)

    lines = cv2.HoughLinesP(
        edges,
        1,
        np.pi / 180,
        threshold=100,
        minLineLength=80,
        maxLineGap=10
    )

    walls = []
    doors = []

    if lines is not None:

        for line in lines:

            x1, y1, x2, y2 = line[0]

            length = np.sqrt((x2-x1)**2 + (y2-y1)**2)

            if length > 100:

                walls.append({
                    "x1": int(x1),
                    "y1": int(y1),
                    "x2": int(x2),
                    "y2": int(y2)
                })

            else:

                doors.append({
                    "x": int(x1),
                    "y": int(y1),
                    "width": 50
                })

    return {
        "walls": walls,
        "doors": doors
    }

@app.post("/upload")
async def upload_blueprint(file: UploadFile = File(...)):

    file_location = os.path.join(UPLOAD_FOLDER, file.filename)

    with open(file_location, "wb") as f:
        f.write(await file.read())

    result = process_blueprint(file_location)

    return result

@app.get("/")
def home():
    return {"message": "ArchAI Backend Running"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
