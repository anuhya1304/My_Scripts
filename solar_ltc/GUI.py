# main.py
import subprocess
import webview
import threading

# Function to run the Streamlit app
def run_streamlit():
    subprocess.run(["streamlit", "run", "dataset_db.py", "--server.headless", "true"])

# Function to launch the webview window
def create_window():
    webview.create_window("Streamlit GUI", "http://localhost:8501")
    webview.start()

# Start Streamlit in a separate thread
thread = threading.Thread(target=run_streamlit)
thread.start()

# Create and display the GUI window
create_window()
