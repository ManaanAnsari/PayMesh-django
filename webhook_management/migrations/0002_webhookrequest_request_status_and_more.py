# Generated by Django 4.2.2 on 2023-07-06 21:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('webhook_management', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='webhookrequest',
            name='request_status',
            field=models.CharField(choices=[('POST', 'POST')], default='CREATED', max_length=30),
        ),
        migrations.AlterField(
            model_name='webhookrequest',
            name='request_data',
            field=models.JSONField(default={}),
        ),
        migrations.AlterField(
            model_name='webhookrequest',
            name='request_sent_at',
            field=models.DateTimeField(blank=True, default=None, null=True),
        ),
        migrations.AlterField(
            model_name='webhookrequest',
            name='request_type',
            field=models.CharField(choices=[('POST', 'POST')], default='POST', max_length=30),
        ),
        migrations.AlterField(
            model_name='webhookrequest',
            name='response_status_code',
            field=models.IntegerField(blank=True, default=None, null=True),
        ),
    ]
