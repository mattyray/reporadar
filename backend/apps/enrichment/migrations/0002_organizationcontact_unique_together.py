from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('enrichment', '0001_initial'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='organizationcontact',
            unique_together={('organization', 'email')},
        ),
    ]
