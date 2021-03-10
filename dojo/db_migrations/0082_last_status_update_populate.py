# Generated by Django 2.2.17 on 2021-02-27 17:14
from django.db import migrations
from django.utils import timezone
import logging
logger = logging.getLogger(__name__)


def populate_last_status_update(apps, schema_editor):
    # We can't import the models directly as it may be a newer
    # version than this migration expects. We use the historical version.
    logger.info('Setting last_status_update timestamp on findings to be initially equal to last_reviewed timestamp (may take a while)')

    now = timezone.now()
    Finding = apps.get_model('dojo', 'Finding')
    findings = Finding.objects.order_by('id').only('id', 'is_Mitigated', 'mitigated', 'last_reviewed', 'last_status_update')

    page_size = 1000
    # use filter to make count fast on mysql
    total_count = Finding.objects.filter(id__gt=0).count()
    logger.debug('found %d findings to update:', total_count)

    # some dude in switzerland says he has 500k findings and the migration needed to be optimized to not take 1,5 hours to run
    # using paging (LIMIT/OFFSET) is very slow, the higher the page number, the longer the query takes
    # so we use a 'seek' method

    i = 0
    last_id = 0
    for p in range(1, (total_count // page_size) + 1):
        page = findings.filter(id__gt=last_id)[:page_size]
        batch = []
        for find in page:
            i += 1
            last_id = find.id

            if find.is_Mitigated:
                find.mitigated = find.mitigated or now

            # by default it is 'now' from the migration, but last_reviewed (or mitigated) is better default for existing findings
            if find.last_reviewed:
                find.last_status_update = find.last_reviewed
            elif find.mitigated:
                find.last_status_update = find.mitigated

            batch.append(find)

            if i > 0 and i % page_size == 0:
                Finding.objects.bulk_update(batch, ['last_status_update', 'mitigated'])
                batch = []
                logger.info('%s out of %s findings updated...', i, total_count)


class Migration(migrations.Migration):

    dependencies = [
        ('dojo', '0081_last_status_update'),
    ]

    operations = [
        migrations.RunPython(populate_last_status_update, migrations.RunPython.noop),
    ]