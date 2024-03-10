from PIL import Image, ImageFilter, ImageDraw
import time

def timer_start():
    global start_time
    start_time = time.time()

def timer_stop():
    if 'start_time' in globals():
        elapsed_time = time.time() - start_time
        print(f"Elapsed time: {elapsed_time:.2f} seconds")
    else:
        print("Timer was not started.")

def gaussian_blur(image_path, radius=2):
    try:
        image = Image.open(image_path)
        blurred_image = image.filter(ImageFilter.GaussianBlur(radius))
        return blurred_image
    except Exception as e:
        print("An error occurred:", e)

def draw_circles(image, luminance_scale=10, spacing=10):
    try:
        rgb_image = image.convert('RGB')
        width, height = rgb_image.size
        # Create a new black canvas with the same size as the original image
        canvas = Image.new("RGB", (width, height), color=(0,0,0))
        draw = ImageDraw.Draw(canvas)

        for y in range(0, height, spacing):
            for x in range(0, width, spacing):
                r, g, b = rgb_image.getpixel((x, y))
                luminance = 0.2126 * r + 0.7152 * g + 0.0722 * b
                luminance /= luminance_scale
                color = (r, g, b)
                draw.ellipse((x-luminance, y-luminance, x+luminance, y+luminance), fill=color)
    except Exception as e:
        print("An error occurred:", e)
    return canvas

if __name__ == "__main__":
    timer_start()
    image_path = r'C:\Users\chara\PycharmProjects\ImagetoPolkaDots\venv\Resources\input_4.png'
    output_path= r'C:\Users\chara\PycharmProjects\ImagetoPolkaDots\venv\Output\output.jpeg'
    #parameters
    luminance_scale=35 # best values b/w 20-50
    spacing=10  # best values b/w 8-15
    blur_radius = 8 # best values b/w 5-10

    blurred_image = gaussian_blur(image_path, 8)

    if blurred_image:
        f=draw_circles(blurred_image,luminance_scale,spacing)#default values are luminance_scale: 10, spacing: 10
        f.save(output_path)
        f.show()
        print(f"Image with drawn circles saved to: {output_path}")
    timer_stop()
