from fastapi import FastAPI, UploadFile, File
from fastapi.staticfiles import StaticFiles
import uvicorn
import os
import cv2
import numpy as np
import trimesh

app = FastAPI()

UPLOAD_FOLDER = "uploads"
MODEL_FOLDER = "models"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(MODEL_FOLDER, exist_ok=True)

app.mount("/models", StaticFiles(directory="models"), name="models")


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

    if lines is not None:

        for line in lines:

            x1, y1, x2, y2 = line[0]

            length = np.sqrt((x2-x1)**2 + (y2-y1)**2)

            if length > 100:
                walls.append((x1, y1, x2, y2))

    return walls


def generate_3d_model(walls, output_path):

    meshes = []

    wall_height = 3
    wall_thickness = 0.2

    for wall in walls:

        x1, y1, x2, y2 = wall

        length = np.sqrt((x2-x1)**2 + (y2-y1)**2)

        wall_mesh = trimesh.creation.box(
            extents=(length/100, wall_thickness, wall_height)
        )

        center_x = (x1 + x2) / 200
        center_y = (y1 + y2) / 200

        wall_mesh.apply_translation([center_x, center_y, wall_height/2])

        meshes.append(wall_mesh)

    if len(meshes) == 0:
        return None

    scene = trimesh.Scene(meshes)

    scene.export(output_path)

    return output_path


@app.post("/upload")
async def upload_blueprint(file: UploadFile = File(...)):

    file_path = os.path.join(UPLOAD_FOLDER, file.filename)

    with open(file_path, "wb") as f:
        f.write(await file.read())

    walls = process_blueprint(file_path)

    model_path = os.path.join(MODEL_FOLDER, "house.glb")

    generate_3d_model(walls, model_path)

    return {
        "model_url": "/models/house.glb"
    }


@app.get("/")
def home():
    return {"message": "ArchAI Backend Running"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
