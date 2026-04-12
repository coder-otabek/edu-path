"""accounts/views.py"""
import random
import string
import secrets
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail

from .models import CustomUser, AbituriyentProfile, PasswordResetOTP
from .forms import (
    RegisterForm, LoginForm, ForgotPasswordForm,
    OTPVerifyForm, ResetPasswordForm, ProfileEditForm
)
from core.models import SiteSettings


def _get_site():
    return SiteSettings.get()


# ---------- Register ----------
def register_view(request):
    site = _get_site()
    if not site.allow_register:
        messages.error(request, "Hozircha ro'yxatdan o'tish yopiq.")
        return redirect('accounts:login')

    form = RegisterForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        cd   = form.cleaned_data
        user = CustomUser.objects.create_user(
            email      = cd['email'],
            password   = cd['password1'],
            first_name = cd['first_name'],
            last_name  = cd['last_name'],
            gender     = cd['gender'],
            is_active  = False,   # email tasdiqlanmaguncha faol emas
        )
        AbituriyentProfile.objects.create(user=user)

        # Email tasdiqlash OTP yuborish
        _send_otp(user, site, purpose='verify')
        request.session['verify_email'] = cd['email']
        messages.info(request, f"Emailingizga tasdiqlash havolasi yuborildi.")
        return redirect('accounts:email_verify')

    return render(request, 'accounts/register.html', {'form': form, 'site': site})


# ---------- Email tasdiqlash (ro'yxatdan o'tish) ----------
def email_verify_view(request):
    """OTP kod kiritish sahifasi — ro'yxatdan o'tish uchun"""
    email = request.session.get('verify_email')
    if not email:
        return redirect('accounts:register')

    # Havola orqali kelganda — kodni URL dan olish
    code_from_url = request.GET.get('code', '')
    if code_from_url:
        return _verify_email_code(request, email, code_from_url, purpose='verify')

    form = OTPVerifyForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        return _verify_email_code(request, email, form.cleaned_data['code'], purpose='verify')

    # Qayta yuborish
    if request.method == 'POST' and request.GET.get('resend'):
        try:
            user = CustomUser.objects.get(email=email, is_active=False)
            site = _get_site()
            _send_otp(user, site, purpose='verify')
            messages.success(request, "Tasdiqlash kodi qayta yuborildi.")
        except CustomUser.DoesNotExist:
            pass

    return render(request, 'accounts/email_verify.html', {
        'form':         form,
        'masked_email': _mask_email(email),
    })


def _verify_email_code(request, email, code, purpose):
    """Email tasdiqlash kodini tekshirish"""
    try:
        user = CustomUser.objects.get(email=email)
        otp  = PasswordResetOTP.objects.filter(
            user=user, code=code, is_used=False, purpose=purpose
        ).latest('created_at')
        if otp.is_expired:
            messages.error(request, "Kod muddati o'tgan. Qayta so'rang.")
            if purpose == 'verify':
                return redirect('accounts:email_verify')
            return redirect('accounts:otp_verify')

        otp.is_used = True
        otp.save()

        if purpose == 'verify':
            user.is_active = True
            user.save(update_fields=['is_active'])
            del request.session['verify_email']
            login(request, user)
            messages.success(request, f"Xush kelibsiz, {user.first_name}!")
            return redirect('dashboard:home')
        else:
            request.session['reset_verified'] = True
            return redirect('accounts:reset_password')

    except PasswordResetOTP.DoesNotExist:
        messages.error(request, "Noto'g'ri yoki eskirgan kod.")
        if purpose == 'verify':
            return redirect('accounts:email_verify')
        return redirect('accounts:otp_verify')


# ---------- Login ----------
def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard:home')

    lang  = request.GET.get('lang', '')
    theme = request.GET.get('theme', '')

    form = LoginForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        cd   = form.cleaned_data
        user = authenticate(request, username=cd['email'], password=cd['password'])
        if user:
            if lang  and lang  in ['uz', 'ru', 'en']:  user.language = lang;  user.save(update_fields=['language'])
            if theme and theme in ['light', 'dark']:    user.theme    = theme; user.save(update_fields=['theme'])
            login(request, user)
            next_url = request.GET.get('next', 'dashboard:home')
            return redirect(next_url)
        else:
            # Email tasdiqlanmaganmi?
            try:
                unverified = CustomUser.objects.get(email=cd['email'], is_active=False)
                form.add_error(None, "Email tasdiqlanmagan. Emailingizni tekshiring.")
            except CustomUser.DoesNotExist:
                form.add_error(None, "Email yoki parol noto'g'ri.")

    return render(request, 'accounts/login.html', {
        'form':  form,
        'next':  request.GET.get('next', ''),
        'lang':  lang,
        'theme': theme,
    })


# ---------- Logout ----------
def logout_view(request):
    if request.method == 'POST':
        logout(request)
    return redirect('accounts:login')


