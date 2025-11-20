"""
QR-Code Generator für PISA-Befragungen

Erstellt QR-Codes für HTML-Formulare.
"""

from io import BytesIO
import qrcode
from PIL import Image, ImageDraw, ImageFont


def generate_qr_code(url: str, with_logo: bool = False) -> BytesIO:
    """
    Erstellt QR-Code für Formular-URL.

    Args:
        url: URL zum HTML-Formular
        with_logo: Ob ein Logo in der Mitte eingefügt werden soll

    Returns:
        BytesIO object mit PNG-Bild
    """

    # QR Code erstellen
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,  # High error correction
        box_size=10,
        border=4,
    )

    qr.add_data(url)
    qr.make(fit=True)

    # Image erstellen
    img = qr.make_image(fill_color="black", back_color="white")
    img = img.convert('RGB')

    # Optional: Logo in der Mitte (funktioniert durch error correction)
    if with_logo:
        # Erstelle einfaches Text-Logo
        logo_size = img.size[0] // 5
        logo = Image.new('RGB', (logo_size, logo_size), 'white')
        draw = ImageDraw.Draw(logo)

        # Zeichne Rahmen
        draw.rectangle([(0, 0), (logo_size-1, logo_size-1)], outline='black', width=3)

        # Text "PISA"
        try:
            # Versuche größere Schrift
            font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", logo_size // 4)
        except:
            # Fallback zu default font
            font = ImageFont.load_default()

        text = "PISA"
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        position = ((logo_size - text_width) // 2, (logo_size - text_height) // 2)
        draw.text(position, text, fill='black', font=font)

        # Logo in Mitte einfügen
        logo_pos = ((img.size[0] - logo_size) // 2, (img.size[1] - logo_size) // 2)
        img.paste(logo, logo_pos)

    # Save to BytesIO
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)

    return buffer


def generate_qr_code_with_instructions(url: str, scale_title: str) -> BytesIO:
    """
    Erstellt QR-Code mit Text-Anleitung drumherum.

    Args:
        url: URL zum Formular
        scale_title: Titel der Skala

    Returns:
        BytesIO object mit PNG-Bild
    """

    # QR Code erstellen
    qr_buffer = generate_qr_code(url, with_logo=True)
    qr_img = Image.open(qr_buffer)

    # Größeres Bild mit Platz für Text
    width = 800
    height = 1000
    canvas = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(canvas)

    # QR Code in Mitte
    qr_size = 600
    qr_img = qr_img.resize((qr_size, qr_size), Image.Resampling.LANCZOS)
    qr_pos = ((width - qr_size) // 2, 150)
    canvas.paste(qr_img, qr_pos)

    # Fonts
    try:
        title_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 40)
        text_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 24)
        small_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 18)
    except:
        title_font = ImageFont.load_default()
        text_font = ImageFont.load_default()
        small_font = ImageFont.load_default()

    # Title
    title = f"📊 {scale_title}"
    bbox = draw.textbbox((0, 0), title, font=title_font)
    title_width = bbox[2] - bbox[0]
    draw.text(((width - title_width) // 2, 50), title, fill='black', font=title_font)

    # Instructions
    instruction = "Scanne den QR-Code mit deinem Handy"
    bbox = draw.textbbox((0, 0), instruction, font=text_font)
    inst_width = bbox[2] - bbox[0]
    draw.text(((width - inst_width) // 2, 800), instruction, fill='black', font=text_font)

    # URL (klein, am unteren Rand)
    url_text = url[:50] + "..." if len(url) > 50 else url
    bbox = draw.textbbox((0, 0), url_text, font=small_font)
    url_width = bbox[2] - bbox[0]
    draw.text(((width - url_width) // 2, 900), url_text, fill='gray', font=small_font)

    # PISA 2022 watermark
    watermark = "Basierend auf PISA 2022"
    bbox = draw.textbbox((0, 0), watermark, font=small_font)
    wm_width = bbox[2] - bbox[0]
    draw.text(((width - wm_width) // 2, 950), watermark, fill='lightgray', font=small_font)

    # Save
    buffer = BytesIO()
    canvas.save(buffer, format='PNG')
    buffer.seek(0)

    return buffer
