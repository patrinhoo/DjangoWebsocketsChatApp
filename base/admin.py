from django.contrib import admin
from .models import UserProfile, Friends, Message, FriendRequest

# Register your models here.
admin.site.register(UserProfile)
admin.site.register(Friends)
admin.site.register(Message)
admin.site.register(FriendRequest)
