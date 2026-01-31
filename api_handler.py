import os
import json
from streamer import streamer_instance
from typing import Dict, Any

def save_uploaded_file(file_data: bytes, filename: str) -> str:
    """Simpan file yang diupload"""
    try:
        file_path = filename
        with open(file_path, "wb") as f:
            f.write(file_data)
        return file_path
    except Exception as e:
        raise Exception(f"Gagal menyimpan file: {str(e)}")

def handle_api_request(action: str, data: dict = None, file_data: bytes = None):
    """Handle API-like requests within Streamlit"""
    try:
        if action == "upload":
            # Handle upload file
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
            
            file_path = filename
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
