# Generated by Django 3.1.6 on 2021-03-03 11:43

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='segretario',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('idUser', models.EmailField(max_length=64)),
                ('surname', models.CharField(max_length=64)),
                ('forename', models.CharField(max_length=64)),
            ],
            options={
                'ordering': ['-idUser'],
            },
        ),
    ]
