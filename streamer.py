import subprocess
import os
import threading
import time

class Streamer:
    def __init__(self):
        self.process = None
        self.streaming = False
        self.logs = []
        self.log_lock = threading.Lock()
        
    def add_log(self, message: str):
        """Tambahkan log dengan thread safety"""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        with self.log_lock:
            self.logs.append(log_entry)
        print(log_entry)
    
    def get_logs(self, limit: int = 50):
        """Dapatkan logs terakhir"""
        with self.log_lock:
            return self.logs[-limit:] if self.logs else []
    
    def clear_logs(self):
        """Bersihkan logs"""
        with self.log_lock:
            self.logs.clear()
    
    def run_ffmpeg(self, video_path: str, stream_key: str, is_shorts: bool):
        """Jalankan streaming menggunakan FFmpeg"""
        if not os.path.exists(video_path):
            self.add_log(f"Error: Video file not found: {video_path}")
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
        
        self.add_log(f"Menjalankan: {' '.join(cmd)}")
        
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
                self.add_log(line.strip())
                
            self.process.wait()
            
        except Exception as e:
            self.add_log(f"Error: {str(e)}")
        finally:
            self.streaming = False
            self.add_log("Streaming selesai atau dihentikan.")
    
    def start_streaming(self, video_path: str, stream_key: str, is_shorts: bool):
        """Mulai streaming dalam thread terpisah"""
        if self.streaming:
            raise Exception("Sudah ada streaming yang aktif")
            
        # Bersihkan logs sebelumnya
        self.clear_logs()
        
        thread = threading.Thread(
            target=self.run_ffmpeg,
            args=(video_path, stream_key, is_shorts),
            daemon=True
        )
        thread.start()
        self.add_log("Streaming dimulai")
        return {"status": "success", "message": "Streaming dimulai"}
    
    def stop_streaming(self):
        """Hentikan streaming"""
        if self.process:
            self.process.terminate()
            self.process = None
        self.streaming = False
        # Kill semua proses ffmpeg
        os.system("pkill -f ffmpeg")
        self.add_log("Streaming dihentikan")
        return {"status": "success", "message": "Streaming dihentikan"}

# Singleton instance
streamer_instance = Streamer()
