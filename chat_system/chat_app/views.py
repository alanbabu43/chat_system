from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Q
from .models import User, Message


def register_view(request):
    if request.user.is_authenticated:
        return redirect('user_list')
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password1 = request.POST.get('password1', '')
        password2 = request.POST.get('password2', '')

        errors = []
        if not username:
            errors.append('Username is required.')
        elif User.objects.filter(username=username).exists():
            errors.append('Username already taken.')
        if not email:
            errors.append('Email is required.')
        elif User.objects.filter(email=email).exists():
            errors.append('Email already registered.')
        if len(password1) < 6:
            errors.append('Password must be at least 6 characters.')
        if password1 != password2:
            errors.append('Passwords do not match.')

        if errors:
            for error in errors:
                messages.error(request, error)
            return render(request, 'chat_app/register.html', {'username': username, 'email': email})

        user = User.objects.create_user(username=username, email=email, password=password1)
        auth_login(request, user)
        User.objects.filter(pk=user.pk).update(is_online=True, last_seen=None)
        return redirect('user_list')

    return render(request, 'chat_app/register.html')


def login_view(request):
    if request.user.is_authenticated:
        return redirect('user_list')
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)
        if user:
            auth_login(request, user)
            User.objects.filter(pk=user.pk).update(is_online=True, last_seen=None)
            return redirect('user_list')
        else:
            messages.error(request, 'Invalid username or password.')
    return render(request, 'chat_app/login.html')


@login_required
def logout_view(request):
    User.objects.filter(pk=request.user.pk).update(is_online=False, last_seen=timezone.now())
    auth_logout(request)
    return redirect('login')


@login_required
def user_list(request):
    from django.db.models import Count, Q
    users = User.objects.exclude(pk=request.user.pk).annotate(
        unread_count=Count(
            'sent_messages',
            filter=Q(sent_messages__receiver=request.user, sent_messages__is_read=False)
        )
    ).order_by('username')
    return render(request, 'chat_app/user_list.html', {'users': users})



@login_required
def chat_view(request, user_id):
    other_user = get_object_or_404(User, pk=user_id)
    if other_user == request.user:
        return redirect('user_list')

    # Load message history
    chat_messages = Message.objects.filter(
        Q(sender=request.user, receiver=other_user) |
        Q(sender=other_user, receiver=request.user)
    ).order_by('timestamp')

    # Mark received messages as read
    unread_ids = list(
        chat_messages.filter(receiver=request.user, is_read=False).values_list('id', flat=True)
    )
    if unread_ids:
        Message.objects.filter(id__in=unread_ids).update(is_read=True)

    return render(request, 'chat_app/chat.html', {
        'other_user': other_user,
        'messages': chat_messages,
        'unread_ids': unread_ids,
    })
