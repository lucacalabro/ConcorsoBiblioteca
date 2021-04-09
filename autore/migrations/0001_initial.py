# Generated by Django 3.1.6 on 2021-03-03 11:43

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('gestore', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='racconti',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('counter', models.IntegerField()),
                ('idUser', models.EmailField(max_length=64)),
                ('title', models.CharField(max_length=128)),
                ('content', models.TextField(max_length=8000)),
                ('submissionDate', models.DateTimeField()),
                ('publishingPermission', models.BooleanField(default=True)),
                ('contacts', models.CharField(max_length=128)),
                ('coAuthors', models.TextField(max_length=8000, null=True)),
                ('authorSurname', models.CharField(max_length=64)),
                ('authorForename', models.CharField(max_length=64)),
                ('authorBirthDate', models.DateTimeField()),
                ('authorStatus', models.CharField(max_length=64)),
                ('authorDetail', models.CharField(max_length=64)),
                ('idEvent', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='gestore.events')),
            ],
        ),
    ]