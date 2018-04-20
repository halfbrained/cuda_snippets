import os
import sys
import string
from .proc_parse_simple import *

CHARS_SNIP = string.ascii_letters + string.digits + '_.$'

SNIP_EXTENSION='.synw-snippet'
SNIP_EXTENSION2='.cuda-snippet'
SNIP_EXTENSION_ALT='.cuda-snips'

SNIP_NAME='name'
SNIP_ID='id'
SNIP_LEX='lex'
SNIP_TEXT='text'


def get_snip_name_from_editor(ed):
    #multi-carets? stop
    carets=ed.get_carets()
    if len(carets)!=1: return
    x, y, x1, y1 = carets[0]

    #selection? stop
    if y1>=0: return
    #check line index
    if y>=ed.get_line_count(): return

    line = ed.get_text_line(y)
    #caret after lineend? stop
    if x>len(line): return

    x0=x
    while (x>0) and (line[x-1] in CHARS_SNIP): x-=1
    return line[x:x0]


def parse_snip_content_to_dict(text):
    res={SNIP_NAME:'', SNIP_ID:'', SNIP_LEX:'', SNIP_TEXT:'' }
    lines=text.splitlines()

    for (index, line) in enumerate(lines):
        if line==SNIP_TEXT+'=':
            res[SNIP_TEXT] = [lines[i] for i in range(index+1, len(lines))]
            break

        for prefix in [SNIP_NAME, SNIP_ID, SNIP_LEX]:
            if line.startswith(prefix+'='):
                res[prefix] = line[len(prefix)+1:]

    return res


def get_snip_list_of_dicts(dir):
    res1 = []
    res2 = []
    for root, subdirs, files in os.walk(dir):
        for f in files:
            if f.endswith(SNIP_EXTENSION) or f.endswith(SNIP_EXTENSION2):
                res1.append(os.path.join(root, f))
            if f.endswith(SNIP_EXTENSION_ALT):
                res2.append(os.path.join(root, f))

    result1 = [parse_snip_content_to_dict(open(fn, encoding='utf8').read()) for fn in res1]
    
    result2 = []
    for fn in res2:
        for line in open(fn, encoding='utf8'):
            if not line.startswith('#') and not line.startswith(' '):
                result2 += [parse_simple_snippet_line(line)]
    
    return sorted(result1+result2, key=lambda d: d[SNIP_NAME])
