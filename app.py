import sys
import subprocess
import os
import streamlit.components.v1 as components
import streamlit as st
from streamer import streamer_instance
from api_handler import handle_api_request
import json

# Page configuration
st.set_page_config(
    page_title="Streaming YT by didinchy",
    page_icon="📈",
    layout="wide"
)

def main():
    st.title("🎥 Live Streaming to YouTube")
    
    # Cek jika ada request API dari form submission
    query_params = st.experimental_get_query_params()
    if "action" in query_params:
        action = query_params["action"][0]
        # Proses API request
        data = {}
        for key in query_params:
            if key != "action":
                data[key] = query_params[key][0]
        
        result = handle_api_request(action, data)
        st.json(result)
        return
    
    # Tabs untuk navigasi
    tab1, tab2, tab3 = st.tabs(["📺 Streaming", "📊 Status", "⚙️ Settings"])
    
    with tab1:
        st.subheader("Upload & Stream Video")
        
        # List available video files
        video_files = [f for f in os.listdir('.') if f.endswith(('.mp4', '.flv', '.mov', '.avi'))]
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("📁 Video yang tersedia:")
            selected_video = st.selectbox("Pilih video", video_files) if video_files else None
            
            uploaded_file = st.file_uploader(
                "Atau upload video baru (mp4/flv/mov/avi)", 
                type=['mp4', 'flv', 'mov', 'avi']
            )
            
            if uploaded_file:
                with open(uploaded_file.name, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                st.success(f"✅ Video berhasil diupload: {uploaded_file.name}")
                video_path = uploaded_file.name
            elif selected_video:
                video_path = selected_video
            else:
                video_path = None
                
        with col2:
            stream_key = st.text_input("🔑 Stream Key YouTube", type="password")
            is_shorts = st.checkbox("📱 Mode Shorts (720x1280)")
            
            st.divider()
            
            col_btn1, col_btn2 = st.columns(2)
            
            with col_btn1:
                if st.button("▶️ Mulai Streaming", use_container_width=True):
                    if not video_path or not stream_key:
                        st.error("❌ Video dan stream key harus diisi!")
                    else:
                        result = handle_api_request("start_stream", {
                            "filename": video_path,
                            "stream_key": stream_key,
                            "is_shorts": is_shorts
                        })
                        if result["status"] == "success":
                            st.success(result["message"])
                        else:
                            st.error(f"❌ {result['message']}")
                            
            with col_btn2:
                if st.button("⏹️ Stop Streaming", use_container_width=True):
                    result = handle_api_request("stop_stream")
                    if result["status"] == "success":
                        st.warning(result["message"])
                    else:
                        st.error(f"❌ {result['message']}")
    
    with tab2:
        st.subheader("📊 Status Streaming")
        
        # Get status
        status_result = handle_api_request("get_status")
        st.metric("Status Streaming", "Aktif" if status_result.get("streaming") else "Tidak Aktif")
        st.metric("Total Logs", status_result.get("logs_count", 0))
        
        st.divider()
        
        # Show logs
        st.subheader("📋 Logs Streaming")
        if st.button("🔄 Refresh Logs"):
            pass  # Akan refresh otomatis
            
        logs_result = handle_api_request("get_logs", {"limit": 100})
        if logs_result["status"] == "success" and logs_result["logs"]:
            logs_text = "\n".join(logs_result["logs"])
            st.text_area("Logs", value=logs_text, height=400, key="logs_display")
        else:
            st.info("Belum ada logs")
    
    with tab3:
        st.subheader("⚙️ Pengaturan & API Info")
        
        # Iklan toggle
        show_ads = st.checkbox("Tampilkan Iklan", value=True)
        if show_ads:
            st.subheader("📢 Iklan Sponsor")
            components.html(
                """
                <div style="background:#f0f2f6;padding:20px;border-radius:10px;text-align:center">
                    <script type='text/javascript' 
                            src='//pl26562103.profitableratecpm.com/28/f9/95/28f9954a1d5bbf4924abe123c76a68d2.js'>
                    </script>
                    <p style="color:#888">Iklan akan muncul di sini</p>
                </div>
                """,
                height=300
            )
        
        st.divider()
        
        # API Documentation
        st.subheader("🌐 API Documentation")
        st.info("""
        **Cara Upload via API:**
        
        Untuk upload video melalui API, Anda bisa menggunakan library HTTP client seperti `requests`:
        
        ```python
        import requests
        
        # Upload video
        with open('video.mp4', 'rb') as f:
            response = requests.post(
                'https://liveapi1.streamlit.app/',
                files={'file': f},
                data={
                    'action': 'upload',
                    'filename': 'video.mp4'
                }
            )
        
        # Mulai streaming
        response = requests.post(
            'https://liveapi1.streamlit.app/',
            data={
                'action': 'start_stream',
                'filename': 'video.mp4',
                'stream_key': 'YOUR_STREAM_KEY',
                'is_shorts': 'false'
            }
        )
        ```
        
        **Endpoint yang Tersedia:**
        - Upload: POST dengan parameter `action=upload` dan `filename`
        - Start Stream: POST dengan parameter `action=start_stream`
        - Stop Stream: POST dengan parameter `action=stop_stream`
        - Get Status: POST dengan parameter `action=get_status`
        - Get Logs: POST dengan parameter `action=get_logs`
        - List Videos: POST dengan parameter `action=list_videos`
        
        Semua request dikirim ke URL utama: `https://liveapi1.streamlit.app/`
        
        **Contoh URL dengan Parameters:**
        - Upload: `https://liveapi1.streamlit.app/?action=upload&filename=test.mp4`
        - Status: `https://liveapi1.streamlit.app/?action=get_status`
        """)
        
        # Test API Form
        st.subheader("🧪 Test API")
        with st.expander("Test API Actions"):
            action = st.selectbox("Pilih Action", [
                "get_status", "get_logs", "list_videos", "stop_stream"
            ])
            
            if st.button("Execute API Call"):
                result = handle_api_request(action)
                st.json(result)

if __name__ == '__main__':
    main()
