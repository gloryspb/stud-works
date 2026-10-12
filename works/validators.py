import os
import zipfile
from io import BytesIO

from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.text import get_valid_filename


def sanitize_filename(filename: str) -> str:
    if not filename:
        raise ValidationError("Не указано имя файла.")
    normalized = filename.replace("\\", "/")
    basename = os.path.basename(normalized)
    if not basename or basename in {".", ".."}:
        raise ValidationError("Недопустимое имя файла.")
    if "/" in basename or "\\" in basename:
        raise ValidationError("Имя файла не должно содержать путь.")
    safe_name = get_valid_filename(basename)
    if not safe_name:
        raise ValidationError("Недопустимое имя файла.")
    return safe_name


def _read_prefix(uploaded_file, size: int) -> bytes:
    uploaded_file.seek(0)
    data = uploaded_file.read(size)
    uploaded_file.seek(0)
    return data


def _validate_pdf(uploaded_file):
    header = _read_prefix(uploaded_file, 8)
    if not header.startswith(b"%PDF"):
        raise ValidationError("Файл с расширением PDF не является корректным PDF-документом.")


def _validate_docx(uploaded_file):
    header = _read_prefix(uploaded_file, 4)
    if not header.startswith(b"PK"):
        raise ValidationError("Файл с расширением DOCX не является документом Word.")
    try:
        uploaded_file.seek(0)
        content = uploaded_file.read()
        uploaded_file.seek(0)
        with zipfile.ZipFile(BytesIO(content)) as archive:
            names = archive.namelist()
    except zipfile.BadZipFile as exc:
        raise ValidationError("Файл DOCX повреждён или имеет неверный формат.") from exc
    if "[Content_Types].xml" not in names:
        raise ValidationError("Файл не соответствует формату DOCX.")
    if not any(name.startswith("word/") for name in names):
        raise ValidationError("Файл не содержит структуру документа Word.")


def validate_work_file(uploaded_file):
    if uploaded_file is None:
        raise ValidationError("Необходимо выбрать файл работы.")

    filename = sanitize_filename(getattr(uploaded_file, "name", ""))
    extension = os.path.splitext(filename)[1].lower()
    allowed = tuple(ext.lower() for ext in settings.ALLOWED_WORK_EXTENSIONS)
    if extension not in allowed:
        raise ValidationError("Разрешены только файлы PDF и DOCX.")

    size = getattr(uploaded_file, "size", None)
    if size is None:
        raise ValidationError("Не удалось определить размер файла.")
    if size <= 0:
        raise ValidationError("Файл пустой.")
    if size > settings.MAX_UPLOAD_SIZE:
        max_mb = settings.MAX_UPLOAD_SIZE // (1024 * 1024)
        raise ValidationError(f"Размер файла не должен превышать {max_mb} МБ.")

    content_type = getattr(uploaded_file, "content_type", "") or ""
    if content_type and content_type not in settings.ALLOWED_WORK_CONTENT_TYPES:
        raise ValidationError("Недопустимый тип содержимого файла.")

    if extension == ".pdf":
        _validate_pdf(uploaded_file)
    elif extension == ".docx":
        _validate_docx(uploaded_file)

    uploaded_file.name = filename
    return uploaded_file
