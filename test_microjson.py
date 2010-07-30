#!/usr/bin/env python

# std
import unittest

# vendor
import microjson


T_DICTS = [
    ('{"abcdef": "ghijkl"}', {'abcdef': 'ghijkl'})
    ]

T_STRS = [
    ('"foo bar baz"', 'foo bar baz'),
    ('"abc\\"def\\"ghi"', 'abc"def"ghi')
    ]

T_LISTS = [
    ('[1,2,3]', [1,2,3]),
    ('[[1,2],["a","b"]]', [[1,2],["a","b"]])
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
    ('1.8446744073709552e19', 1.8446744073709552e19),
    ('Infinity', float('infinity')),
    ('-Infinity', float('-infinity'))
    ]

T_FIXED = [('true', True), ('false', False), ('null', None)]

T_MALFORMED = [
    '',
    '123',      # bare values not yet parseable
    '"ewg"',
    'wegouhweg',
    '["abcdef]',
    '["a","b"', 
    '[Inf]',
    '{"a:"b"}',
    '{"a":13',
    '{123: 456}'
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
        


