from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    pass

# Profile data model
class Profile(models.Model):
    follower = models.ForeignKey(User, on_delete=models.DO_NOTHING, null=True, related_name='following')
    following = models.ForeignKey(User, on_delete=models.DO_NOTHING, null=True, related_name='follower')

    def __str__(self):
        return f"{self.follower} follows {self.following}"

# Posts data model
class Post(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    post = models.TextField()

    date_added = models.DateTimeField(auto_now=True)
    liked_users = models.ManyToManyField(User, related_name='liked_posts')

    def __str__(self):
        return f"{self.user} {self.post} {self.date_added}"
