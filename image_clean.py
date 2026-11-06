"""Remove only pale red specimen watermarks before OCR. Preserve dark text."""
from PIL import Image

def clean(source,target):
    image=Image.open(source).convert('RGB')
    if image.width*image.height>16000000: raise ValueError('Image resolution too large')
    r,g,b=image.split()
    # LUT operations stay in Pillow, avoiding a NumPy dependency.
    from PIL import ImageChops
    red_excess=ImageChops.subtract(r,g).point(lambda x:255 if x>10 else 0)
    blue_excess=ImageChops.subtract(r,b).point(lambda x:255 if x>10 else 0)
    pale=r.point(lambda x:255 if x>150 else 0)
    pale_g=g.point(lambda x:255 if x>100 else 0)
    mask=ImageChops.multiply(ImageChops.multiply(red_excess,blue_excess),ImageChops.multiply(pale,pale_g))
    image.paste((255,255,255),mask=mask)
    image.save(target,'PNG')
