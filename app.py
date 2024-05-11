from flask import Flask, request, render_template, send_from_directory, jsonify
from PIL import Image
from pydub import AudioSegment
import os
import io

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads/'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif', 'mp3', 'wav'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload_image', methods=['POST'])
def upload_image():
    file = request.files['file']
    compress_factor = int(request.form['compress_factor'])
    if file and allowed_file(file.filename):
        original_stream = file.stream.read()
        original_size = len(original_stream)
        file.stream.seek(0)  # Reset stream position
        img = Image.open(file.stream)
        img_format = img.format
        compressed_image, final_size = compress_image(img, compress_factor)
        compressed_filename = f"compressed_{file.filename}"
        compressed_path = os.path.join(app.config['UPLOAD_FOLDER'], compressed_filename)
        compressed_image.save(compressed_path, format=img_format)
        return render_template('results.html', original_size=original_size, final_size=final_size, filename=compressed_filename, type='image')
    return 'File not allowed', 400

@app.route('/upload_audio', methods=['POST'])
def upload_audio():
    file = request.files['file']
    compress_factor = int(request.form['compress_factor'])
    if file and allowed_file(file.filename):
        original_stream = file.stream.read()
        original_size = len(original_stream)
        file.stream.seek(0)
        compressed_audio, final_size = compress_audio(file.stream, compress_factor)
        compressed_filename = f"compressed_{file.filename}"
        compressed_path = os.path.join(app.config['UPLOAD_FOLDER'], compressed_filename)
        compressed_audio.export(compressed_path, format="mp3")
        return render_template('results.html', original_size=original_size, final_size=final_size, filename=compressed_filename, type='audio')
    return 'File not allowed', 400

def compress_image(img, compress_factor):
    quality = max(10, 95 - 30 * compress_factor)
    output_stream = io.BytesIO()
    
    # Convert image to RGB if it is in RGBA mode
    if img.mode == 'RGBA':
        img = img.convert('RGB')
    
    img.save(output_stream, format='JPEG', quality=quality)
    final_size = output_stream.tell()
    output_stream.seek(0)
    img = Image.open(output_stream)
    return img, final_size

def compress_audio(stream, compress_factor):
    bitrate_options = ['64k', '48k', '32k']
    sound = AudioSegment.from_file(stream)
    compressed_audio = sound.set_frame_rate(22050)
    final_bitrate = bitrate_options[min(compress_factor - 1, len(bitrate_options) - 1)]
    output_stream = io.BytesIO()
    compressed_audio.export(output_stream, format="mp3", bitrate=final_bitrate)
    final_size = output_stream.tell()
    return compressed_audio, final_size

@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    app.run(debug=True)