# ---------- Forgot Password ----------
def forgot_password_view(request):
    site = _get_site()

    # Qayta yuborish
    if request.method == 'POST' and request.GET.get('resend'):
        email = request.POST.get('email', '')
        try:
            user = CustomUser.objects.get(email=email, is_active=True)
            _send_otp(user, site, purpose='reset')
            messages.success(request, "Kod qayta yuborildi.")
        except CustomUser.DoesNotExist:
            pass
        return redirect('accounts:otp_verify')

    form = ForgotPasswordForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        email = form.cleaned_data['email']
        user  = CustomUser.objects.get(email=email)
        _send_otp(user, site, purpose='reset')
        request.session['reset_email'] = email
        return redirect('accounts:otp_verify')

    return render(request, 'accounts/forgot_password.html', {'form': form})


def otp_verify_view(request):
    email = request.session.get('reset_email')
    if not email:
        return redirect('accounts:forgot_password')

    # Havola orqali kelganda
    code_from_url = request.GET.get('code', '')
    if code_from_url:
        return _verify_email_code(request, email, code_from_url, purpose='reset')

    form = OTPVerifyForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        return _verify_email_code(request, email, form.cleaned_data['code'], purpose='reset')

    return render(request, 'accounts/otp_verify.html', {
        'form':         form,
        'masked_email': _mask_email(email),
    })


def reset_password_view(request):
    if not request.session.get('reset_verified'):
        return redirect('accounts:forgot_password')

    email = request.session.get('reset_email')
    form  = ResetPasswordForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        try:
            user = CustomUser.objects.get(email=email)
            user.set_password(form.cleaned_data['password1'])
            user.save()
            del request.session['reset_email']
            del request.session['reset_verified']
            messages.success(request, "Parol muvaffaqiyatli o'zgartirildi. Kiring.")
            return redirect('accounts:login')
        except CustomUser.DoesNotExist:
            return redirect('accounts:forgot_password')

    return render(request, 'accounts/reset_password.html', {'form': form})


# ---------- Profile ----------
@login_required
def profile_view(request):
    profile, _ = AbituriyentProfile.objects.get_or_create(user=request.user)
    return render(request, 'accounts/profile.html', {'profile': profile})


@login_required
def profile_edit_view(request):
    profile, _ = AbituriyentProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        first_name = request.POST.get('first_name', '').strip()
        last_name  = request.POST.get('last_name', '').strip()
        if first_name:
            request.user.first_name = first_name
        if last_name:
            request.user.last_name = last_name
        request.user.save()

        def get_int(key):
            val = request.POST.get(key, '').strip()
            return int(val) if val else None

        def get_float(key):
            val = request.POST.get(key, '').strip()
            return float(val) if val else None

        profile.dtm_score            = get_int('dtm_score')
        profile.ielts_score          = get_float('ielts_score')
        profile.sat_score            = get_int('sat_score')
        profile.gpa                  = get_float('gpa')
        profile.olympiad_level       = request.POST.get('olympiad_level', '')
        profile.main_subject         = request.POST.get('main_subject', '')
        profile.second_subject       = request.POST.get('second_subject', '')
        profile.desired_degree       = request.POST.get('desired_degree', 'bachelor')
        profile.desired_specialty    = request.POST.get('desired_specialty', '')
        profile.study_type           = request.POST.get('study_type', 'both')
        profile.native_language      = request.POST.get('native_language', 'uz')
        profile.needs_grant          = 'needs_grant' in request.POST
        profile.can_self_finance     = 'can_self_finance' in request.POST
        profile.monthly_budget       = get_int('monthly_budget')
        profile.volunteer_hours      = get_int('volunteer_hours') or 0
        profile.has_work_experience  = 'has_work_experience' in request.POST
        profile.work_experience_desc = request.POST.get('work_experience_desc', '')
        profile.achievements         = request.POST.get('achievements', '')
        profile.bio                  = request.POST.get('bio', '')

        if 'avatar' in request.FILES:
            profile.avatar = request.FILES['avatar']

        profile.save()
        messages.success(request, "Profil muvaffaqiyatli yangilandi!")
        return redirect('accounts:profile')

    return render(request, 'accounts/profile_edit.html', {
        'profile': profile,
        'user':    request.user,
    })


@login_required
def settings_view(request):
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'theme':
            theme = request.POST.get('theme', 'light')
            request.user.theme = theme
            request.user.save(update_fields=['theme'])
            return JsonResponse({'ok': True, 'theme': theme})
        elif action == 'language':
            lang = request.POST.get('language', 'uz')
            request.user.language = lang
            request.user.save(update_fields=['language'])
            return JsonResponse({'ok': True, 'language': lang})
    return render(request, 'accounts/settings.html')


@login_required
def onboarding_view(request):
    if request.user.onboarded:
        return redirect('dashboard:home')
    if request.method == 'POST':
        lang  = request.POST.get('language', 'uz')
        theme = request.POST.get('theme', 'light')
        request.user.language  = lang
        request.user.theme     = theme
        request.user.onboarded = True
        request.user.save(update_fields=['language', 'theme', 'onboarded'])
        return redirect('dashboard:home')
    return render(request, 'accounts/onboarding.html')


