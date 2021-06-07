import sys
import re
import math

BEGIN = 'BEGIN'
END = 'END'


class Pawky:
    """The base `awk` class. It contains almost all the `awk` builtin variables and functions.

    These builtin variables from `awk` are currently available.
    :ivar str CONVFMT: Format for internal conversion of numbers  to  string, initially = "%.6g". Currently unused.
    :ivar str FILENAME: Name of the current input file.
    :ivar int FNR: Current record number in FILENAME.
    :ivar str FS: Splits records into fields as a regular expression.
    :ivar int NF: Number of fields in the current record.
    :ivar int NR: Current record number in the total input stream.
    :ivar str OFMT: Format for printing numbers; initially = "%.6g". Currently unused.
    :ivar str OFS: Inserted between fields on output, initially = " ". Use this manually or use `Pawky.print()`.
    :ivar str ORS: Terminates each record on output, initially = "\\n". Use this manually or use `Pawky.print`.
    :ivar int RLENGTH: Length  set by the last call to the built-in function, `match()`. Currently unused.
    :ivar str RS: Input record separator, initially = "\\n".
    :ivar int RSTART: Index set by the last call to `match()`.

    Other instance variables
    :ivar bool IGNORECASE: Specifies whether the regular expression pattern matching should ignore case,
                           initially = True.
    :ivar function begin: If not `None`, this function is called before processing any file.
    :ivar function mid: If not `None`, this function is called for each line of each file.
    :ivar function end: If not `None`, this function is called after processing all files.
    :ivar dict refun: Contains the pattern and the funtion to call when the pattern matches for each line.
    """

    def __init__(self, fs=r'[ \t\n]+', autoparse=False):
        """Initializes the `Pawky` class.

        :param str fs: The field separator (regular expression) to use for splitting the records. Defaults to
                       '[ \\t\\n]+'.
        :param bool autoparse: If `True`, possible fields are automatically parsed to `int` or `float`. Defaults to
                               False.
        """
        self.CONVFMT = '%.6g'
        self.FILENAME = None
        self.FNR = 0
        self.FS = fs
        self.NF = None
        self.NR = 0
        self.OFMT = '%.6g'
        self.OFS = ' '
        self.ORS = '\n'
        self.RLENGTH = None
        self.RS = '\n'
        self.RSTART = None
        self.IGNORECASE = False

        self.begin = None
        self.mid = lambda *args: print(*args, sep=self.OFS, end=self.ORS)
        self.end = None
        self.refun = {}

        self.autoparse = autoparse
        self.__record = None
        self.__old_stdout = None

    def gsub(self, r, s, t=None):
        """Global substitution, every match of regular expression r in variable t is replaced by string s. The replaced
        string and the number of replacements is returned. If t is omitted, $0 is used. An \i in the replacement string
        s is replaced by the ith matched group of t. \\\\ (two backslashes) put literal \ in the replacement string. For
        a `awk` like replacement, wrap the pattern r in (), and use \\1 (single backslash) instead of &.

        :return: Tuple with (replaced string, number of replacements).
        :rtype: tuple
        """
        if t is None:
            t = self.__record['$0']
        return re.subn(r, s, t, flags=self.IGNORECASE)

    def index(self, s, t):
        """If t is a substring of s, then the position where t starts is returned, else 0 is returned. The first
        character of s is in position 1."""
        try:
            return s.index(t) + 1
        except:
            return 0

    def length(self, s):
        """Returns the length of string s."""
        return len(s)

    def match(self, s, r):
        """Returns the index of the first longest match of regular expression r in string s. Returns 0 if no match. As a
        side effect, RSTART is set to the return value. RLENGTH is set to the length of the match or -1 if no match. If
        the empty string is matched, RLENGTH is set to 0, and 1 is returned if the match is at the front, and
        length(s)+1 is returned if the match is at the back."""
        m = re.search(r, s, flags=self.IGNORECASE)
        if m is None:
            self.RSTART = 0
            self.RLENGTH = -1
        else:
            s = m.span()
            self.RSTART = s[0] + 1
            self.RLENGTH = s[1] - s[0]
        return self.RSTART

    def split(self, s, A=None, r=None):
        """String s is split into fields by regular expression r and the fields are loaded into array A. If A is
        omitted, fields is returned. Otherwise, A is assumed to be a list and the fields are loaded into it and the
        number of fields is returned. If r is omitted, FS is used."""
        if r is None:
            r = self.FS
        s = str(s)
        if r == ' ':
            s = s.strip()
            r = r'[ \t\n]+'
        fields = re.split(r, s)
        if A is None:
            return fields
        else:
            A.clear()
            A.extend(fields)
            return len(A)

    def sprintf(self, format, expr_list):
        """Returns a string constructed from expr_list according to format. Uses Python's % operator with strings."""
        return format % expr_list

    def sub(self, r, s, t=None):
        """Single substitution, same as gsub() except at most one substitution.

        :return: Tuple with (replaced string, number of replacements).
        :rtype: tuple
        """
        if t is None:
            t = self.__record['$0']
        return re.subn(r, s, t, count=1, flags=self.IGNORECASE)

    def substr(self, s, i, n=None):
        """Returns the substring of string s, starting at index i, of length n. If n is omitted, the suffix of s,
        starting at i is returned."""
        return s[i:] if n is None else s[i:i+n]

    def tolower(self, s):
        """Returns a copy of s with all upper case characters converted to lower case."""
        return s.lower()

    def toupper(self, s):
        """Returns a copy of s with all lower case characters converted to upper case."""
        return s.upper()

    def __setitem__(self, key, value):
        """Assigns functions to run on pattern match. This is used to insert values into `Pawky.refun`.
        Use this like `awk[<pattern>] = f`, where f is a function that will run if the pattern matches. Supported
        patterns include:

          * `awk['BEGIN'] = f`: Sets `Pawky.begin`, the function that will be called before processing any file.
          * `awk['END'] = f`: Sets `Pawky.end`, the function that will be called after processing all files.
          * `awk[...] = f`, `awk[:] = f`, `awk[::] = f`: Sets `Pawky.mid`, the function that will be called for each
            line of each file.
          * `awk[n] = f`: The function that will be called for the nth line. If n is positive, it'll be called for the
            nth line of all the files together; it's like comparing with NR. If n is negative, it'll be called for the
            nth line of each file separately; it's like comparing with FNR. In either case, the absolute value of n is
            used for indexing. Note that, just like in `awk`, here too it's 1-indexed.
          * `awk[a:b:c] = f`: The function that will be called for every cth line starting from the ath (inclusive) line
            upto the bth (exclusive) line. The slices behaves the same way as normal Python slices, but negative values
            for a and b are not allowed. If c is positive, the slices represents line numbers for all the files
            together. If c is negative, the slices represents line numbers for each file separately. In either case, the
            absolute value of c is used as the step size. Note that, just like in `awk`, here too it's 1-indexed.
          * `awk['pattern'] = f`: Calls the function if the record matches the regular expression pattern.
          * `awk[field, 'pattern'] = f`: Calls the function if the field matches the regular expression pattern. The
            field is used as `record[field]`.

        :param key: The line or pattern to match.
        :param function value: The function to run.
        """
        if key == BEGIN:
            self.begin = value
        elif key == END:
            self.end = value
        elif key == Ellipsis:
            self.mid = value
        elif isinstance(key, slice):
            if key.start == None and key.stop == None and key.step == None:
                self.mid = value
            else:
                self.refun[(1 if key.start is None else key.start, key.stop,
                            1 if key.step is None else key.step)] = value
        else:  # str or int or (field, str)
            self.refun[key] = value

    def __getattribute__(self, name):
        """Return the attributes of Pawky and allows for calling arithmetic functions directly from the math module.

        :param str name: The attribute name.
        :return: The attribute value.
        """
        try:
            return super().__getattribute__(name)
        except AttributeError:
            return getattr(math, name)

    def __call__(self, *fns, fs=r'[ \t\n]+', asregex=True):
        """Processes all the files passed.
        Since there's no way to know how many times this will be called, unlike `awk`, here BEGIN and END are called
        once everytime this is called. So, everytime this method is called, functions are called in the order: BEGIN,
        Process all the files, END. This will also match the records with the patterns and run the functions. The order
        in which the functions are called is not defined. Except BEGIN and END, a instance of Record for each line will
        be passed to all the functions.

        Note that, this'll reset FNR to 0 everytime this is called, before processing any files. This'll also reset NR
        to 0 before processing each of the files, just like in `awk`.

        :param str fns: The files to process.
        :param str fs: The file separator (regular expression) to use for the files, defaults to '[ \\t\\n]+'. This will
                       change FS.
        :param bool asregex: If True, fs is used as a regular expression, otherwise it is used as it is, like a string.
                             Defaults to True.
        """
        self.FS = fs if asregex else re.escape(fs)
        if self.begin is not None:
            self.begin()
        self.FNR = 0
        for fn in fns:
            self.FILENAME = fn
            with open(self.FILENAME) as f:
                self.NR = 0
                for record in re.split(self.RS, f.read()):
                    self.FNR += 1
                    self.NR += 1
                    self.__record = Record(self, record)
                    if self.mid is not None:
                        self.mid(self.__record)
                    for k in self.refun:
                        if isinstance(k, int):
                            if (k > 0 and k == self.NR) or (k < 0 and -k == self.FNR):
                                self.refun[k](self.__record)
                        elif isinstance(k, str):
                            if re.search(k, record, re.IGNORECASE if self.IGNORECASE else 0):
                                self.refun[k](self.__record)
                        elif isinstance(k, tuple):
                            if len(k) == 2:
                                if re.search(k[1], str(self.__record[k[0]]), re.IGNORECASE if self.IGNORECASE else 0):
                                    self.refun[k](self.__record)
                            elif len(k) == 3:
                                i = self.NR if k[2] > 0 else self.FNR
                                if (k[1] is None or i < k[1]) and i >= k[0] and (i - k[0]) % k[2] == 0:
                                    self.refun[k](self.__record)
        if self.end is not None:
            self.end()

    def __lt__(self, value):
        """Used to simulate input redirection. This allows to call Pawky with a file as `awk < 'filename'`. The input
        can either be a file name or a iterator of file names. This is same as `__call__`, only without the keyword
        arguments.

        :param value: File name.
        :return: The current instance.
        :rtype: Pawky
        """
        if isinstance(value, str):
            self(value)
        else:
            self(*value)
        return self

    def __redirect_stdout(self, value, mode):
        if value is None:
            if self.__old_stdout is not None:
                sys.stdout.close()
                sys.stdout = self.__old_stdout
                self.__old_stdout = None
        else:
            if self.__old_stdout is None:
                self.__old_stdout = sys.stdout
            sys.stdout = open(value, mode)
        return self

    def __gt__(self, value):
        """Used to simulate output redirection. This allows to write the output to a file with `awk > 'filename'`. Note
        that, this'll change the system stdout, thus any kinds of output will be redirected to the file. Also, since how
        Python works, use this before starting processing to redirect the output. To reset the output back to standard
        output, pass `None`.

        :param str value: File name.
        :return: The current instance.
        :rtype: Pawky
        """
        return self.__redirect_stdout(value, 'w')

    def __rshift__(self, value):
        """Used to simulate output redirection. This allows to append the output to a file with `awk >> 'filename'`.
        Note that, this'll change the system stdout, thus any kinds of output will be redirected to the file. Also,
        since how Python works, use this before starting processing to redirect the output. To reset the output back to
        standard output, pass `None`.

        :param str value: File name.
        :return: The current instance.
        :rtype: Pawky
        """
        return self.__redirect_stdout(value, 'a')


