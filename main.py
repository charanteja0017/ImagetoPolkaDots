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

def draw_circles(image, luminance_scale=10, spacing=10,color=(0,0,0)):
    try:
        rgb_image = image.convert('RGB')
        width, height = rgb_image.size
        # Create a new black canvas with the same size as the original image
        canvas = Image.new("RGB", (width, height), color)
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
    # file prameters
    image_path = r'C:\Users\chara\PycharmProjects\ImagetoPolkaDots\venv\Resources\love.jpg'
    output_path= r'C:\Users\chara\PycharmProjects\ImagetoPolkaDots\venv\Output\output.jpeg'
    #parameters
    luminance_scale=35 # best values b/w 20-50
    spacing=10  # best values b/w 8-15
    blur_radius = 3 # best values b/w 5-10 and make it 0 to keep it original
    color = (0, 0, 0)#for white or any other colour change r, g, & b values here


    blurred_image = gaussian_blur(image_path, blur_radius)

    if blurred_image:
        f=draw_circles(blurred_image,luminance_scale,spacing,color)#default values are luminance_scale: 10, spacing: 10
        f.save(output_path)
        f.show()
        print(f"Image with drawn circles saved to: {output_path}")
    timer_stop()
