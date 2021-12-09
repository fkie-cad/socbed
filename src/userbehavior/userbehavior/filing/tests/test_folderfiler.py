#!/usr/bin/python3
# -*- coding: utf-8 -*-

import os
import os.path

import pytest

from userbehavior.filing.filer import FilerException
from userbehavior.filing.folderfiler import FolderFiler


@pytest.fixture()
def ff(tmpdir):
    tmp_folder = str(tmpdir)
    return FolderFiler(tmp_folder)


class TestFolderFiler:
    def test_get_folder(self, tmpdir):
        tmp_folder = str(tmpdir)
        ff = FolderFiler(tmp_folder)
        assert ff.get_folder() == tmp_folder

    def test_exception_if_path_is_not_string(self):
        with pytest.raises(FilerException) as e:
            ff = FolderFiler(folder=5)

    def test_get_files(self, ff: FolderFiler):
        assert isinstance(ff.get_files(), list)

    def test_get_files_not_subfolders(self, ff: FolderFiler):
        folder = ff.get_folder()
        os.mkdir(os.path.join(folder, "TestFolder"))
        files = ff.get_files()
        assert "TestFolder" not in files

    def test_create(self, ff: FolderFiler):
        ff.create("TF1")
        files = ff.get_files()
        assert "TF1" in files

    def test_create_two_files(self, ff: FolderFiler):
        ff.create("TF1")
        ff.create("TF2")
        files = ff.get_files()
        assert "TF1" in files
        assert "TF2" in files

    def test_read_empty_file(self, ff: FolderFiler):
        ff.create("TestFile")
        text = ff.read("TestFile")
        assert text == ""

    def test_append_twice(self, ff: FolderFiler):
        ff.create("TestFile")
        ff.append("TestFile", "TestTextOne")
        ff.append("TestFile", "TestTextTwo")
        text = ff.read("TestFile")
        assert "TestTextOne" in text
        assert "TestTextTwo" in text

    def test_delete_file(self, ff: FolderFiler):
        ff.create("TestFile")
        assert len(ff.get_files()) == 1
        ff.delete("TestFile")
        assert ff.get_files() == []

    def test_copy_file_without_content(self, ff: FolderFiler):
        ff.create("TestFile")
        ff.copy("TestFile", "DestTestFile")
        assert "DestTestFile" in ff.get_files()

    def test_copy_file_content(self, ff: FolderFiler):
        ff.create("TestFile")
        ff.append("TestFile", "ATestText")
        ff.copy("TestFile", "DestTestFile")
        assert ff.read("DestTestFile") == "ATestText"

    def test_copy_file_overwrite(self, ff: FolderFiler):
        ff.create("TestFile")
        ff.append("TestFile", "TestText")
        ff.create("DestFile")
        ff.copy("TestFile", "DestFile")
        assert "TestText" in ff.read("DestFile")

    def test_move_file_without_content(self, ff: FolderFiler):
        ff.create("TestFile")
        ff.move("TestFile", "DestFile")
        assert "DestFile" in ff.get_files()
        assert "TestFile" not in ff.get_files()

    def test_move_file_overwrite(self, ff: FolderFiler):
        ff.create("TestFile")
        ff.append("TestFile", "TestText")
        ff.create("DestFile")
        ff.move("TestFile", "DestFile")
        assert "TestText" in ff.read("DestFile")

    def test_move_file_content(self, ff: FolderFiler):
        ff.create("TestFile")
        ff.append("TestFile", "ATestText")
        ff.move("TestFile", "DestTestFile")
        assert ff.read("DestTestFile") == "ATestText"

    def test_exception_read_non_existent(self, ff: FolderFiler):
        with pytest.raises(FilerException) as e:
            ff.read("TestFile")
        assert "TestFile" in str(e.value)

    def test_exception_append_non_existent(self, ff: FolderFiler):
        with pytest.raises(FilerException) as e:
            ff.append("TestFile", "TestText")
        assert "TestFile" in str(e.value)

    def test_exception_delete_non_existent(self, ff: FolderFiler):
        with pytest.raises(FilerException) as e:
            ff.delete("TestFile")
        assert "TestFile" in str(e.value)

    def test_exception_copy_non_existent(self, ff: FolderFiler):
        with pytest.raises(FilerException) as e:
            ff.copy("TestFile", "DestFile")
        assert "TestFile" in str(e.value)

    def test_exception_move_non_existent(self, ff: FolderFiler):
        with pytest.raises(FilerException) as e:
            ff.move("TestFile", "DestFile")
        assert "TestFile" in str(e.value)
