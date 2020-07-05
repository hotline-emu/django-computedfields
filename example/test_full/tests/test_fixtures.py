from django.test import TestCase
from ..models import FixtureParent, FixtureChild
from django.core.management import call_command
from contextlib import contextmanager
from json import dumps, loads


def dumpdata_to_jsonstring(modelname):
    import sys
    from io import StringIO
    buf = StringIO()
    sysout = sys.stdout
    sys.stdout = buf
    call_command('dumpdata', modelname)
    sys.stdout = sysout
    return buf.getvalue()


# This test case must run before the second one.
class CreateDesyncFixtureData(TestCase):
    def test_parent_data(self):
        FixtureParent.objects.create(name='A')
        FixtureParent.objects.create(name='B')
        FixtureParent.objects.create(name='C')
        raw = dumpdata_to_jsonstring('test_full.FixtureParent')
        with open('fixtureparent.json', 'w') as f:
            f.write(raw)

    def test_child_data(self):
        pA = FixtureParent.objects.create(name='A')
        for i in range(10):
            FixtureChild.objects.create(name=str(i), parent=pA)
        raw = dumpdata_to_jsonstring('test_full.FixtureChild')

        # delete path to get desync computed value
        data = loads(raw)
        for el in data:
            el['fields']['path'] = ''
        
        with open('fixturechild.json', 'w') as f:
            f.write(dumps(data))


class TestUpdatedata(TestCase):
    fixtures = ["fixtureparent.json", "fixturechild.json"]

    def test_computedfields_desync(self):
        # all children_count are zero
        self.assertEqual(list(FixtureParent.objects.all().values_list('children_count', flat=True)), [0, 0, 0])
        # all path fields are empty
        self.assertEqual(any(FixtureChild.objects.all().values_list('path', flat=True)), False)

    def test_computedfields_resync(self):
        from time import time
        call_command('updatedata')  # expensive since resyncing all cfs in test models (~120ms)
        self.assertEqual(list(FixtureParent.objects.all().values_list('children_count', flat=True)), [10, 0, 0])
        self.assertEqual(
            list(FixtureChild.objects.all().values_list('path', flat=True)),
            ['/A#10/' + str(i) for i in range(10)]
        )
