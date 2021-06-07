# Pawky

### The Python version of `awk`.

#### awk

> **pattern scanning and text processing language**
>
> The [AWK](http://man7.org/linux/man-pages/man1/awk.1p.html) language is useful for the manipulation of data files, text retrieval and processing, and for prototyping and experimenting with algorithms. [It](https://en.wikipedia.org/wiki/AWK) is a data-driven scripting language consisting of a set of actions to be taken against streams of textual data – either run directly on files or used as part of a pipeline – for purposes of extracting or transforming text, such as producing formatted reports.

## Why Pawky?

Pawky is just a for-fun project to design an `awk`-like program in Python. Pawky is neither a recreation of `awk` nor an `awk` parser. Pawky allows you to use an `awk`-like syntax in Python to easily process files. Most of the built-in `awk` variables and functions are available, but most of them need to be used manually. Pawky tries to give a shell-like feel (syntax), but the more usual Python syntax is recommended. Follow the codes below and try each snippet; trying random code is the best way to learn.

## Get Started

Start by importing Pawky and creating an instance of Pawky.

```python
from pawky import Pawky

awk = Pawky()
```

To process files, call the instance (`awk`) and pass the file names. By default, all the lines will be printed to the standard output.

```python
awk('file1.txt', 'file2.txt', ...)
```

To specify a field separator, pass that as a keyword argument. By default, the field separator is used as a regular expression. To use it as it is, pass a third keyword argument, `asregex=False`.

```python
awk('marks.txt', fs='\t')
```

You can also use the input redirection syntax from Bash to process the files. This way, however, you can't set the field separator.

```python
awk < 'marks.txt'  # For a single file
awk < ('marks1.txt', 'marks2.txt')  # For multiple files
```

### Specifying Functions

The default function that is executed for each of the lines is specified in `Pawky.mid`. You can change it with either of the following lines:

```python
awk.mid = f  # It is recommended to use this, the others are just syntactic sugar
awk[...] = f
awk[:] = f
awk[::] = f
```

The function that is executed before processing any file is specified in `Pawky.begin` and the function that is executed after processing all the files is specified in `Pawky.end`. You can change them with either of the following lines:

```python
awk.begin = f
awk['BEGIN'] = f

awk.end = f
awk['END'] = f
```

Since there's no way to know how many times `awk` will be called, BEGIN and END is called once every time `awk` is called. Thus, the order of execution will be different depending on how `awk` was called.

```python
awk('file1.txt')
awk('file2.txt')
# Functions will be executed as:
# BEGIN
# Process file1.txt
# END
# BEGIN
# Process file2.txt
# END

awk('file1.txt', 'file2.txt')
# Functions will be executed as:
# BEGIN
# Process file1.txt
# Process file2.txt
# END
```

If either of `Pawky.begin`, `Pawky.mid` or `Pawky.end` is `None`, it is ignored.

## Output Redirection

Bash-like output redirection is also possible with Pawky.

```python
awk > 'out.txt'  # Output will be written (overwritten) to out.txt
awk >> 'out.txt'  # Output will be written (appended) to out.txt
```

Because of how Python works, you should use this separately before calling `awk` for processing the files.

```python
awk < 'marks.txt' > 'out.txt'  # This line is interpreted as
(awk < 'marks.txt') and ('marks.txt' > 'out.txt')

# Instead use
awk > 'out.txt'
awk < 'marks.txt'
# or even
(awk > 'out.txt') < 'marks.txt'
```

This step completely redirects the standard output to the file. Thus, any kind of output operation, even from other `print` statements not related to Pawky, will be written to the file. To reset the output to normal, do

```python
awk > None
# or
awk >> None
```

## Pattern Matching

Pawky can call functions on certain lines if the line matches a pattern.

First, disable the default print behavior by setting `mid` to `None`.

```python
awk.mid = None
```

Now specify a function that will be called only for the first line. Note that the indexing is 1-based.

```python
awk[1] = print  # Print the first line
```

Now specify another function for the rest of the lines. Note the use of the [slice operator](https://python-reference.readthedocs.io/en/latest/docs/brackets/slicing.html).

```python
awk[2:] = lambda r: print(r, '# Student')  # This will print the line 2 and above
```

And just for fun, we'll also print every third line starting from the second line up to the seventh line separately too. Again, note the use of the slice operator.

```python
awk[2:8:3] = lambda r: print(r, '# Fun')  # 8 since stop is exclusive
```

Now calling this on [marks.txt](marks.txt) will produce the following output. Note that the order in which the above functions will be executed for the same line is not defined.

```
Name     Math Science English Arts
Wade        1     6.0      92   13 # Student
Wade        1     6.0      92   13 # Fun
Anwar       2      51      16   10 # Student
Ismael      4       2      38   72 # Student
Nikkita     8      10     4.2   26 # Student
Nikkita     8      10     4.2   26 # Fun
Mariella   16      24      32   21 # Student
Jimmy      32      20      76   44 # Student
Ace        64      48     8.3   52 # Student
Johan      12      40      65   42 # Student
Martine     8    96.1      53   88 # Student
Mac        25      81       6   10 # Student
```

### Negative Indices

By default, when specifying line numbers or slices, only positive values are supported as indices. With positive indices, the line numbers are matched for all the files together. It's like matching NR in `awk`.

```
NR=1{print}
NR>1{print}
```

But if negative indices are used or a negative step size is used in slices, the line numbers are matched for each file separately. The absolute value of the indices and step size will be used for comparison. The start and stop for slices must still be positive. Negative indices are like matching FNR in `awk`.

```
FNR=1{print}
FNR>1{print}
```

### Regular Expression

Pawky also works with regular expressions. To print the lines containing a small 'a', you can do

```python
awk['a'] = print
```

To match the regular expressions case-insensitively, set this at the beginning of your program.

```python
awk.IGNORECASE = True
```

To only match a certain field, use the field name as the first argument. To print the lines where the first field ends with 'a', do

```python
awk['$1',  # The first field, 1-indexed
    'a$'] = print  # Regular expression to match ending with 'a'

# Or
awk[0, 'a$'] = print  # If using int to access the fields, then it's 0-indexed
```

## Accessing Fields

Fields in the records can be accessed almost in the same way as in `awk`. To print the first field of each record, you can do one of the followings:

```python
awk.mid = lambda r: print(r['$1'])  # awk like $ syntax
awk.mid = lambda r: print(r['S1'])  # because S looks like $
awk.mid = lambda r: print(r['D1'])  # D for dollar ($)
awk.mid = lambda r: print(r['F1'])  # F for field

# These are also available as attributes
awk.mid = lambda r: print(r.S1)
awk.mid = lambda r: print(r.D1)
awk.mid = lambda r: print(r.F1)
```

You can access the last field of a record with `awk['$NF']`. In place of NF, you can use any other indexable attribute of the record. As in `awk`, in Pawky too, the fields are 1-indexed. Using `$0` will return the whole record. Using any out-of-bounds number will just return the empty string.

You can also use integers or slices for accessing the fields. When integers are used, 0-based indexing is used; there's no way to access the whole record. Out of bound indexes will also result in an error. To print the first field of each record, do

```python
awk.mid = lambda r: print(r[0])
```

## Setting Fields

The fields can be set in the same way they're accessed.

```python
record['$1'] = 'value'  # will set the first field and update the record
record['$0'] = 'value'  # will set the record and update the fields
record['$10'] = 'value'  # (assuming there are < 10 fields) will set the field, update the record and change NF.
record[0] = 'value'  # will set the first field and update the record, 0-indexed
```

Note that, unlike accessing, the dot-based syntax can't be used to set the fields. Similarly, changing NF will not drop excess fields.

## What's more?

Read the in-code documentation for more info.

## TODO

* Allow changing of NF to manipulate fields.
