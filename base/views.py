from django.shortcuts import redirect
from django.views.generic import TemplateView, View
from django.contrib.auth.views import LoginView
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import login, logout
from django.contrib import messages

from django.contrib.auth.models import User
from .models import UserProfile, Friends, FriendRequest
from .forms import ProfileUpdateForm


class LoginView(LoginView):
    template_name = 'base/login.html'
    redirect_authenticated_user = True


class LogoutView(View):
    def get(self, request, *args, **kwargs):
        logout(request)
        return redirect('login')


class RegisterView(TemplateView):
    template_name = 'base/register.html'

    def get(self, *args, **kwargs):
        if self.request.user.is_authenticated:
            return redirect('home')
        return super(RegisterView, self).get(*args, **kwargs)

    def post(self, request, *args, **kwargs):
        form = UserCreationForm(request.POST)

        if form.is_valid():
            user = form.save()
            if user is not None:
                UserProfile.objects.create(name=user.username, user=user)
                Friends.objects.create(owner=user)

                login(self.request, user)
                return redirect('home')

        if request.POST.get('password1', '') == '':
            messages.error(request, 'Hasło nie może być puste!')
        elif request.POST.get('password2', '') == '':
            messages.error(request, 'Powtórzenie hasła nie może być puste!')
        elif request.POST.get('password1', '') != request.POST.get('password2', ''):
            messages.error(request, 'Hasła muszą być identyczne!')
        elif User.objects.filter(username=request.POST.get('username', '')):
            messages.error(request, 'Użytkownik o podanej nazwie już istnieje!')
        else:
            messages.error(request, 'Podczas rejestracji wystąpił błąd!')

        return redirect('register')


class HomeView(LoginRequiredMixin, TemplateView):
    template_name = 'base/home.html'
    login_url = 'login'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['friends'] = Friends.objects.get(owner=self.request.user).friends.all()
        context['friend_request_send'] = FriendRequest.objects.filter(sender=self.request.user)
        context['friend_request_received'] = FriendRequest.objects.filter(target=self.request.user)

        return context
        
    def post(self, request, *args, **kwargs):
        user_profile = UserProfile.objects.get(user=request.user)

        form = ProfileUpdateForm(request.POST, request.FILES, instance=user_profile)
        if form.is_valid():
            form.save()

        return redirect('home')
