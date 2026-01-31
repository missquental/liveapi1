import subprocess
import os
import threading
from typing import Callable

class Streamer:
    def __init__(self):
        self.process = None
        self.streaming = False
        self.logs = []
        
    def log_message(self, message: str):
        """Simpan log pesan"""
        log_entry = f"[{len(self.logs) + 1}] {message}"
        self.logs.append(log_entry)
        print(log_entry)
    
    def run_ffmpeg(self, video_path: str, stream_key: str, is_shorts: bool):
        """Jalankan streaming menggunakan FFmpeg"""
        if not os.path.exists(video_path):
            self.log_message(f"Error: Video file not found: {video_path}")
            return
            
        output_url = f"rtmp://a.rtmp.youtube.com/live2/{stream_key}"
        
        # Build command
        cmd = [
            "ffmpeg", "-re", "-stream_loop", "-1", "-i", video_path,
            "-c:v", "libx264", "-preset", "veryfast", "-b:v", "2500k",
            "-maxrate", "2500k", "-bufsize", "5000k",
            "-g", "60", "-keyint_min", "60",
            "-c:a", "aac", "-b:a", "128k",
            "-f", "flv"
        ]
        
        # Tambahkan scaling untuk shorts
        if is_shorts:
            cmd.extend(["-vf", "scale=720:1280"])
            
        cmd.append(output_url)
        
        self.log_message(f"Menjalankan: {' '.join(cmd)}")
        
        try:
            self.process = subprocess.Popen(
                cmd, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.STDOUT, 
                text=True
            )
            
            self.streaming = True
            
            # Baca output FFmpeg
            for line in self.process.stdout:
                self.log_message(line.strip())
                
            self.process.wait()
            
        except Exception as e:
            self.log_message(f"Error: {str(e)}")
        finally:
            self.streaming = False
            self.log_message("Streaming selesai atau dihentikan.")
    
    def start_streaming(self, video_path: str, stream_key: str, is_shorts: bool):
        """Mulai streaming dalam thread terpisah"""
        if self.streaming:
            raise Exception("Sudah ada streaming yang aktif")
            
        thread = threading.Thread(
            target=self.run_ffmpeg,
            args=(video_path, stream_key, is_shorts),
            daemon=True
        )
        thread.start()
        self.log_message("Streaming dimulai")
        return {"status": "success", "message": "Streaming dimulai"}
    
    def stop_streaming(self):
        """Hentikan streaming"""
        if self.process:
            self.process.terminate()
            self.process = None
        self.streaming = False
        # Kill semua proses ffmpeg
        os.system("pkill ffmpeg")
        self.log_message("Streaming dihentikan")
        return {"status": "success", "message": "Streaming dihentikan"}

# Singleton instance
streamer_instance = Streamer()
