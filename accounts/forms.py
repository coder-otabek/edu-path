"""accounts/forms.py"""
from django import forms
from django.contrib.auth.password_validation import validate_password
from .models import CustomUser, AbituriyentProfile


class RegisterForm(forms.Form):
    first_name = forms.CharField(max_length=100)
    last_name  = forms.CharField(max_length=100)
    email      = forms.EmailField()
    password1  = forms.CharField(widget=forms.PasswordInput)
    password2  = forms.CharField(widget=forms.PasswordInput)
    gender     = forms.ChoiceField(choices=[('male','Erkak'),('female','Ayol')], required=True)

    def clean_email(self):
        email = self.cleaned_data['email'].lower()
        if CustomUser.objects.filter(email=email).exists():
            raise forms.ValidationError("Bu email allaqachon ro'yxatdan o'tgan.")
        return email

    def clean(self):
        cd = super().clean()
        p1, p2 = cd.get('password1'), cd.get('password2')
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError("Parollar mos kelmadi.")
        if p1:
            validate_password(p1)
        return cd


class LoginForm(forms.Form):
    email    = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)


class ForgotPasswordForm(forms.Form):
    email = forms.EmailField()

    def clean_email(self):
        email = self.cleaned_data['email'].lower()
        if not CustomUser.objects.filter(email=email, is_active=True).exists():
            raise forms.ValidationError("Bu email bilan hisob topilmadi.")
        return email


class OTPVerifyForm(forms.Form):
    code = forms.CharField(max_length=6, min_length=6)


class ResetPasswordForm(forms.Form):
    password1 = forms.CharField(widget=forms.PasswordInput)
    password2 = forms.CharField(widget=forms.PasswordInput)

    def clean(self):
        cd = super().clean()
        p1, p2 = cd.get('password1'), cd.get('password2')
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError("Parollar mos kelmadi.")
        if p1:
            validate_password(p1)
        return cd


class ProfileEditForm(forms.ModelForm):
    first_name = forms.CharField(max_length=100, required=False)
    last_name  = forms.CharField(max_length=100, required=False)

    class Meta:
        model  = AbituriyentProfile
        fields = [
            'avatar', 'ielts_score', 'sat_score', 'gpa',
            'olympiad_level', 'main_subject', 'second_subject',
            'desired_degree', 'desired_specialty', 'study_type',
            'native_language', 'can_self_finance', 'needs_grant',
            'monthly_budget', 'volunteer_hours', 'has_work_experience',
            'work_experience_desc', 'achievements', 'bio',
        ]
        widgets = {
            'work_experience_desc': forms.Textarea(attrs={'rows': 3}),
            'achievements':         forms.Textarea(attrs={'rows': 3}),
            'bio':                  forms.Textarea(attrs={'rows': 3}),
        }