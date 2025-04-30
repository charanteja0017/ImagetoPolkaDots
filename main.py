from flask import Flask, request, send_file, jsonify
from PIL import Image, ImageFilter, ImageDraw
from concurrent.futures import ThreadPoolExecutor
import cv2
import numpy as np
import torch
from io import BytesIO
from PIL import ImageFont

app = Flask(__name__)




def process_image_pipeline(image, blur_radius=2, luminance_scale=10, spacing=10, color=(0, 0, 0)):
    np_image = np.array(image)
    height, width = np_image.shape[:2]
    blur_kernel_size = (blur_radius * 2 + 1, blur_radius * 2 + 1)
    np_image = cv2.blur(np_image, blur_kernel_size)
    rgb_weights = np.array([0.299, 0.587, 0.114])
    canvas = np.full((height, width, 3), color, dtype=np.uint8)
    y_coords, x_coords = np.mgrid[0:height:spacing, 0:width:spacing]
    points = np.stack((y_coords.flatten(), x_coords.flatten()), axis=1)
    rgb_values = np_image[points[:, 0], points[:, 1]]
    luminance = np.maximum(1, np.dot(rgb_values, rgb_weights) / 255.0 * spacing)
    for idx, (y, x) in enumerate(points):
        lum = luminance[idx]
        cv2.ellipse(canvas,(x, y),(int(lum), int(lum)),0, 0, 360,rgb_values[idx].tolist(),-1)
    return Image.fromarray(canvas)


@app.route('/process-image', methods=['POST'])
def process_image():
    try:
        if 'image' not in request.files:
            return jsonify({"error": "No image provided"}), 400
        image_file = request.files['image']
        if not image_file.filename:
            return jsonify({"error": "Empty filename"}), 400
        try:
            luminance_scale = int(request.form.get('luminance_scale', 35))
            spacing = int(request.form.get('spacing', 10))
            blur_radius = int(request.form.get('blur_radius', 3))
            color = tuple(int(x) for x in request.form.get('color', '0,0,0').split(','))
            scale_factor = float(request.form.get('scale_factor', 1.0))
        except ValueError as e:
            return jsonify({"error": f"Invalid parameter value: {str(e)}"}), 400
        image = Image.open(image_file)
        if scale_factor != 1.0:
            image = image.resize(tuple(int(dim * scale_factor) for dim in image.size), Image.Resampling.LANCZOS)
        with ThreadPoolExecutor(max_workers=1) as executor:
            final_image = executor.submit(process_image_pipeline, image, blur_radius, luminance_scale, spacing, color).result()
        img_io = BytesIO()
        final_image.save(img_io, format='JPEG', quality=95)
        img_io.seek(0)
        return send_file(img_io, mimetype='image/jpeg', as_attachment=True, download_name='processed.jpg')
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def edge_detection(image, low_threshold=100, high_threshold=200):
    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    gpu_image = cv2.cuda_GpuMat()
    gpu_image.upload(gray_image)
    edges_gpu = cv2.cuda_Canny(gpu_image, low_threshold, high_threshold)
    edges = edges_gpu.download()
    return edges





if __name__ == '__main__':
    app.run(debug=True)



