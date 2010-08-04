#!/usr/bin/env python


# std
import unittest

# vendor
import microjson


T_DICTS = [
    ('{}', {}),
    ('{"a":1}', {"a":1}),
    ('{"abcdef": "ghijkl"}', {'abcdef': 'ghijkl'}),

    # whitespace tests
    ('\t{\n\r\t }\r\n', {}),
    (' \t{ "a"\n:\t"b"\n\t}  ', {"a":"b"})
    ]

T_STRS = [
    ('"foo bar baz"', 'foo bar baz'),
    ('"abc\\"def\\"ghi"', 'abc"def"ghi'),

    # escaped unicode 
    ('"\u0124\u0113\u013a\u013e\u014d"', u"\u0124\u0113\u013a\u013e\u014d"),
    ('"\u201chello\u201d"', u"\u201chello\u201d"),

    # bare utf-8 
    ('"\xc6\x91"', u"\u0191"),
    ('"\xc4\x91"', u"\u0111"),

    # mixed utf-8 and escaped unicode
    ('"a\xc6\x91b\u0191c\u2018"', u"a\u0191b\u0191c\u2018"),
    ]

# test range of 16-bit characters > 0x7F
T_UNICODE = [('"' + c.encode('utf-8') + '"', c) for c in 
        (unichr(i) for i in range(0x80, 0x10000))
    ]

T_LISTS = [
    ('[]', []),
    ('[1,2,3]', [1,2,3]),
    ('[[1,2],["a","b"]]', [[1,2],["a","b"]]),

    # whitespace tests
    ('\t\n[\r\n \t]\n', []),
    ('  [\n\t1,\t2 ] \t', [1,2])

    ]

T_INTS = [
    ('0', 0),
    ('-1', -1),
    ('123', 123), 
    ('-2147483648', -2147483648),
    ('2147483648', 2147483648),
    ('4294967296', 4294967296),
    ('9223372036854775808', 9223372036854775808L),
    ('18446744073709551616', 18446744073709551616L)
    ]

T_FLOATS = [
    ('.1', 0.1),
    ('-.1', -0.1),
    ('1.0', 1.0),
    ('-1.0', -1.0),
    ('3.14159', 3.14159),
    ('-3.14159', -3.14159),
    ('1E1', 1E1),
    ('-1E2', -1E2),
    ('-1E-2', -1E-2),
    ('12E-2', 12E-2),
    ('1.8446744073709552e19', 1.8446744073709552e19)
    ]

T_FIXED = [('true', True), ('false', False), ('null', None)]

# bare values (not wrapped in {} or []) are not yet parseable
T_MALFORMED = [
    '',             # empty
    '123',          # bare int 
    '[0123]',       # number with leading zero
    '"ewg"',        # bare string
    'wegouhweg',    # bare char data
    '["abcdef]',    # string missing trailing '"'
    '["a","b"',     # list missing trailing ']'
    '{"a:"b"}',     # key missing trailing '"'
    '{"a":13',      # dict missing trailing '}'
    '{123: 456}'    # object keys must be quoted
    ]


def wrap(cases):
    "wrap bare values in a list to produce valid json data"
    return [('[%s]' % js, [py]) for js, py in cases]


class TestMicrojson(unittest.TestCase):

    def do_test(self, cases):
        for js, py in cases:
            r = microjson.parse_json(js)
            self.assertEquals(r, py)

    def test_dict(self):
        self.do_test(T_DICTS)

    def test_list(self):
        self.do_test(T_LISTS)

    def test_string(self):
        self.do_test(wrap(T_STRS))

    def test_unicode(self):
        self.do_test(wrap(T_UNICODE))

    def test_integer(self):
        self.do_test(wrap(T_INTS))
    
    def test_floats(self):
        self.do_test(wrap(T_FLOATS))

    def test_null_and_bool(self):
        self.do_test(wrap(T_FIXED))

    def test_malformed(self):
        "assert a JsonError is raised for these cases"
        for js in T_MALFORMED:
            self.assertRaises(microjson.JsonError, microjson.parse_json, js)

def main():
    unittest.main()


if __name__ == "__main__":
    main()
        


