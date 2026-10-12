from django import forms

from .models import StudentWork, TeacherComment
from .validators import validate_work_file


class WorkUploadForm(forms.ModelForm):
    title = forms.CharField(
        label="Название работы",
        max_length=200,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "Курсовая работа по дисциплине..."}
        ),
    )
    description = forms.CharField(
        label="Описание",
        required=False,
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "rows": 4,
                "placeholder": "Кратко опишите содержание работы (необязательно)",
            }
        ),
    )
    file = forms.FileField(
        label="Файл работы",
        help_text="Допустимы PDF и DOCX, размер не более 10 МБ.",
        widget=forms.ClearableFileInput(attrs={"class": "form-control", "accept": ".pdf,.docx"}),
    )

    class Meta:
        model = StudentWork
        fields = ("title", "description", "file")

    def clean_file(self):
        uploaded = self.cleaned_data.get("file")
        return validate_work_file(uploaded)

    def clean_title(self):
        title = self.cleaned_data["title"].strip()
        if not title:
            raise forms.ValidationError("Укажите название работы.")
        return title


class WorkReviewForm(forms.Form):
    status = forms.ChoiceField(
        label="Результат проверки",
        choices=[
            choice
            for choice in StudentWork.Status.choices
            if choice[0] != StudentWork.Status.PENDING
        ],
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    comment = forms.CharField(
        label="Комментарий",
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "rows": 5,
                "placeholder": "Оставьте замечания или итоговый комментарий",
            }
        ),
    )

    def clean_status(self):
        status = self.cleaned_data["status"]
        allowed = {choice[0] for choice in StudentWork.Status.choices}
        if status not in allowed:
            raise forms.ValidationError("Выбран недопустимый статус проверки.")
        if status == StudentWork.Status.PENDING:
            raise forms.ValidationError("Выберите результат проверки, а не исходный статус «На проверке».")
        return status

    def clean_comment(self):
        text = self.cleaned_data["comment"].strip()
        if not text:
            raise forms.ValidationError("Комментарий не может быть пустым.")
        return text


class StatusFilterForm(forms.Form):
    status = forms.ChoiceField(
        required=False,
        choices=[("", "Все статусы")] + list(StudentWork.Status.choices),
        widget=forms.Select(attrs={"class": "form-select"}),
    )
