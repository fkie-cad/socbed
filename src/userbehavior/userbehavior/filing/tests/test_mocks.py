#!/usr/bin/python3
# -*- coding: utf-8 -*-

import pytest

from userbehavior.filing.filer import FilerException
from userbehavior.filing.tests.mocks import MockFiler, MockFilingProfile


@pytest.fixture()
def mf(request):
    return MockFiler()


class TestMockFiler:
    def test_get_files(self, mf):
        assert isinstance(mf.get_files(), list)

    def test_create_two_files(self, mf):
        mf.create("TF1")
        mf.create("TF2")
        files = mf.get_files()
        assert "TF1" in files
        assert "TF2" in files

    def test_read_empty_file(self, mf):
        mf.create("TestFile")
        text = mf.read("TestFile")
        assert text == ""

    def test_append(self, mf):
        mf.create("TestFile")
        mf.append("TestFile", "TestText")
        text = mf.read("TestFile")
        assert "TestText" in text

    def test_append_twice(self, mf):
        mf.create("TestFile")
        mf.append("TestFile", "TestTextOne")
        mf.append("TestFile", "TestTextTwo")
        text = mf.read("TestFile")
        assert "TestTextOne" in text
        assert "TestTextTwo" in text

    def test_delete_file(self, mf):
        mf.create("TestFile")
        assert len(mf.get_files()) == 1
        mf.delete("TestFile")
        assert mf.get_files() == []

    def test_copy_file_without_content(self, mf):
        mf.create("TestFile")
        mf.copy("TestFile", "DestTestFile")
        assert "DestTestFile" in mf.get_files()

    def test_copy_file_content(self, mf):
        mf.create("TestFile")
        mf.append("TestFile", "ATestText")
        mf.copy("TestFile", "DestTestFile")
        assert mf.read("DestTestFile") == "ATestText"

    def test_copy_file_overwrite(self, mf):
        mf.create("TestFile")
        mf.append("TestFile", "TestText")
        mf.create("DestFile")
        mf.copy("TestFile", "DestFile")
        assert "TestText" in mf.read("DestFile")

    def test_move_file_without_content(self, mf):
        mf.create("TestFile")
        mf.move("TestFile", "DestFile")
        assert "DestFile" in mf.get_files()
        assert "TestFile" not in mf.get_files()

    def test_move_file_content(self, mf):
        mf.create("TestFile")
        mf.append("TestFile", "ATestText")
        mf.move("TestFile", "DestTestFile")
        assert mf.read("DestTestFile") == "ATestText"

    def test_move_file_overwrite(self, mf):
        mf.create("TestFile")
        mf.append("TestFile", "TestText")
        mf.create("DestFile")
        mf.move("TestFile", "DestFile")
        assert "TestText" in mf.read("DestFile")

    def test_exception_read_non_existent(self, mf):
        with pytest.raises(FilerException) as e:
            mf.read("TestFile")
        assert "TestFile" in str(e.value)

    def test_exception_append_non_existent(self, mf):
        with pytest.raises(FilerException) as e:
            mf.append("TestFile", "TestText")
        assert "TestFile" in str(e.value)

    def test_exception_delete_non_existent(self, mf):
        with pytest.raises(FilerException) as e:
            mf.delete("TestFile")
        assert "TestFile" in str(e.value)

    def test_exception_copy_non_existent(self, mf):
        with pytest.raises(FilerException) as e:
            mf.copy("TestFile", "DestFile")
        assert "TestFile" in str(e.value)

    def test_exception_move_non_existent(self, mf):
        with pytest.raises(FilerException) as e:
            mf.move("TestFile", "DestFile")
        assert "TestFile" in str(e.value)


@pytest.fixture()
def mfp():
    return MockFilingProfile()


class TestMockFilingProfile:
    def test_init(self):
        mfp = MockFilingProfile()

    def test_init_with_filer(self):
        MockFilingProfile(filer=MockFiler())

    def test_get_filer(self):
        mock_filer = MockFiler()
        mfp = MockFilingProfile(filer=mock_filer)
        assert mfp.get_filer() == mock_filer

    def test_get_random_text(self, mfp):
        text = mfp.get_random_text()
        assert isinstance(text, str)

    def test_get_random_filename(self, mfp):
        fn = mfp.get_random_text()
        assert isinstance(fn, str)

    def test_get_two_diffrent_random_filenames(self, mfp):
        fn1 = mfp.get_random_filename()
        fn2 = mfp.get_random_filename()
        assert not fn1 == fn2

    @pytest.mark.parametrize(
        "distribution", [
            "Next Action"
        ])
    def test_distributions(self, mfp, distribution):
        mfp.get_value(distribution)
