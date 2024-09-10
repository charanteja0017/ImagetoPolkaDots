from flask import Flask, request, send_file, jsonify
from PIL import Image, ImageFilter, ImageDraw
from concurrent.futures import ThreadPoolExecutor

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


if __name__ == '__main__':
    app.run(debug=True)
