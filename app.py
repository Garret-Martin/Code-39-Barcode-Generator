from flask import Flask, render_template, request, jsonify, session
from flask_session import Session
import barcode
from barcode.writer import ImageWriter
from io import BytesIO
import base64
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Set a secret key for session encryption

# Configure server-side session
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

@app.route('/barcode_pages')
def barcode_pages():
    barcode_pages = session.get('barcode_pages', [])
    return render_template('barcode_pages.html', barcode_pages=barcode_pages)

def generate_barcode_image(code):
    rv = BytesIO()
    barcode_class = barcode.get_barcode_class('code39')
    barcode_instance = barcode_class(code, writer=ImageWriter(), add_checksum=False)
    barcode_instance.write(rv)
    return rv

def generate_barcode_pages(codes):
    barcode_pages = []
    for code in codes:
        if "PIN:" in code:
            main_code, pin = code.split(" PIN:")
            barcode_img_code = generate_barcode_image(main_code.strip())
            barcode_img_pin = generate_barcode_image(pin.strip())
            
            barcode_base64_code = base64.b64encode(barcode_img_code.getvalue()).decode('utf-8')
            barcode_base64_pin = base64.b64encode(barcode_img_pin.getvalue()).decode('utf-8')
            
            barcode_pages.append({
                'value': code,
                'barcode_base64_code': barcode_base64_code,
                'barcode_base64_pin': barcode_base64_pin
            })
        else:
            barcode_img = generate_barcode_image(code)
            barcode_base64 = base64.b64encode(barcode_img.getvalue()).decode('utf-8')
            barcode_pages.append({'value': code, 'barcode_base64': barcode_base64})
    return barcode_pages


@app.route('/generate_barcodes', methods=['POST'])
def generate_barcodes():
    try:
        data = request.json
        codes = data.get('codes', [])
        barcode_pages = generate_barcode_pages(codes)
        session['barcode_pages'] = barcode_pages  # Store in session
        return jsonify(success=True)
    except Exception as e:
        app.logger.error(f"Error generating barcodes: {e}")
        return jsonify(success=False)

@app.route('/generate_preview', methods=['POST'])
def generate_preview():
    try:
        data = request.json
        codes = data.get('codes', [])
        barcode_pages = generate_barcode_pages(codes)
        return jsonify(success=True, barcodes=barcode_pages)
    except Exception as e:
        app.logger.error(f"Error generating barcode preview: {e}")
        return jsonify(success=False)

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
