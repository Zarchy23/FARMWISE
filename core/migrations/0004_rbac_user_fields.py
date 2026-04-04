# Generated migration for RBAC User model changes

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_alter_user_phone_number'),  # Update this to your latest migration
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='assigned_farms',
            field=models.ManyToManyField(
                to='core.farm',
                related_name='assigned_to_users',
                blank=True,
                help_text='For agronomists/veterinarians: farms they are assigned to'
            ),
        ),
        migrations.AddField(
            model_name='user',
            name='cooperative_member',
            field=models.ForeignKey(
                null=True,
                blank=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='members',
                to='core.cooperative',
                help_text='For farmers: the cooperative they belong to'
            ),
        ),
        migrations.AddField(
            model_name='user',
            name='permissions',
            field=models.JSONField(
                default=dict,
                blank=True,
                help_text='Custom permission overrides (JSON format)'
            ),
        ),
        migrations.AddField(
            model_name='user',
            name='is_active_member',
            field=models.BooleanField(
                default=True,
                help_text='For cooperative members: whether they are active in the cooperative'
            ),
        ),
        migrations.AddIndex(
            model_name='user',
            index=models.Index(fields=['cooperative_member'], name='users_cooperative_idx'),
        ),
    ]