class Record:
    """The record class. All the methods from the parent Pawky class are also available.

    :ivar Pawky awk: The parent `awk` class.
    :ivar str record: The record string, this'll be updated if the fields change.
    :ivar list fields: The fields of the record.
    """

    def __init__(self, awk, record):
        """Initialize the record class. This is used internally by Pawky.

        :param Pawky awk: The parent `Pawky` instance.
        :param str record: The record line.
        """
        self.awk = awk
        self.record = record
        self.fields = re.split(awk.FS, record)
        self.awk.NF = len(self.fields)
        self.parse_fields()

        self.__idx = 0

    def parse_fields(self, forced=False):
        """Parse the fields to `int` or `float` if possible and if Pawky.autoparse is True.

        :param bool forced: If True, the fields are parsed regardless of the value of Pawky.autoparse, defaults to
                            False.
        """
        if self.awk.autoparse or forced:
            for i in range(self.awk.NF):
                try:
                    self.fields[i] = int(self.fields[i])
                except:
                    try:
                        self.fields[i] = float(self.fields[i])
                    except:
                        pass

    def __str__(self):
        """Returns the string representation of the current record.

        :return: The string representation.
        :rtype: str
        """
        return self.record

    def __len__(self):
        """Return the number of fields in the record.

        :return: Number of fields.
        :rtype: int
        """
        return self.awk.NF

    def __getitem__(self, key):
        """Returns the fields from the record. The key can be one of:

          * `record['$1']`, `record['S1']`, `record['D1']`, `record['F1']`, `record['1']`: Return the 1st field from the
            record. If the key is a string the indexing is 1 based; if 0 is passed, the whole record is returned. This
            will also not raise an exception if the index is out of bounds, rather it'll return the empty string just
            like in `awk`.
          * `record['$NF']`: Return the last field from the record. Instead of NF you can use any attribute of the
            record object. Note that, unlike `awk`, you can't use things like `record['$(NF-1)']` or `record['$(1+2)']`
            etc.
          * `record[0]`: Returns the first field of the record. If the key is a int the indexing is 0-based. It'll also
            raise exception on index out of bounds. Obviously, you can't get the whole record this way.

        :param key: The field name.
        :return: The field value.
        """
        if isinstance(key, str):
            if key.startswith('$') or key.startswith('S') or key.startswith('D') or key.startswith('F'):
                key = key[1:]
            try:
                idx = int(key)
            except ValueError:
                idx = self.__getattribute__(key)
            if idx == 0:
                return self.record
            elif idx <= self.awk.NF:
                return self.fields[idx - 1]
            else:
                return ''
        else:
            return self.fields[key]

    def __setitem__(self, key, value):
        """Set the fields or the record. The key (see `__getitem__` for more information) can be one of:

          * `record['$1']`, `record['S1']`, `record['D1']`, `record['F1']`, `record['1']`, `record[0]`: The 1st field is
            set. This'll change the record with the OFS.
          * `record['$NF']`: The last field is set. This'll change the record with the OFS.
          * `record['$0']`: The whole record is set. This'll also set the fields and NF accordingly.
          * `record['$x']` where x > NF: Extra fields are added and the corresponding field is set. This'll change the
            record with the OFS and change NF accordingly. If the key is a int, trying to set a out of bounds field this
            way will raise an exception.

        :param key: The field name.
        :param value: The new value of the field or record.
        """
        if isinstance(key, str):
            if key.startswith('$') or key.startswith('S') or key.startswith('D') or key.startswith('F'):
                key = key[1:]
            try:
                idx = int(key)
            except ValueError:
                idx = self.__getattribute__(key)
            if idx == 0:
                self.record = value
                self.fields = re.split(self.awk.FS, value)
                self.awk.NF = len(self.fields)
                self.parse_fields()
                return
            elif idx > self.awk.NF:
                self.fields += [''] * (idx - self.awk.NF)
                self.awk.NF = idx
            idx -= 1
        else:
            idx = key
        self.fields[idx] = value
        self.record = self.awk.OFS.join(map(str, self.fields))
        self.parse_fields()

    def __getattribute__(self, name):
        """Return the attributes of the record. This also allows the record to access the attributes of its parent Pawky
        instance. You can also access the fields this way. For instance, doing `record.S1` is the same as doing
        `record['S1']`.

        :param str name: The attribute name.
        :return: The attribute value.
        """
        try:
            return super().__getattribute__(name)
        except AttributeError:
            try:
                return self.awk.__getattribute__(name)
            except AttributeError:
                return self[name]

    def __iter__(self):
        """Allows the record to be iterated over. Use as `for r in record`.

        :return: The iterator (itself).
        :rtype: Record
        """
        self.__idx = 0
        return self

    def __next__(self):
        """Returns the next field for the iterator.

        :raises StopIteration: Exception to stop iteration.
        :return: The field value.
        """
        if self.__idx < self.awk.NF:
            field = self.fields[self.__idx]
            self.__idx += 1
            return field
        else:
            raise StopIteration
