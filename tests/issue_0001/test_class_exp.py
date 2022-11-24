from bernard.utils import ClassExp


# noinspection PyProtectedMember
def test_compile():
    ce = ClassExp(r"(RawText|Text)+ QuickRepliesList?")
    expect = "re.compile('((?:RawText,)|(?:Text,))+(?:QuickRepliesList,)?')"
    assert repr(ce._compiled_expression) == expect


# noinspection PyProtectedMember
def test_make_string():
    ce = ClassExp(r"")
    expect = "int,bool,int,bool,"
    assert ce._make_string([42, True, 42, False]) == expect


def test_match():
    ce = ClassExp(r"(int|bool)+ float")
    assert ce.match([42, 42, 42, True, 42, 42.0])
    assert not ce.match([42, True, 42, True])
