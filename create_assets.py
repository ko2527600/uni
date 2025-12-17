from PIL import Image, ImageDraw
import os
import random

print("🎨 SYSTEM CHECK: Starting Asset Generator...")

# 1. Create the folder if it's missing
static_folder = os.path.join('app', 'static')
if not os.path.exists(static_folder):
    os.makedirs(static_folder)
    print(f"📂 Created missing folder: {static_folder}")
else:
    print(f"📂 Found folder: {static_folder}")

# 2. Generate LOGO
print("... Drawing Logo ...")
try:
    size = (500, 500)
    img = Image.new('RGBA', size, (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)
    draw.ellipse([50, 50, 450, 450], fill='#2575fc') # Blue Circle
    draw.rectangle([150, 150, 200, 350], fill='white') # U Shape Left
    draw.rectangle([300, 150, 350, 350], fill='white') # U Shape Right
    draw.pieslice([150, 250, 350, 400], 0, 180, fill='white') # U Shape Bottom
    
    logo_path = os.path.join(static_folder, 'logo.png')
    img.save(logo_path)
    print(f"✅ Logo Saved: {logo_path}")
except Exception as e:
    print(f"❌ Error creating Logo: {e}")

# 3. Generate BACKGROUND
print("... Painting Background ...")
try:
    width, height = 1920, 1080
    img = Image.new('RGB', (width, height), '#667eea')
    draw = ImageDraw.Draw(img)
    # Draw abstract bubbles
    for _ in range(20):
        x = random.randint(-200, width)
        y = random.randint(-200, height)
        r = random.randint(200, 600)
        color = (random.randint(100, 200), random.randint(100, 200), 255, 50)
        overlay = Image.new('RGBA', (width, height), (0,0,0,0))
        over_draw = ImageDraw.Draw(overlay)
        over_draw.ellipse([x, y, x+r, y+r], fill=color)
        img = Image.blend(img.convert('RGBA'), overlay, 0.3).convert('RGB')

    bg_path = os.path.join(static_folder, 'background.jpg')
    img.save(bg_path)
    print(f"✅ Background Saved: {bg_path}")
except Exception as e:
    print(f"❌ Error creating Background: {e}")

print("🚀 DONE! Check your app/static folder now.")