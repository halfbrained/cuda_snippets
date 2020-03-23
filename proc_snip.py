import sys
import os
import string
from .proc_parse_std import parse_snippet_file
from .proc_parse_simple import parse_simple_snippet_line

CHARS_SNIP = string.ascii_letters + string.digits + '_.$>'
# char '>' is here to disable plugin work after "ul>li",
# to pass it to Emmet (which has lower event priority)

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


def get_snip_list_of_dicts(dir):
    files1 = []
    files2 = []
    for root, subdirs, files in os.walk(dir):
        for f in files:
            if f.endswith(SNIP_EXTENSION) or f.endswith(SNIP_EXTENSION2):
                files1.append(os.path.join(root, f))
            if f.endswith(SNIP_EXTENSION_ALT):
                files2.append(os.path.join(root, f))

    r1 = []
    for fn in files1:
        d = parse_snippet_file(open(fn, encoding='utf8').read())
        if d: 
            r1.append(d)
    
    r2 = []
    for fn in files2:
        for s in open(fn, encoding='utf8').read().splitlines():
            if s and s[0] not in ('#', ' '):
                d = parse_simple_snippet_line(s.strip())
                if d:
                    r2.append(d)
    
    return sorted(r1+r2, key=lambda d: d[SNIP_NAME])
