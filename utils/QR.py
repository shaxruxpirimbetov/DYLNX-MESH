import io
import boto3
import qrcode
from botocore.config import Config
from decouple import config
from PIL import Image, ImageDraw

# Настройки Cloudflare R2 (лучше вынести в переменные окружения, но для примера можно так)
CLOUDFLARE_ACCOUNT_ID = config("CLOUDFLARE_ACCOUNT_ID")
CLOUDFLARE_ACCESS_KEY_ID = config("CLOUDFLARE_ACCESS_KEY_ID")
CLOUDFLARE_SECRET_ACCESS_KEY = config("CLOUDFLARE_SECRET_ACCESS_KEY")
CLOUDFLARE_R2_BUCKET = config("CLOUDFLARE_R2_BUCKET")
CLOUDFLARE_R2_PUBLIC_URL = config("CLOUDFLARE_R2_PUBLIC_URL")
BACKEND_HERE = config("BACKEND_HERE")

def make(uuid):
    # 1. Настройка параметров QR-кода
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )

    qr.add_data(f"{BACKEND_HERE}/mesh/{uuid}/")
    qr.make(fit=True)

    # Создаем картинку
    img = qr.make_image(fill_color="darkblue", back_color="lightyellow")

    # 2. Сохраняем картинку в оперативную память (вместо жесткого диска)
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)  # Возвращаем указатель в начало файла

    # 3. Инициализируем S3-клиент для подключения к Cloudflare R2
    session = boto3.session.Session()
    s3_client = session.client(
        's3',
        endpoint_url=f"https://{CLOUDFLARE_ACCOUNT_ID}.r2.cloudflarestorage.com",
        aws_access_key_id=CLOUDFLARE_ACCESS_KEY_ID,
        aws_secret_access_key=CLOUDFLARE_SECRET_ACCESS_KEY,
        config=Config(signature_version='s3v4'),
    )

    # Путь файла внутри бакета (например: qrcode/my_code.png)
    file_path = f"qrcode/{uuid}.png"

    # 4. Загружаем файл в Cloudflare R2
    s3_client.upload_fileobj(
        buffer,
        CLOUDFLARE_R2_BUCKET,
        file_path,
        ExtraArgs={'ContentType': 'image/png'}
    )

    # 5. Возвращаем публичную ссылку на загруженный QR-код
    public_url = f"{CLOUDFLARE_R2_PUBLIC_URL}/{file_path}"
    return public_url

import segno

def generate_custom_qr(value):
    # Создаем QR-код с высоким уровнем коррекции
    qr = segno.make_qr(value, error='h')
    matrix = qr.matrix

    scale = 20      # Размер модуля в пикселях
    border = 2      # Отступ от краев
    matrix_size = len(matrix)
    size = (matrix_size + border * 2) * scale

    # Создаем изображение
    img = Image.new("RGBA", (size, size), "white")
    draw = ImageDraw.Draw(img)

    # Цвета: графитовый основной и изумрудный акцент для глазков
    dot_color = (15, 23, 42, 255)
    finder_color = (16, 185, 129, 255)

    for r_idx, row in enumerate(matrix):
        for c_idx, val in enumerate(row):
            if val:
                x = (c_idx + border) * scale
                y = (r_idx + border) * scale

                # Проверяем, является ли точка частью трех угловых глазков
                is_finder = (
                        (r_idx < 8 and c_idx < 8) or
                        (r_idx < 8 and c_idx >= matrix_size - 8) or
                        (r_idx >= matrix_size - 8 and c_idx < 8)
                )

                margin = scale * 0.1  # Небольшой отступ

                if is_finder:
                    # Угловые маркеры оставляем в виде скругленных квадратов для контраста
                    draw.rounded_rectangle(
                        [x + margin, y + margin, x + scale - margin, y + scale - margin],
                        radius=scale * 0.3,
                        fill=finder_color
                    )
                else:
                    # Превращаем каждую точку в ромб (диамант)
                    cx = x + scale / 2
                    cy = y + scale / 2

                    points = [
                        (cx, y + margin),             # Верхняя вершина
                        (x + scale - margin, cy),     # Правая вершина
                        (cx, y + scale - margin),     # Нижняя вершина
                        (x + margin, cy)              # Левая вершина
                    ]
                    draw.polygon(points, fill=dot_color)

    img.save("test.png")

# generate_custom_qr("https://dylnx-indol.vercel.app")