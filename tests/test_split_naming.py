import re


def test_core_pages_regex_matches():
    name = "20250101_foo_pages_1-2.pdf"
    m = re.search(r"_pages_(\d+)-(\d+)\\.pdf$", name)
    assert m is None, "Old broken pattern should not match"

    m2 = re.search(r"_pages_(\d+)-(\d+)\.pdf$", name)
    assert m2, "Correct pattern should match"
    assert m2.group(1) == "1"
    assert m2.group(2) == "2"


def test_split_pages_regex_matches():
    name = "20250101_foo_split_pages_3-6.pdf"
    m = re.search(r"_split_pages_(\d+)-(\d+)\\.pdf$", name)
    assert m is None, "Old broken pattern should not match"

    m2 = re.search(r"_split_pages_(\d+)-(\d+)\.pdf$", name)
    assert m2, "Correct pattern should match"
    assert m2.group(1) == "3"
    assert m2.group(2) == "6"


def test_previous_end_extraction():
    prev = "20250101_foo_split_pages_3-6.pdf"
    m2 = re.search(r"_split_pages_(\d+)-(\d+)\.pdf$", prev)
    assert m2
    assert int(m2.group(2)) == 6