# ---------- Helpers ----------
def _generate_otp(length=6):
    return ''.join(random.choices(string.digits, k=length))


def _send_otp(user, site, purpose='reset'):
    """
    OTP yuborish — kod ham, havola ham boradi.
    purpose: 'reset' (parol tiklash) | 'verify' (email tasdiqlash)
    """
    code = _generate_otp()
    PasswordResetOTP.objects.create(user=user, code=code, purpose=purpose)

    from django.conf import settings as django_settings
    base_url = getattr(django_settings, 'SITE_URL', 'http://localhost:8000')
    lang = getattr(user, 'language', 'uz') or 'uz'
    name = user.first_name or user.email.split('@')[0]
    site_name = site.name if hasattr(site, 'name') else 'EduPath'

    if purpose == 'verify':
        link = f"{base_url}/accounts/email-verify/?code={code}"
        subjects = {
            'uz': f"[{site_name}] Emailingizni tasdiqlang",
            'ru': f"[{site_name}] Подтвердите ваш email",
            'en': f"[{site_name}] Confirm your email",
        }
        bodies = {
            'uz': (
                f"Salom {name},\n\n"
                f"EduPath ga xush kelibsiz!\n\n"
                f"Emailingizni tasdiqlash uchun quyidagi havolani bosing:\n"
                f"👉 {link}\n\n"
                f"Yoki ushbu 6 raqamli kodni kiriting: {code}\n\n"
                f"⏰ Havola 15 daqiqa davomida amal qiladi.\n\n"
                f"Agar siz ro'yxatdan o'tmagan bo'lsangiz, bu xabarni e'tiborsiz qoldiring.\n\n"
                f"Hurmat bilan,\n{site_name} jamoasi"
            ),
            'ru': (
                f"Здравствуйте, {name}!\n\n"
                f"Добро пожаловать в EduPath!\n\n"
                f"Для подтверждения email нажмите на ссылку ниже:\n"
                f"👉 {link}\n\n"
                f"Или введите этот 6-значный код: {code}\n\n"
                f"⏰ Ссылка действительна 15 минут.\n\n"
                f"Если вы не регистрировались, просто проигнорируйте это письмо.\n\n"
                f"С уважением,\nКоманда {site_name}"
            ),
            'en': (
                f"Hello {name},\n\n"
                f"Welcome to EduPath!\n\n"
                f"Please confirm your email by clicking the link below:\n"
                f"👉 {link}\n\n"
                f"Or enter this 6-digit code: {code}\n\n"
                f"⏰ The link is valid for 15 minutes.\n\n"
                f"If you did not register, please ignore this email.\n\n"
                f"Best regards,\n{site_name} Team"
            ),
        }
    else:
        link = f"{base_url}/accounts/otp-verify/?code={code}"
        subjects = {
            'uz': f"[{site_name}] Parolni tiklash",
            'ru': f"[{site_name}] Восстановление пароля",
            'en': f"[{site_name}] Password Reset",
        }
        bodies = {
            'uz': (
                f"Salom {name},\n\n"
                f"Parolingizni tiklash uchun quyidagi havolani bosing:\n"
                f"👉 {link}\n\n"
                f"Yoki ushbu 6 raqamli kodni kiriting: {code}\n\n"
                f"⏰ Havola 15 daqiqa davomida amal qiladi.\n\n"
                f"Agar siz so'ramagan bo'lsangiz, bu xabarni e'tiborsiz qoldiring.\n\n"
                f"Hurmat bilan,\n{site_name} jamoasi"
            ),
            'ru': (
                f"Здравствуйте, {name}!\n\n"
                f"Для сброса пароля нажмите на ссылку ниже:\n"
                f"👉 {link}\n\n"
                f"Или введите этот 6-значный код: {code}\n\n"
                f"⏰ Ссылка действительна 15 минут.\n\n"
                f"Если вы не запрашивали сброс пароля, просто проигнорируйте это письмо.\n\n"
                f"С уважением,\nКоманда {site_name}"
            ),
            'en': (
                f"Hello {name},\n\n"
                f"To reset your password, click the link below:\n"
                f"👉 {link}\n\n"
                f"Or enter this 6-digit code: {code}\n\n"
                f"⏰ The link is valid for 15 minutes.\n\n"
                f"If you did not request a password reset, please ignore this email.\n\n"
                f"Best regards,\n{site_name} Team"
            ),
        }

    subject = subjects.get(lang, subjects['uz'])
    body    = bodies.get(lang, bodies['uz'])

    from django.conf import settings as _s
    from_email = getattr(_s, 'DEFAULT_FROM_EMAIL', 'noreply@edupath.uz')
    try:
        send_mail(subject, body, from_email, [user.email], fail_silently=False)
    except Exception:
        pass


def _mask_email(email):
    if not email or '@' not in email:
        return email
    local, domain = email.split('@', 1)
    if len(local) <= 2:
        return f"{'*' * len(local)}@{domain}"
    return f"{local[0]}{'*' * (len(local) - 2)}{local[-1]}@{domain}"