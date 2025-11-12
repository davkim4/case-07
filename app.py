from flask import Flask, request, jsonify, render_template
from azure.storage.blob import BlobServiceClient
from dotenv import load_dotenv
import os
from datetime import datetime
from werkzeug.utils import secure_filename

load_dotenv()

AZURE_CONNECTION_STRING = os.getenv("AZURE_CONNECTION_STRING")
CONTAINER_NAME = os.getenv("CONTAINER_NAME", "lanternfly-images-c33su723")

bsc = BlobServiceClient.from_connection_string(AZURE_CONNECTION_STRING) ## Create Blob Service Client
cc  = bsc.get_container_client(CONTAINER_NAME) # Replace with Container name cc.url will get you the url path to the container.  
app = Flask(__name__)
@app.post("/api/v1/upload")
def upload():
    if "file" not in request.files:
        return jsonify(ok=False, error="No file provided"), 400

    f = request.files["file"]
    if f.filename == "":
        return jsonify(ok=False, error="Empty filename"), 400

    # Sanitize and timestamp filename
    safe_filename = secure_filename(f.filename)
    timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%S")
    blob_name = f"{timestamp}-{safe_filename}"

    try:
        cc.upload_blob(name=blob_name, data=f, overwrite=True)
    except Exception as e:
        return jsonify(ok=False, error=str(e)), 500

    blob_url = f"{cc.url}/{blob_name}"
    return jsonify(ok=True, url=blob_url)

@app.get("/api/v1/gallery")
def gallery():
    try:
        blob_list = cc.list_blobs()
        urls = [f"{cc.url}/{blob.name}" for blob in blob_list]
        return jsonify(ok=True, gallery=urls)
    except Exception as e:
        return jsonify(ok=False, error=str(e)), 500


@app.get("/api/v1/health")
def health():
    return jsonify(ok=True, status="healthy")

@app.get("/")
def index():
    return render_template("index.html")

if __name__ == "__main__":
    import os

    port = int(os.environ.get("PORT", 8000))  # Azure sets PORT; fallback 8000 locally
    app.run(host="0.0.0.0", port=port)