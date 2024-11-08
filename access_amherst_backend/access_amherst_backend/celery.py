from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from django_celery_beat.models import PeriodicTask, IntervalSchedule, CrontabSchedule

# Set the default Django settings module for the Celery program.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "access_amherst_backend.settings")

app = Celery("access_amherst_backend")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

# Use the Celery Beat scheduler
app.conf.beat_scheduler = "django_celery_beat.schedulers.DatabaseScheduler"

@app.on_after_finalize.connect
def setup_periodic_tasks(sender, **kwargs):
    """
    Setup periodic tasks for Celery Beat.
    """
    from django_celery_beat.models import PeriodicTask

    # Clear existing tasks to avoid duplication
    PeriodicTask.objects.filter(name__in=[
        'Initiate Hub Workflow',
        'Initiate Daily Mammoth Workflow',
        'Remove Old Events'
    ]).delete()

    # Schedule every 6 hours
    interval_schedule, _ = IntervalSchedule.objects.get_or_create(
        every=6, period=IntervalSchedule.HOURS
    )
    PeriodicTask.objects.create(
        interval=interval_schedule,
        name='Initiate Hub Workflow',
        task='access_amherst_algo.tasks.initiate_hub_workflow',
    )

    # Schedule every 24 hours at 8:30 AM EST
    crontab_schedule_daily_mammoth, _ = CrontabSchedule.objects.get_or_create(
        minute='30',
        hour='13',  # 8:30 AM EST is 1:30 PM UTC
        day_of_week='*',
        day_of_month='*',
        month_of_year='*',
        timezone='America/New_York'
    )
    PeriodicTask.objects.create(
        crontab=crontab_schedule_daily_mammoth,
        name='Initiate Daily Mammoth Workflow',
        task='access_amherst_algo.tasks.initiate_daily_mammoth_workflow',
    )

    # Schedule every 24 hours at 10 PM EST
    crontab_schedule_remove_old, _ = CrontabSchedule.objects.get_or_create(
        minute='0',
        hour='3',  # 10 PM EST is 3:00 AM UTC
        day_of_week='*',
        day_of_month='*',
        month_of_year='*',
        timezone='America/New_York'
    )
    PeriodicTask.objects.create(
        crontab=crontab_schedule_remove_old,
        name='Remove Old Events',
        task='access_amherst_algo.tasks.remove_old_events',
    )