from bernard.i18n.loaders import extract_ranges


def test_extract_ranges():
    row = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10"]
    ranges = [
        0,
        (1, 2),
        (8, None),
    ]

    extracted = extract_ranges(row, ranges)

    assert extracted == ["1", "2", "9", "10"]
