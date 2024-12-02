from flask import Flask, request, send_file, jsonify
from PIL import Image, ImageFilter, ImageDraw
from concurrent.futures import ThreadPoolExecutor
import cv2
import numpy as np
import torch
from io import BytesIO
import cupy as cp  # Use CuPy for GPU-bound image processing
from PIL import ImageFont

app = Flask(__name__)


#global parmas


# Function to apply Gaussian blur and draw circles (GPU-bound)
def process_image_pipeline(image, blur_radius=2, luminance_scale=10, spacing=10, color=(0, 0, 0)):
    # Convert image to numpy array
    np_image = np.array(image)

    # Use CuPy for GPU processing (convert numpy array to CuPy array)
    cp_image = cp.array(np_image)

    # Apply Gaussian blur using OpenCV's CUDA backend (if available)
    #cp_image = cv2.cuda_GaussianBlur(cp_image, (blur_radius * 2 + 1, blur_radius * 2 + 1), 0)
    blur_kernel_size = (blur_radius * 2 + 1, blur_radius * 2 + 1)
    cp_image = cv2.blur(np_image, blur_kernel_size)

    # Convert back to CPU to work with Pillow for drawing
    np_image = cp.asnumpy(cp_image)
    rgb_image = Image.fromarray(np_image).convert('RGB')

    width, height = rgb_image.size
    canvas = Image.new("RGB", (width, height), color)
    draw = ImageDraw.Draw(canvas)
    for y in range(0, height, spacing):
        for x in range(0, width, spacing):
            r, g, b = rgb_image.getpixel((x, y))
            #luminance = 0.2126 * r + 0.7152 * g + 0.0722 * b
            #luminance /= luminance_scale
            luminance = spacing
            #draw.ellipse((x - luminance, y - luminance, x + luminance, y + luminance), fill=(r, g, b))
            #draw.rectangle((x - luminance, y - luminance, x + luminance, y + luminance), fill=(r, g, b))
            draw.rectangle((x - luminance, y - luminance, x , y ), fill=(r, g, b),outline=(0, 0, 0))
            font = ImageFont.load_default()  # Default font
            #hex_color = f"#{r:02x}{g:02x}{b:02x}"
            #text in the box
            text = f"box : \n [{int(y/luminance)},{int(x/luminance)}] \n#{r:02x}{g:02x}{b:02x}"

            # Calculate the text bounding box
            text_bbox = draw.textbbox((0, 0), text, font=font)
            text_width, text_height = text_bbox[2] - text_bbox[0], text_bbox[3] - text_bbox[1]

            # Set the text position to the top-left corner of the square
            text_x = x - luminance +5 # x-coordinate of the top-left corner of the square
            text_y = y - luminance  # y-coordinate of the top-left corner of the square

            # Draw the text in the top-left corner of the square
            draw.text((text_x, text_y), text, fill=(0, 0, 0), font=font)




    return canvas


@app.route('/process-image', methods=['POST'])
def process_image():
    try:
        image_file = request.files.get('image')
        if not image_file:
            return jsonify({"error": "No image provided"}), 400

        luminance_scale = int(request.form.get('luminance_scale', 35))
        spacing = int(request.form.get('spacing', 10))
        blur_radius = int(request.form.get('blur_radius', 3))
        color = tuple(map(int, request.form.get('color', '0,0,0').split(',')))
        scale_factor = float(request.form.get('scale_factor', 1.0))

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


# GPU-accelerated edge detection using OpenCV with CUDA
def edge_detection(image, low_threshold=100, high_threshold=200):
    """Perform Canny edge detection using GPU."""
    # Convert image to grayscale
    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Upload image to GPU (CUDA Mat)
    gpu_image = cv2.cuda_GpuMat()
    gpu_image.upload(gray_image)

    # Perform edge detection using CUDA-accelerated Canny
    edges_gpu = cv2.cuda_Canny(gpu_image, low_threshold, high_threshold)

    # Download result back to CPU
    edges = edges_gpu.download()

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



