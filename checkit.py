import os
import sys

Line = [0]

def CheckIt(file):
    count = 0
    with open(file, 'r') as f:
        while True:
            line = f.readline()
            if not line: break
            count += 1
            if line.startswith('v'):          continue
            if line.startswith('Parsing'):    continue
            if line.startswith('-----'):      continue
            if line.startswith('Processing'):
                Line[-1] = 0
                continue
            # Line should start with a line number
            try:
                number, rest = line.split(':', maxsplit=1)
                number = int(number)
                # Number should be one more than last line number
                if number == Line[-1] + 1: Line[-1] += 1
                # Look for special cases where line number does not change
                elif number == Line[-1]:
                    if not rest.split()[0] in ['ConvertedCondition', 'ConditionalLevel', 'Limiting', 'SKIPPED']:
                        if not rest.startswith('[') and rest.rstrip().endswith(']'):
                            print(f'Unexpected line numbering discontinuity found at line {count}')
                # Look for special case where line number can change dramatically
                elif not 'Previously' in rest and not 'Returning' in rest:
                    print(f'Unexpected line numbering discontinuity found at line {count}')
                # Look for include
                if 'Including' in rest: Line.append(0)
                # Look for return
                elif 'Returning' in rest: Line.pop()
            except ValueError:
                if not line.strip(): continue       # Allow blank lines
                if "RESULTS:" in line: break
                print(f'Unexpected line format found at line {count}')

CheckIt("u54")