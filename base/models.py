from django.db import models
from django.contrib.auth.models import User
from django.dispatch import receiver
from django.db.models.signals import post_delete


# Create your models here.
class UserProfile(models.Model):
    name = models.CharField(max_length=200, null=True)
    avatar = models.ImageField(
        null=True, default="images/avatar.svg", upload_to='images/profile_images/')
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.name


@receiver(post_delete, sender=UserProfile)
def post_delete_user(sender, instance, *args, **kwargs):
    if instance.user:  # just in case user is not specified
        instance.user.delete()


class Friends(models.Model):
    owner = models.OneToOneField(User, on_delete=models.CASCADE)
    friends = models.ManyToManyField(
        'UserProfile', blank=True, related_name='userprofiles')

    def __str__(self):
        return self.owner.username


class Message(models.Model):
    body = models.TextField()
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='author')
    receiver = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='receiver')
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created']

    def __str__(self):
        return self.body[:10]


class FriendRequest(models.Model):
    sender = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='sender')
    target = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='target')

    def __str__(self):
        return str(self.sender.username + ' - ' + self.target.username)
