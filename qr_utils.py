import os
import qrcode
from PIL import Image

def generate_qr_code(challan_number, public_url, qr_folder):
    """
    Generates a high-contrast QR code for the given public URL
    and saves it to qr_folder with filename {challan_number}.png.
    Returns the filename.
    """
    os.makedirs(qr_folder, exist_ok=True)
    filename = f"{challan_number}.png"
    filepath = os.path.join(qr_folder, filename)

    # Initialize QR Code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=3,
    )
    qr.add_data(public_url)
    qr.make(fit=True)

    # Using high-contrast dark forest color #1b4332 on white for reliable scanning & theme match
    img = qr.make_image(fill_color="#1b4332", back_color="#ffffff")
    img.save(filepath)

    return filename
