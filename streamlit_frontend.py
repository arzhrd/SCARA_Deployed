import streamlit as st
import requests
import time

# --- Page Configuration ---
st.set_page_config(
    page_title="SCARA Robot Control",
    page_icon="🤖",
    layout="wide"
)

# --- State Management ---
if 'robot_state' not in st.session_state:
    st.session_state.robot_state = {
        "servo1": 90,
        "servo3": 90,
        "servo4": 90,
        "gripper": "Release",
        "hand_detected": False,
        "current_control": "Servo 1",
        "is_recording": False,
        "is_playing": False,
        "hand_gesture_enabled": True
    }

# --- Backend API ---
# This URL is now set to your specific ngrok tunnel
BACKEND_URL = "https://kayden-mitochondrial-demetria.ngrok-free.dev" 

if BACKEND_URL == "YOUR_NGROK_URL_HERE":
    st.error("Please update the `BACKEND_URL` in `streamlit_frontend.py` with your live ngrok URL.")
    st.stop()

API_ENDPOINTS = {
    "command": f"{BACKEND_URL}/command",
    "status": f"{BACKEND_URL}/status",
    "video": f"{BACKEND_URL}/video_feed"
}

def send_command(payload):
    """Sends a command to the Flask backend."""
    try:
        response = requests.post(API_ENDPOINTS["command"], json=payload, timeout=5)
        response.raise_for_status() # Raise an exception for bad status codes
        return response.json()
    except requests.exceptions.RequestException as e:
        st.toast(f"Error: Could not connect to robot server. Is it running? Is ngrok correct? Error: {e}", icon="🔥")
        return None

def update_status():
    """Polls the backend for the latest robot state."""
    try:
        response = requests.get(API_ENDPOINTS["status"], timeout=3)
        response.raise_for_status()
        st.session_state.robot_state = response.json()
    except requests.exceptions.RequestException:
        pass # Fail silently on auto-refresh

# --- UI Layout ---
st.title("🤖 SCARA Robot Control Panel")
st.caption(f"Connected to: `{BACKEND_URL}`")

col1, col2 = st.columns(2)

with col1:
    st.header("Camera Feed")
    # We add a timestamp to the URL to try and bust caching
    video_url = f"{API_ENDPOINTS['video']}?_t={time.time()}"
    st.image(video_url, use_column_width=True, caption="Live Robot View")

with col2:
    st.header("Status & Mode")
    
    # Status Indicators
    state = st.session_state.robot_state
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Hand Detected", "YES" if state["hand_detected"] else "NO")
    c2.metric("Recording", "ON" if state["is_recording"] else "OFF")
    c3.metric("Playing", "ON" if state["is_playing"] else "OFF")
    c4.metric("Gestures", "ON" if state["hand_gesture_enabled"] else "OFF")
    
    st.text(f"Gesture Control Target: {state['current_control']}")
    
    st.divider()

    # --- Manual Controls ---
    st.header("Manual Controls")
    
    if st.button("Toggle Hand Gesture Control", use_container_width=True, type="primary" if state["hand_gesture_enabled"] else "secondary"):
        send_command({"command": "toggle_gesture"})

    # Sliders
    s1_val = st.slider(
        "Servo 1 (Base, 0-180)", 0, 180, 
        value=int(st.session_state.robot_state.get('servo1', 90)),
        key="s1_slider"
    )
    if s1_val != int(st.session_state.robot_state.get('servo1', 90)):
         send_command({"command": "set_servo_1", "value": s1_val})

    s3_val = st.slider(
        "Servo 3 (Link 3, 0-180)", 0, 180, 
        value=int(st.session_state.robot_state.get('servo3', 90)),
        key="s3_slider"
    )
    if s3_val != int(st.session_state.robot_state.get('servo3', 90)):
        send_command({"command": "set_servo_3", "value": s3_val})

    s4_val = st.slider(
        "Servo 4 (Link 4, 0-180)", 0, 180, 
        value=int(st.session_state.robot_state.get('servo4', 90)),
        key="s4_slider"
    )
    if s4_val != int(st.session_state.robot_state.get('servo4', 90)):
        send_command({"command": "set_servo_4", "value": s4_val})

    # Linear Actuator Buttons
    st.subheader("Servo 2 (Linear Actuator)")
    b1, b2, b3 = st.columns(3)
    if b1.button("Up", use_container_width=True):
        send_command({"command": "linear_actuator", "value": "up"})
    if b2.button("Stop", use_container_width=True):
        send_command({"command": "linear_actuator", "value": "stop"})
    if b3.button("Down", use_container_width=True):
        send_command({"command": "linear_actuator", "value": "down"})

    # Gripper
    st.subheader("Gripper")
    g1, g2 = st.columns(2)
    if g1.button("Hold (Grip)", use_container_width=True):
        send_command({"command": "gripper", "value": "Hold"})
    if g2.button("Release", use_container_width=True):
        send_command({"command": "gripper", "value": "Release"})

# --- Playback Controls ---
st.divider()
st.header("Recording & Playback")

rec_col1, rec_col2 = st.columns(2)
with rec_col1:
    if st.button("🔴 Start Recording", use_container_width=True, disabled=state["is_recording"]):
        send_command({"command": "start_recording"})
with rec_col2:
    if st.button("⏹️ Stop Recording", use_container_width=True, disabled=not state["is_recording"]):
        send_command({"command": "stop_recording"})

play_col1, play_col2, play_col3 = st.columns([1,1,2])
with play_col1:
    loops = st.number_input("Loops", 1, 100, 1)
with play_col2:
    speed = st.slider("Speed", 0.0, 10.0, 5.0, 0.5) # 0=Slow, 5=Normal, 10=Fast

with play_col3:
    if st.button("▶️ Play Recording", use_container_width=True, disabled=state["is_playing"]):
        send_command({"command": "play_recording", "loops": loops, "speed": speed})
    if st.button("⏹️ Stop Playback", use_container_width=True, disabled=not state["is_playing"]):
        send_command({"command": "stop_playback"})


# --- Auto-polling ---
# This small piece of JavaScript will force Streamlit to rerun every second,
# which in turn calls update_status()
st.html("""
    <script>
        var streamlitDoc = window.parent.document;
        var toolbarButton = streamlitDoc.querySelector('.stApp [data-testid="stToolbar"] > button');
        
        // Only run if the button is found
        if (toolbarButton) {
            setInterval(function() {
                // Check if the button is not already in a 'running' state
                if (!toolbarButton.closest('.stApp').classList.contains('streamlit-running')) {
                    toolbarButton.click();
                }
            }, 1000); // Rerun every 1000ms (1 second)
        }
    </script>
""")

# Call the update function on every rerun
update_status()

