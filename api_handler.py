import os
import json
import base64
from streamer import streamer_instance
from typing import Dict, Any
import tempfile

def save_uploaded_file(file_data: bytes, filename: str) -> str:
    """Simpan file yang diupload melalui API"""
    try:
        # Simpan file di direktori saat ini
        file_path = filename
        
        # Tulis file
        with open(file_path, "wb") as f:
            f.write(file_data)
            
        return file_path
    except Exception as e:
        raise Exception(f"Gagal menyimpan file: {str(e)}")

def handle_api_request(action: str, data: dict = None, file_data: bytes = None):
    """Handle API-like requests within Streamlit"""
    try:
        if action == "upload":
            # Handle upload file via API
            filename = data.get("filename")
            if not filename:
                return {"status": "error", "message": "Filename required"}
            
            if not file_data:
                return {"status": "error", "message": "File data required"}
            
            # Simpan file
            file_path = save_uploaded_file(file_data, filename)
            
            return {
                "status": "success", 
                "message": f"File {filename} uploaded successfully",
                "filepath": file_path,
                "filesize": os.path.getsize(file_path)
            }
            
        elif action == "start_stream":
            filename = data.get("filename")
            stream_key = data.get("stream_key")
            is_shorts = data.get("is_shorts", False)
            
            if not filename or not stream_key:
                return {"status": "error", "message": "Filename and stream key required"}
            
            file_path = filename  # File sudah ada di current directory
            if not os.path.exists(file_path):
                return {"status": "error", "message": f"File not found: {filename}"}
            
            result = streamer_instance.start_streaming(file_path, stream_key, is_shorts)
            return result
            
        elif action == "stop_stream":
            result = streamer_instance.stop_streaming()
            return result
            
        elif action == "get_status":
            return {
                "status": "success",
                "streaming": streamer_instance.streaming,
                "logs_count": len(streamer_instance.logs)
            }
            
        elif action == "get_logs":
            limit = data.get("limit", 50)
            logs = streamer_instance.logs[-limit:] if streamer_instance.logs else []
            return {
                "status": "success",
                "logs": logs,
                "total": len(streamer_instance.logs)
            }
            
        elif action == "list_videos":
            # List semua file video di direktori
            video_extensions = ('.mp4', '.flv', '.mov', '.avi', '.mkv')
            videos = []
            for file in os.listdir('.'):
                if file.lower().endswith(video_extensions):
                    file_stats = os.stat(file)
                    videos.append({
                        "filename": file,
                        "size": file_stats.st_size,
                        "modified": file_stats.st_mtime
                    })
            return {
                "status": "success",
                "videos": videos
            }
            
        else:
            return {"status": "error", "message": "Invalid action"}
            
    except Exception as e:
        return {"status": "error", "message": str(e)}

# === FASTAPI INTEGRATION ===
# Tambahkan ini untuk membuat endpoint API sederhana

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
import uvicorn
import threading

# Buat instance FastAPI global
api_app = FastAPI(title="YouTube Streaming API")

@api_app.post("/api/upload")
async def api_upload_video(file: UploadFile = File(...)):
    """API endpoint untuk upload video"""
    try:
        # Baca file data
        file_data = await file.read()
        
        # Simpan file
        with open(file.filename, "wb") as f:
            f.write(file_data)
            
        return JSONResponse(
            content={
                "status": "success",
                "filename": file.filename,
                "size": len(file_data),
                "message": "Upload successful"
            },
            status_code=200
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_app.post("/api/stream/start")
async def api_start_stream(
    filename: str = Form(...),
    stream_key: str = Form(...),
    is_shorts: bool = Form(False)
):
    """API endpoint untuk mulai streaming"""
    try:
        if not os.path.exists(filename):
            raise HTTPException(status_code=404, detail=f"File not found: {filename}")
            
        result = streamer_instance.start_streaming(filename, stream_key, is_shorts)
        return JSONResponse(content=result, status_code=200)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_app.post("/api/stream/stop")
async def api_stop_stream():
    """API endpoint untuk stop streaming"""
    result = streamer_instance.stop_streaming()
    return JSONResponse(content=result, status_code=200)

@api_app.get("/api/status")
async def api_get_status():
    """API endpoint untuk status streaming"""
    status_result = {
        "streaming": streamer_instance.streaming,
        "logs_count": len(streamer_instance.logs)
    }
    return JSONResponse(content=status_result, status_code=200)

@api_app.get("/api/logs")
async def api_get_logs(limit: int = 50):
    """API endpoint untuk logs"""
    logs = streamer_instance.logs[-limit:] if streamer_instance.logs else []
    return JSONResponse(
        content={
            "logs": logs,
            "total": len(streamer_instance.logs)
        },
        status_code=200
    )

@api_app.get("/api/videos")
async def api_list_videos():
    """API endpoint untuk list video"""
    video_extensions = ('.mp4', '.flv', '.mov', '.avi', '.mkv')
    videos = []
    for file in os.listdir('.'):
        if file.lower().endswith(video_extensions):
            file_stats = os.stat(file)
            videos.append({
                "filename": file,
                "size": file_stats.st_size,
                "modified": file_stats.st_mtime
            })
    return JSONResponse(
        content={"videos": videos},
        status_code=200
    )

# Fungsi untuk menjalankan API server di background
def start_api_server():
    """Jalankan API server di thread terpisah"""
    def run():
        uvicorn.run(api_app, host="0.0.0.0", port=8000, log_level="error")
    
    api_thread = threading.Thread(target=run, daemon=True)
    api_thread.start()
    return api_thread

# Jalankan API server saat module diimport
api_thread = start_api_server()
