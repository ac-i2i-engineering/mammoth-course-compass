from django.db import models


class Event(models.Model):
    id = models.IntegerField(
        primary_key=True, unique=True, null=False, blank=False
    )
    title = models.CharField(max_length=255)
    author_name = models.CharField(max_length=255, null=True, blank=True)
    author_email = models.CharField(max_length=255, null=True, blank=True)
    pub_date = models.DateTimeField(null=True, blank=True)
    host = models.TextField(
        null=True, blank=True
    )  # This can store a list of hosts as a comma-separated string or JSON
    link = models.URLField(max_length=500, null=True, blank=True)
    picture_link = models.URLField(max_length=500, null=True, blank=True)
    event_description = models.TextField(null=True, blank=True)
    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)
    location = models.CharField(max_length=500, null=True, blank=True)
    categories = (
        models.TextField()
    )  # This can store a list of categories as a comma-separated string or JSON
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    map_location = models.CharField(max_length=500, null=True)

    def __str__(self):
        return self.title
