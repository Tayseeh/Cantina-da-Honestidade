"""Serviços de validação e armazenamento de imagens do Confia+."""

import os
import shutil
import uuid
from io import BytesIO

from PIL import Image, ImageOps, UnidentifiedImageError

# Caminho absoluto da raiz do projeto: media_service.py fica na própria raiz.
# As fotos precisam ficar dentro de static/uploads para serem servidas pelo Flask.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def migrate_legacy_product_photos():
    """Copia fotos existentes do caminho antigo para a pasta pública correta."""
    legacy_folder = os.path.join(os.path.dirname(BASE_DIR), "static", "uploads", "produtos")
    current_folder = os.path.join(BASE_DIR, "static", "uploads", "produtos")
    if not os.path.isdir(legacy_folder):
        return
    os.makedirs(current_folder, exist_ok=True)
    for filename in os.listdir(legacy_folder):
        source = os.path.join(legacy_folder, filename)
        destination = os.path.join(current_folder, filename)
        if os.path.isfile(source) and not os.path.exists(destination):
            try:
                shutil.copy2(source, destination)
            except OSError:
                # Uma falha na cópia de uma foto antiga não deve impedir o app de iniciar.
                continue


def process_profile_photo(upload):
    """Valida, processa e salva a foto enviada para o perfil do usuário."""
    if not upload or not upload.filename:
        return None
    upload.stream.seek(0, os.SEEK_END)
    size = upload.stream.tell()
    upload.stream.seek(0)
    if size == 0 or size > 4 * 1024 * 1024:
        raise ValueError("A foto deve ter até 4 MB.")

    # Lê os bytes uma única vez para validar e depois normalizar a imagem.
    raw = upload.read()
    try:
        with Image.open(BytesIO(raw)) as image:
            if image.format not in {"JPEG", "PNG", "WEBP"}:
                raise ValueError("Envie uma foto JPG, PNG ou WebP.")
            if image.width * image.height > 20_000_000:
                raise ValueError("A imagem é grande demais. Escolha uma foto menor.")
            image.verify()
        with Image.open(BytesIO(raw)) as image:
            image = ImageOps.exif_transpose(image)
            # Padroniza dimensões e formato para reduzir espaço e evitar arquivos enormes.
            image.thumbnail((512, 512))
            if "A" in image.getbands():
                background = Image.new("RGB", image.size, "white")
                background.paste(image, mask=image.getchannel("A"))
                image = background
            else:
                image = image.convert("RGB")
            output = BytesIO()
            image.save(output, format="JPEG", quality=88, optimize=True)
            return output.getvalue()
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError) as error:
        raise ValueError("Não foi possível ler essa imagem. Escolha um arquivo JPG, PNG ou WebP válido.") from error


def store_product_photo(image_bytes):
    """Processa e armazena a imagem enviada para um produto."""
    if image_bytes is None:
        return "", None
    photo_folder = os.path.join(BASE_DIR, "static", "uploads", "produtos")
    os.makedirs(photo_folder, exist_ok=True)
    # Nome aleatório evita colisões e não expõe o nome original enviado pelo usuário.
    filename = f"{uuid.uuid4().hex}.jpg"
    disk_path = os.path.join(photo_folder, filename)
    with open(disk_path, "wb") as photo_file:
        photo_file.write(image_bytes)
    return f"uploads/produtos/{filename}", disk_path
