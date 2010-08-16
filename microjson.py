
# microjson - Minimal JSON parser for use in standalone scripts.
# No warranty. Free to use/modify as you see fit. 
# Send ideas, bugs to http://github.com/phensley
# Copyright (c) 2010 Patrick Hensley <spaceboy@indirect.com>


# std
import codecs
import StringIO
import string


# character classes
WS = set([' ','\t','\r','\n','\b','\f'])
NUMS = set([str(i) for i in range(0, 10)])
NUMSTART = NUMS.union(['.','-','+'])
NUMCHARS = NUMSTART.union(['e','E'])
ESC_MAP = {'n':'\n','t':'\t','r':'\r','b':'\b','f':'\f'}

# error messages
E_BYTES = 'input string must be type str containing ASCII or UTF-8 bytes'
E_MALF = 'malformed JSON data'
E_TRUNC = 'truncated JSON data'
E_BOOL = 'expected boolean'
E_NULL = 'expected null'
E_LITEM = 'expected list item'
E_DKEY = 'expected key'
E_COLON = 'missing colon after key'
E_EMPTY = 'found empty string, not valid JSON data'
E_WRAP = 'can only parse JSON wrapped in an object {} or array []'
E_BADESC = 'bad escape character found'


class JSONError(Exception):
    pass


def jsonerr(msg, stm=None, pos=0):
    if stm:
        msg += ' at position %d, "%s"' % (pos, repr(stm.substr(pos, 32)))
    return JSONError(msg)


class JSONStream(object):

    # no longer inherit directly from StringIO, since we only want to
    # expose the methods below and not allow direct access to the 
    # underlying stream.

    def __init__(self, data):
        self._stm = StringIO.StringIO(data)

    @property
    def pos(self):
        return self._stm.pos

    @property
    def len(self):
        return self._stm.len

    def getvalue(self):
        return self._stm.getvalue()

    def skipspaces(self):
        "post-cond: read pointer will be over first non-WS char"
        self._skip(lambda c: c not in WS)

    def _skip(self, stopcond):
        while True:
            c = self.peek()
            if stopcond(c) or c == '':
                break
            self.next()

    def next(self, size=1):
        return self._stm.read(size)

    def next_ord(self):
        return ord(self.next())

    def peek(self):
        if self.pos == self.len:
            return ''
        return self.getvalue()[self.pos]

    def substr(self, pos, length):
        return self.getvalue()[pos:pos+length]


def decode_utf8(c0, stm):
    c0 = ord(c0)
    r = 0xFFFD      # unicode replacement character
    nc = stm.next_ord

    # 110yyyyy 10zzzzzz
    if (c0 & 0xE0) == 0xC0:
        r = ((c0 & 0x1F) << 6) + (nc() & 0x3F)

    # 1110xxxx 10yyyyyy 10zzzzzz
    elif (c0 & 0xF0) == 0xE0:
        r = ((c0 & 0x0F) << 12) + ((nc() & 0x3F) << 6) + (nc() & 0x3F)

    # 11110www 10xxxxxx 10yyyyyy 10zzzzzz
    elif (c0 & 0xF8) == 0xF0:
        r = ((c0 & 0x07) << 18) + ((nc() & 0x3F) << 12) + \
            ((nc() & 0x3F) << 6) + (nc() & 0x3F)
    return unichr(r)


def decode_escape(c, stm):
    # whitespace
    v = ESC_MAP.get(c, None)
    if v is not None:
        return v

    # plain character
    elif c != 'u':
        return c

    # decode unicode escape \u1234
    sv = 12
    r = 0
    for i in range(0, 4):
        r |= int(stm.next(), 16) << sv
        sv -= 4
    return unichr(r)


def parse_str(stm):
    # skip over '"'
    stm.next()  
    r = []
    while True:
        c = stm.next()
        if c == '':
            raise jsonerr(E_TRUNC, stm, stm.pos - 1)
        elif c == '\\':
            c = stm.next()
            r.append(decode_escape(c, stm))
        elif c == '"':
            return ''.join(r)
        elif c > '\x7f':
            r.append(decode_utf8(c, stm))
        else:
            r.append(c)


def parse_fixed(stm, expected, value, errmsg):
    off = len(expected)
    pos = stm.pos
    if stm.substr(pos, off) == expected:
        stm.next(off)
        return value
    raise jsonerr(errmsg, stm, pos)


def parse_num(stm):
    # Per rfc 4627 section 2.4 '0' and '0.1' are valid, but '01' and
    # '01.1' are not, presumably since this would be confused with an
    # octal number.  This rule is not enforced.
    is_float = is_neg = saw_exp = 0
    pos = stm.pos
    while True:
        c = stm.peek()

        if c == '':
            raise jsonerr(E_TRUNC, stm, pos)

        if c not in NUMCHARS:
            break

        if c == '-' and not saw_exp:
            is_neg = 1
        elif c in ('.','e','E'):
            is_float = 1
            if c in ('e','E'):
                saw_exp = 1
        stm.next() 

    s = stm.substr(pos, stm.pos - pos)
    if is_float:
        return float(s)
    return long(s)


def parse_list(stm):
    # skip over '['
    stm.next()  
    result = []
    pos = stm.pos
    while True:
        stm.skipspaces()
        c = stm.peek()
        if c == '':
            raise jsonerr(E_TRUNC, stm, pos)

        elif c == ']':
            stm.next()
            return result

        elif c == ',':
            stm.next()
            result.append(parse_json_raw(stm))
            continue

        elif not result:
            # first list item
            result.append(parse_json_raw(stm))
            continue
        

def parse_dict(stm):
    # skip over '{'
    stm.next()
    result = {}
    expect_key = 0
    pos = stm.pos
    while True:
        stm.skipspaces()
        c = stm.peek()

        if c == '':
            raise jsonerr(E_TRUNC, stm, pos)

        # end of dictionary, or next item
        if c in ('}',','):
            stm.next()
            if expect_key:
                raise jsonerr(E_DKEY, stm, stm.pos)
            if c == '}':
                return result
            expect_key = 1
            continue

        # parse out a key/value pair
        elif c == '"':
            key = parse_str(stm)
            stm.skipspaces()
            c = stm.next()
            if c != ':':
                raise jsonerr(E_COLON, stm, stm.pos)

            stm.skipspaces()
            val = parse_json_raw(stm)
            result[key] = val
            expect_key = 0
            continue

        # unexpected character in middle of dict
        raise jsonerr(E_MALF, stm, stm.pos)


def parse_json(data):
    if not isinstance(data, str):
        raise jsonerr(E_BYTES)
    data = data.strip()
    stm = JSONStream(data)
    if not data:
        raise jsonerr(E_EMPTY, stm, stm.pos)
    if data[0] not in ('{','['):
        raise jsonerr(E_WRAP, stm, stm.pos)
    return parse_json_raw(stm)


def parse_json_raw(stm):
    while True:
        stm.skipspaces()
        c = stm.peek()
        if c == '"': 
            return parse_str(stm)
        elif c == '{': 
            return parse_dict(stm)
        elif c == '[': 
            return parse_list(stm)
        elif c == 't':
            return parse_fixed(stm, 'true', True, E_BOOL)
        elif c == 'f':
            return parse_fixed(stm, 'false', False, E_BOOL)
        elif c == 'n': 
            return parse_fixed(stm, 'null', None, E_NULL)
        elif c in NUMSTART:
            return parse_num(stm)

        raise jsonerr(E_MALF, stm, stm.pos)

