import os, uuid, subprocess, threading, time
from flask import Flask, request, render_template, send_file, jsonify

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
PROCESSED_FOLDER = 'processed'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)

def compress_video(input_path, output_path):
    cmd = ['ffmpeg', '-i', input_path, '-vcodec', 'libx264', '-crf', '28', 
           '-preset', 'fast', '-acodec', 'aac', '-b:a', '128k', output_path, '-y']
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def delete_after_delay(path, delay=3600):
    def delete():
        time.sleep(delay)
        if os.path.exists(path): os.remove(path)
    threading.Thread(target=delete).start()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return jsonify({'error': 'No file'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    unique_id = str(uuid.uuid4())
    ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else 'mp4'
    input_path = os.path.join(UPLOAD_FOLDER, f"{unique_id}_input.{ext}")
    output_path = os.path.join(PROCESSED_FOLDER, f"{unique_id}_compressed.mp4")
    
    file.save(input_path)
    compress_video(input_path, output_path)
    os.remove(input_path)
    delete_after_delay(output_path)
    
    return jsonify({'download_url': f'/download/{unique_id}'})

@app.route('/download/<unique_id>')
def download(unique_id):
    path = os.path.join(PROCESSED_FOLDER, f"{unique_id}_compressed.mp4")
    return send_file(path, as_attachment=True)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
