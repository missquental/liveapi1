import os
import json
from streamer import streamer_instance

def handle_api_request(action: str, data: dict = None):
    """Handle API-like requests within Streamlit"""
    try:
        if action == "upload":
            # Simulasi upload - dalam praktiknya file sudah diupload oleh Streamlit
            filename = data.get("filename")
            if not filename:
                return {"status": "error", "message": "Filename required"}
            return {"status": "success", "message": f"File {filename} ready for streaming"}
            
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
            
        else:
            return {"status": "error", "message": "Invalid action"}
            
    except Exception as e:
        return {"status": "error", "message": str(e)}
