from django.contrib.postgres.fields import ArrayField, JSONField
from django.db import models


class TimeStampedModelMixin:
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class Replay(models.Model, TimeStampedModelMixin):
    url = models.CharField(max_length=256)
    log = models.TextField()
    data = JSONField(null=True)
    save_date = models.DateTimeField(null=True)


class Player(models.Model):
    name = models.CharField(max_length=256)
    player_num = models.IntegerField()
    replay = models.ForeignKey('replay_viewer.Replay', on_delete=models.CASCADE)
    identity = models.ForeignKey('replay_viewer.Identity', on_delete=models.CASCADE, null=True)


class Team(models.Model):
    data = ArrayField(base_field=models.CharField(max_length=256))
    player = models.ForeignKey('replay_viewer.Player', on_delete=models.CASCADE)
    replay = models.ForeignKey('replay_viewer.Replay', on_delete=models.CASCADE, null=True)


class Pokemon(models.Model):
    team = models.ForeignKey('replay_viewer.Team', on_delete=models.CASCADE)


class Identity(models.Model):
    username = models.CharField(max_length=96)

