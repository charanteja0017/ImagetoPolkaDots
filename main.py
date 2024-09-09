from flask import Flask, request, send_file, jsonify
from PIL import Image, ImageFilter, ImageDraw
import time
import os
from concurrent.futures import ThreadPoolExecutor

app = Flask(__name__)

def gaussian_blur(image, radius=2):
    try:
        blurred_image = image.filter(ImageFilter.GaussianBlur(radius))
        return blurred_image
    except Exception as e:
        print("An error occurred in Gaussian blur:", e)

def draw_circles(image, luminance_scale=10, spacing=10, color=(0, 0, 0)):
    try:
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
        return canvas
    except Exception as e:
        print("An error occurred in drawing circles:", e)

@app.route('/process-image', methods=['POST'])
def process_image():
    try:
        # Receive image file and parameters from request
        image_file = request.files.get('image')
        luminance_scale = int(request.form.get('luminance_scale', 35))
        spacing = int(request.form.get('spacing', 10))
        blur_radius = int(request.form.get('blur_radius', 3))
        color = tuple(map(int, request.form.get('color', '0,0,0').split(',')))

        if not image_file:
            return jsonify({"error": "No image provided"}), 400

        # Open the image
        image = Image.open(image_file)

        # Process the image in a multithreaded way
        with ThreadPoolExecutor() as executor:
            future_blur = executor.submit(gaussian_blur, image, blur_radius)
            blurred_image = future_blur.result()

            if blurred_image:
                future_draw = executor.submit(draw_circles, blurred_image, luminance_scale, spacing, color)
                final_image = future_draw.result()

                # Save the processed image temporarily
                output_path = 'Output.jpg'
                final_image.save(output_path)

                return send_file(output_path, mimetype='image/jpeg')
        return jsonify({"error": "Image processing failed"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)


'''
Import this to post man to test this out 
curl -X POST http://127.0.0.1:5000/process-image `
-F "image=@E:\SNEH1408.jpeg" `
-F "luminance_scale=35" `
-F "spacing=10" `
-F "blur_radius=3" `
-F "color=0,0,0" `
-OutFile processed_image.jpg
'''