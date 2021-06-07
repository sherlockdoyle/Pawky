from pawky import *

awk = Pawky(autoparse=True)  # Parse possible fields to numbers
awk.mid = None  # Don't call the default function

mark_sum = [0] * 4


def begin():
    global mark_sum
    mark_sum = [0] * 4


awk['BEGIN'] = begin  # Called at the beginning


def header(r):
    print(r, 'Total')


awk[1] = header  # Called for the first line


def lines(r):
    s = r['$2'] + r['$3'] + r['$4'] + r['$5']  # Find the sum
    mark_sum[0] += r['$2']
    mark_sum[1] += r['$3']
    mark_sum[2] += r['$4']
    mark_sum[3] += r['$5']
    print(r, str(s).rjust(5))


awk[2:] = lines  # Called for each line except the first one


def end():
    print('Total'.ljust(8),
          str(mark_sum[0]).rjust(4),
          str(mark_sum[1]).rjust(7),
          str(mark_sum[2]).rjust(7),
          str(mark_sum[3]).rjust(4),
          str(sum(mark_sum)).rjust(5))


awk['END'] = end  # Called at the end

awk < 'marks.txt'
# print to file
# (awk > 'out.txt') < 'marks.txt'
