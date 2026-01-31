import streamlit as st
import uvicorn
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
import os
import shutil
from streamer import streamer_instance
import threading
import time

# Buat folder uploads
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Inisialisasi FastAPI
api = FastAPI(title="YouTube Live Streaming API")

# === API ENDPOINTS ===

@api.get("/")
async def root():
    """API Root"""
    return {
        "message": "YouTube Live Streaming API",
        "docs": "/docs",
        "endpoints": {
            "upload": "POST /api/upload",
            "start_stream": "POST /api/start",
            "stop_stream": "POST /api/stop",
            "status": "GET /api/status",
            "logs": "GET /api/logs"
        }
    }

@api.post("/api/upload")
async def upload_video(file: UploadFile = File(...)):
    """
    Upload video file
    """
    try:
        # Validasi ekstensi file
        allowed_extensions = {'.mp4', '.flv', '.mov', '.avi', '.mkv'}
        file_extension = os.path.splitext(file.filename)[1].lower()
        
        if file_extension not in allowed_extensions:
            raise HTTPException(
                status_code=400, 
                detail=f"Tipe file tidak didukung. Gunakan: {allowed_extensions}"
            )
        
        # Simpan file ke uploads folder
        file_path = os.path.join(UPLOAD_FOLDER, file.filename)
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        return JSONResponse(
            content={
                "status": "success",
                "filename": file.filename,
                "path": file_path,
                "size": os.path.getsize(file_path),
                "message": "Upload berhasil"
            },
            status_code=200
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api.post("/api/start")
async def start_stream(
    filename: str = Form(...),
    stream_key: str = Form(...),
    is_shorts: bool = Form(False)
):
    """
    Mulai streaming ke YouTube
    """
    try:
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        
        if not os.path.exists(file_path):
            raise HTTPException(
                status_code=404, 
                detail=f"File tidak ditemukan: {filename}"
            )
        
        # Cek apakah sudah streaming
        if streamer_instance.streaming:
            raise HTTPException(
                status_code=400, 
                detail="Sudah ada streaming yang aktif"
            )
        
        # Mulai streaming
        result = streamer_instance.start_streaming(file_path, stream_key, is_shorts)
        return JSONResponse(content=result, status_code=200)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api.post("/api/stop")
async def stop_stream():
    """
    Hentikan streaming
    """
    try:
        result = streamer_instance.stop_streaming()
        return JSONResponse(content=result, status_code=200)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api.get("/api/status")
async def stream_status():
    """
    Dapatkan status streaming
    """
    return JSONResponse(
        content={
            "streaming": streamer_instance.streaming,
            "active_process": streamer_instance.process is not None
        },
        status_code=200
    )

@api.get("/api/logs")
async def get_logs(limit: int = 50):
    """
    Dapatkan log streaming
    """
    logs = streamer_instance.get_logs(limit)
    return JSONResponse(
        content={
            "logs": logs,
            "total_logs": len(logs)
        },
        status_code=200
    )

@api.get("/api/list-videos")
async def list_videos():
    """
    Dapatkan daftar video yang sudah diupload
    """
    try:
        videos = []
        for filename in os.listdir(UPLOAD_FOLDER):
            file_path = os.path.join(UPLOAD_FOLDER, filename)
            if os.path.isfile(file_path):
                file_stats = os.stat(file_path)
                videos.append({
                    "filename": filename,
                    "size": file_stats.st_size,
                    "modified": time.ctime(file_stats.st_mtime)
                })
        
        return JSONResponse(
            content={"videos": videos},
            status_code=200
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# === STREAMLIT INTERFACE ===

def streamlit_interface():
    st.set_page_config(
        page_title="Streaming API Manager",
        page_icon="🎬",
        layout="wide"
    )
    
    st.title("🎬 YouTube Live Streaming API Manager")
    
    tab1, tab2, tab3 = st.tabs(["📤 Upload", "▶️ Control", "📊 Monitor"])
    
    with tab1:
        st.subheader("Upload Video")
        uploaded_file = st.file_uploader("Pilih video", type=['mp4', 'flv', 'mov', 'avi'])
        
        if uploaded_file:
            with open(os.path.join(UPLOAD_FOLDER, uploaded_file.name), "wb") as f:
                f.write(uploaded_file.getbuffer())
            st.success(f"✅ {uploaded_file.name} berhasil diupload!")
            
        st.subheader("Daftar Video")
        if os.path.exists(UPLOAD_FOLDER):
            videos = [f for f in os.listdir(UPLOAD_FOLDER) if os.path.isfile(os.path.join(UPLOAD_FOLDER, f))]
            for video in videos:
                st.write(f"📁 {video}")
    
    with tab2:
        st.subheader("Control Panel")
        
        # List video files
        video_files = []
        if os.path.exists(UPLOAD_FOLDER):
            video_files = [f for f in os.listdir(UPLOAD_FOLDER) if os.path.isfile(os.path.join(UPLOAD_FOLDER, f))]
        
        selected_video = st.selectbox("Pilih Video", video_files) if video_files else None
        stream_key = st.text_input("Stream Key YouTube", type="password")
        is_shorts = st.checkbox("Mode Shorts (720x1280)")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("▶️ Start Streaming"):
                if not selected_video or not stream_key:
                    st.error("Pilih video dan masukkan stream key!")
                else:
                    try:
                        file_path = os.path.join(UPLOAD_FOLDER, selected_video)
                        result = streamer_instance.start_streaming(file_path, stream_key, is_shorts)
                        st.success(result["message"])
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
        
        with col2:
            if st.button("⏹️ Stop Streaming"):
                result = streamer_instance.stop_streaming()
                st.warning(result["message"])
    
    with tab3:
        st.subheader("Monitoring")
        
        # Status
        status_info = {
            "Streaming Aktif": streamer_instance.streaming,
            "Process Aktif": streamer_instance.process is not None
        }
        st.json(status_info)
        
        # Logs
        st.subheader("Logs")
        if st.button("🔄 Refresh Logs"):
            pass
            
        logs = streamer_instance.get_logs(100)
        if logs:
            st.text_area("Streaming Logs", value="\n".join(logs), height=400, key="logs_monitor")
        else:
            st.info("Belum ada logs")
    
    st.divider()
    st.info("""
    ### API Endpoints:
    - `POST /api/upload` - Upload video
    - `POST /api/start` - Mulai streaming  
    - `POST /api/stop` - Stop streaming
    - `GET /api/status` - Status streaming
    - `GET /api/logs` - Logs streaming
    - `GET /api/list-videos` - Daftar video
    
    Base URL: https://liveapi1.streamlit.app/
    """)

# Jalankan keduanya
if __name__ == "__main__":
    import sys
    if "streamlit" in sys.argv:
        streamlit_interface()
    else:
        # Jalankan API server
        uvicorn.run(api, host="0.0.0.0", port=8000)
