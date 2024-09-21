from flask import Flask, request, send_file, jsonify
from PIL import Image, ImageFilter, ImageDraw
from concurrent.futures import ThreadPoolExecutor
from flask import Flask, request, jsonify, send_file
import cv2
import numpy as np
from io import BytesIO
from PIL import Image

app = Flask(__name__)


# Function to apply Gaussian blur and draw circles
def process_image_pipeline(image, blur_radius=2, luminance_scale=10, spacing=10, color=(0, 0, 0)):
    image = image.filter(ImageFilter.GaussianBlur(blur_radius))

    rgb_image = image.convert('RGB')
    width, height = rgb_image.size
    canvas = Image.new("RGB", (width, height), color)
    draw = ImageDraw.Draw(canvas)

    for y in range(0, height, spacing):
        for x in range(0, width, spacing):
            r, g, b = rgb_image.getpixel((x, y))
            luminance = 0.2126 * r + 0.7152 * g + 0.0722 * b
            luminance /= luminance_scale
            draw.ellipse((x - luminance, y - luminance, x + luminance, y + luminance), fill=(r, g, b))
            #draw.rectangle((x - luminance, y - luminance, x + luminance, y + luminance), fill=(r, g, b))

    return canvas


@app.route('/process-image', methods=['POST'])
def process_image():
    try:
        # Receive image file and parameters from request
        image_file = request.files.get('image')
        if not image_file:
            return jsonify({"error": "No image provided"}), 400

        luminance_scale = int(request.form.get('luminance_scale', 35))
        spacing = int(request.form.get('spacing', 10))
        blur_radius = int(request.form.get('blur_radius', 3))
        color = tuple(map(int, request.form.get('color', '0,0,0').split(',')))
        scale_factor = float(request.form.get('scale_factor', 1.0))  # Add scale factor

        # Open and resize the image if necessary
        image = Image.open(image_file)
        if scale_factor != 1.0:
            new_size = (int(image.width * scale_factor), int(image.height * scale_factor))
            image = image.resize(new_size, Image.Resampling.LANCZOS)

        # Process the image in a thread pool for parallel processing
        with ThreadPoolExecutor() as executor:
            future_image = executor.submit(process_image_pipeline, image, blur_radius, luminance_scale, spacing, color)
            final_image = future_image.result()

            # Save the processed image temporarily
            output_path = 'Output.jpg'
            final_image.save(output_path)

            return send_file(output_path, mimetype='image/jpeg')
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def edge_detection(image, low_threshold=100, high_threshold=200):
    """Perform Canny edge detection."""
    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray_image, low_threshold, high_threshold)
    return edges


@app.route('/upload', methods=['POST'])
def upload_image():
    """API endpoint for uploading an image and performing edge detection."""
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    try:
        # Read the image
        image = Image.open(file.stream)
        image = np.array(image)

        # Perform edge detection
        edges = edge_detection(image)

        # Convert the edge-detected image to a PIL image and return as a response
        pil_image = Image.fromarray(edges)
        img_io = BytesIO()
        pil_image.save(img_io, 'PNG')
        img_io.seek(0)

        return send_file(img_io, mimetype='image/png')

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
