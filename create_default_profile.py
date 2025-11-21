from PIL import Image, ImageDraw
import os

def create_default_profile():
    # Create a 300x360 image with white background
    width = 300
    height = 360
    img = Image.new('RGB', (width, height), '#f8f9fa')  # Light gray background
    draw = ImageDraw.Draw(img)
    
    # Add a simple silhouette
    # Draw head
    draw.ellipse([width//2-50, 50, width//2+50, 150], fill='#dee2e6')  # Gray color
    # Draw body
    draw.polygon([
        width//2-60, 160,  # Left shoulder
        width//2+60, 160,  # Right shoulder
        width//2+80, 360,  # Right bottom
        width//2-80, 360   # Left bottom
    ], fill='#dee2e6')
    
    # Save the image
    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'images')
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, 'default-profile.png')
    img.save(output_path)
    print(f"Created default profile picture at: {output_path}")

if __name__ == '__main__':
    create_default_profile()