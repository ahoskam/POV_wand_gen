from PIL import Image

# Create a 16x16 black square
size = (16, 16)
blank_image = Image.new('RGBA', size, (0, 0, 0, 255))  # Black, fully opaque

# Save as ICO with multiple sizes
sizes = [(16, 16), (32, 32), (64, 64)]
blank_image.save('pov_wand.ico', format='ICO', sizes=sizes)

print("Black square ICO file 'pov_wand.ico' created successfully!")