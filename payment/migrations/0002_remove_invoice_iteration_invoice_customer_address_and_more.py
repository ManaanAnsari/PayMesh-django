# Generated by Django 4.2.2 on 2023-06-25 16:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('payment', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='invoice',
            name='iteration',
        ),
        migrations.AddField(
            model_name='invoice',
            name='customer_address',
            field=models.CharField(default=None, max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name='invoice',
            name='closed_at',
            field=models.DateTimeField(default=None, null=True),
        ),
        migrations.AlterField(
            model_name='invoice',
            name='expired_at',
            field=models.DateTimeField(default=None, null=True),
        ),
        migrations.AlterField(
            model_name='supportednetwork',
            name='network_name',
            field=models.CharField(max_length=100),
        ),
    ]
