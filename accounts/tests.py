from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

User = get_user_model()


class AccountsTests(TestCase):
    def test_register_creates_student(self):
        response = self.client.post(
            reverse("accounts:register"),
            {
                "username": "student1",
                "first_name": "Анна",
                "email": "anna@university.ru",
                "password1": "StrongPass123",
                "password2": "StrongPass123",
            },
        )
        self.assertEqual(response.status_code, 302)
        user = User.objects.get(username="student1")
        self.assertEqual(user.role, User.Role.STUDENT)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_cannot_self_assign_teacher_or_admin_role(self):
        response = self.client.post(
            reverse("accounts:register"),
            {
                "username": "hacker",
                "first_name": "Хакер",
                "email": "hacker@university.ru",
                "password1": "StrongPass123",
                "password2": "StrongPass123",
                "role": User.Role.TEACHER,
                "is_staff": "on",
                "is_superuser": "on",
            },
        )
        self.assertEqual(response.status_code, 302)
        user = User.objects.get(username="hacker")
        self.assertEqual(user.role, User.Role.STUDENT)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_login_and_logout(self):
        User.objects.create_user(
            username="student2",
            email="student2@university.ru",
            password="StrongPass123",
            first_name="Иван",
            role=User.Role.STUDENT,
        )
        login_response = self.client.post(
            reverse("accounts:login"),
            {"username": "student2", "password": "StrongPass123"},
        )
        self.assertEqual(login_response.status_code, 302)
        self.assertRedirects(login_response, reverse("works:dashboard"), fetch_redirect_response=False)

        dashboard = self.client.get(reverse("works:dashboard"))
        self.assertEqual(dashboard.status_code, 200)

        logout_response = self.client.post(reverse("accounts:logout"))
        self.assertEqual(logout_response.status_code, 302)
        home = self.client.get(reverse("home"))
        self.assertNotContains(home, "Кабинет")

    def test_anonymous_user_cannot_open_dashboard(self):
        response = self.client.get(reverse("works:dashboard"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("accounts:login"), response.url)
