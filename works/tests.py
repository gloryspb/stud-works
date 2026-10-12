import io
import tempfile
import zipfile

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import StudentWork, TeacherComment

User = get_user_model()


def make_pdf(name="work.pdf"):
    return SimpleUploadedFile(
        name,
        b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF",
        content_type="application/pdf",
    )


def make_docx(name="work.docx"):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("[Content_Types].xml", "<Types></Types>")
        archive.writestr("word/document.xml", "<w:document></w:document>")
    return SimpleUploadedFile(
        name,
        buffer.getvalue(),
        content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )


class WorkFlowTests(TestCase):
    def setUp(self):
        self.media_dir = tempfile.TemporaryDirectory()
        self.media_override = override_settings(MEDIA_ROOT=self.media_dir.name)
        self.media_override.enable()
        self.addCleanup(self.media_override.disable)
        self.addCleanup(self.media_dir.cleanup)
        self.student = User.objects.create_user(
            username="student",
            email="student@university.ru",
            password="StrongPass123",
            first_name="Студент",
            role=User.Role.STUDENT,
        )
        self.other_student = User.objects.create_user(
            username="other",
            email="other@university.ru",
            password="StrongPass123",
            first_name="Другой",
            role=User.Role.STUDENT,
        )
        self.teacher = User.objects.create_user(
            username="teacher",
            email="teacher@university.ru",
            password="StrongPass123",
            first_name="Преподаватель",
            role=User.Role.TEACHER,
        )

    def test_upload_pdf_creates_pending_work(self):
        self.client.login(username="student", password="StrongPass123")
        response = self.client.post(
            reverse("works:upload"),
            {
                "title": "Лабораторная работа 1",
                "description": "Описание",
                "file": make_pdf(),
            },
        )
        self.assertEqual(response.status_code, 302)
        work = StudentWork.objects.get(title="Лабораторная работа 1")
        self.assertEqual(work.student, self.student)
        self.assertEqual(work.status, StudentWork.Status.PENDING)

    def test_upload_docx_is_allowed(self):
        self.client.login(username="student", password="StrongPass123")
        response = self.client.post(
            reverse("works:upload"),
            {"title": "Реферат", "file": make_docx()},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(StudentWork.objects.filter(title="Реферат").count(), 1)

    def test_reject_unsupported_file_type(self):
        self.client.login(username="student", password="StrongPass123")
        bad_file = SimpleUploadedFile("notes.txt", b"hello", content_type="text/plain")
        response = self.client.post(
            reverse("works:upload"),
            {"title": "Неверный файл", "file": bad_file},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Разрешены только файлы PDF и DOCX")
        self.assertFalse(StudentWork.objects.filter(title="Неверный файл").exists())

    @override_settings(MAX_UPLOAD_SIZE=50)
    def test_reject_oversized_file(self):
        self.client.login(username="student", password="StrongPass123")
        big_pdf = SimpleUploadedFile(
            "big.pdf",
            b"%PDF-1.4\n" + b"a" * 100,
            content_type="application/pdf",
        )
        response = self.client.post(
            reverse("works:upload"),
            {"title": "Большой файл", "file": big_pdf},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Размер файла не должен превышать")
        self.assertFalse(StudentWork.objects.filter(title="Большой файл").exists())

    def test_student_sees_only_own_works(self):
        own = StudentWork.objects.create(
            title="Моя работа",
            student=self.student,
            file=make_pdf("own.pdf"),
        )
        foreign = StudentWork.objects.create(
            title="Чужая работа",
            student=self.other_student,
            file=make_pdf("foreign.pdf"),
        )
        self.client.login(username="student", password="StrongPass123")
        response = self.client.get(reverse("works:dashboard"))
        self.assertContains(response, own.title)
        self.assertNotContains(response, foreign.title)

        forbidden = self.client.get(reverse("works:detail", args=[foreign.pk]))
        self.assertEqual(forbidden.status_code, 403)

    def test_cannot_download_someone_elses_file(self):
        work = StudentWork.objects.create(
            title="Чужая",
            student=self.other_student,
            file=make_pdf("secret.pdf"),
        )
        self.client.login(username="student", password="StrongPass123")
        response = self.client.get(reverse("works:download", args=[work.pk]))
        self.assertEqual(response.status_code, 403)

    def test_student_cannot_change_review_status(self):
        work = StudentWork.objects.create(
            title="На проверке",
            student=self.student,
            file=make_pdf("check.pdf"),
        )
        self.client.login(username="student", password="StrongPass123")
        response = self.client.post(
            reverse("works:review", args=[work.pk]),
            {"status": StudentWork.Status.REVIEWED, "comment": "Сам себе поставил оценку"},
        )
        self.assertEqual(response.status_code, 403)
        work.refresh_from_db()
        self.assertEqual(work.status, StudentWork.Status.PENDING)
        self.assertEqual(TeacherComment.objects.count(), 0)

    def test_teacher_can_change_status_and_comment(self):
        work = StudentWork.objects.create(
            title="Курсовая",
            student=self.student,
            file=make_pdf("course.pdf"),
        )
        self.client.login(username="teacher", password="StrongPass123")
        response = self.client.post(
            reverse("works:review", args=[work.pk]),
            {
                "status": StudentWork.Status.NEEDS_FIXES,
                "comment": "Исправьте введение и список литературы.",
            },
        )
        self.assertEqual(response.status_code, 302)
        work.refresh_from_db()
        self.assertEqual(work.status, StudentWork.Status.NEEDS_FIXES)
        comment = TeacherComment.objects.get(work=work)
        self.assertEqual(comment.teacher, self.teacher)
        self.assertIn("Исправьте введение", comment.text)

    def test_missing_work_returns_404(self):
        self.client.login(username="teacher", password="StrongPass123")
        response = self.client.get(reverse("works:detail", args=[99999]))
        self.assertEqual(response.status_code, 404)
        download = self.client.get(reverse("works:download", args=[99999]))
        self.assertEqual(download.status_code, 404)

    def test_anonymous_cannot_open_protected_pages(self):
        work = StudentWork.objects.create(
            title="Закрытая",
            student=self.student,
            file=make_pdf("closed.pdf"),
        )
        pages = [
            reverse("works:upload"),
            reverse("works:detail", args=[work.pk]),
            reverse("works:teacher_works"),
            reverse("works:review", args=[work.pk]),
        ]
        for url in pages:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 302)
            self.assertIn(reverse("accounts:login"), response.url)
