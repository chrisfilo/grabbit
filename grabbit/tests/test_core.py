import pytest
from grabbit import File, Entity, Layout
import os
from pprint import pprint


@pytest.fixture
def file(tmpdir):
    testfile = 'sub-03_ses-2_task-rest_acq-fullbrain_run-2_bold.nii.gz'
    fn = tmpdir.mkdir("tmp").join(testfile)
    fn.write('###')
    return File(os.path.join(str(fn)))

@pytest.fixture(scope='module')
def layout():
    root = os.path.join(os.path.dirname(__file__), 'data', '7t_trt')
    config = os.path.join(os.path.dirname(__file__), 'specs', 'test.json')
    return Layout(root, config)


class TestFile:

    def test_init(self, tmpdir):
        fn = tmpdir.mkdir("tmp").join('tmp.txt')
        fn.write('###')
        f = File(str(fn))
        assert os.path.exists(f.path)
        assert f.filename is not None
        assert os.path.isdir(f.dirname)
        assert f.entities == {}

    def test_matches(self, file):
        assert file._matches()
        assert file._matches(extensions='nii.gz')
        assert not file._matches(extensions=['.txt', '.rtf'])
        file.entities = {'task': 'rest', 'run': '2' }
        assert file._matches(entities={'task': 'rest', 'run': 2})
        assert not file._matches(entities={'task': 'rest', 'run': 4})

    def test_named_tuple(self, file):
        file.entities = {'attrA': 'apple', 'attrB': 'banana' }
        tup = file.as_named_tuple()
        assert(tup.filename == file.path)
        assert isinstance(tup, tuple)
        assert not hasattr(tup, 'task')
        assert tup.attrA == 'apple'


class TestEntity:

    def test_init(self):
        e = Entity('avaricious', 'aardvark-(\d+)')
        assert e.name == 'avaricious'
        assert e.pattern == 'aardvark-(\d+)'
        assert not e.mandatory
        assert e.directory is None
        assert e.files == {}

    def test_matches(self, tmpdir):
        filename = "aardvark-4-reporting-for-duty.txt"
        tmpdir.mkdir("tmp").join(filename).write("###")
        f = File(os.path.join(str(tmpdir), filename))
        e = Entity('avaricious', 'aardvark-(\d+)')
        e.matches(f)
        assert 'avaricious' in f.entities
        assert f.entities['avaricious'] == '4'

    def test_unique_and_count(self):
        e = Entity('prop', '-(\d+)')
        e.files = {
            'test1-10.txt': '10',
            'test2-7.txt': '7',
            'test3-7.txt': '7'
        }
        assert sorted(e.unique()) == ['10', '7']
        assert e.count() == 2
        assert e.count(files=True) == 3

    def test_add_file(self):
        e = Entity('prop', '-(\d+)')
        e.add_file('a', '1')
        assert e.files['a'] == '1'


class TestLayout:

    def test_init(self, layout):
        assert os.path.exists(layout.root)
        assert isinstance(layout.files, dict)
        assert isinstance(layout.entities, dict)
        assert isinstance(layout.mandatory, set)
        assert not layout.dynamic_getters

    def test_dynamic_getters(self):
        data_dir = os.path.join(os.path.dirname(__file__), 'data', '7t_trt')
        config = os.path.join(os.path.dirname(__file__), 'specs', 'test.json')
        layout = Layout(data_dir, config, dynamic_getters=True)
        assert hasattr(layout, 'get_subjects')
        assert 'sub-01' in getattr(layout, 'get_subjects')()

    def test_querying(self, layout):
        # def get(self, return_type='tuple', target=None, extensions=None, **kwargs):
        result = layout.get(subject=1, run=1, session=1, extensions='nii.gz')
        assert len(result) == 8
        result = layout.get(subject='01', run=1, session=1, type='phasediff',
                            extensions='.json')
        assert len(result) == 1
        assert 'phasediff.json' in result[0].filename
        assert hasattr(result[0], 'run')
        assert result[0].run == 'run-1'
        result = layout.get(target='subject', return_type='id')
        assert len(result) == 10
        assert 'sub-03' in result
        result = layout.get(target='subject', return_type='dir')
        assert os.path.exists(result[0])
        assert os.path.isdir(result[0])

    def test_unique_and_count(self, layout):
        result = layout.unique('subject')
        assert len(result) == 10
        assert 'sub-03' in result
        assert layout.count('run') == 2
        assert layout.count('run', files=True) > 2
