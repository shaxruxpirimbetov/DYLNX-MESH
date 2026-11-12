import io
import boto3
import qrcode
from botocore.config import Config
from decouple import config

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

    qr.add_data(f"{BACKEND_HERE}/mesh/{uuid}")
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