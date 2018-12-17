import os
from datetime import datetime
import cudatext as app

MACRO_SEL = '${sel}'
MACRO_CLIP = '${cp}'
MACRO_FILENAME = '${fname}'
MACRO_DATE = '${date:' #no }
MACRO_CMT_START = '${cmt_start}'
MACRO_CMT_END = '${cmt_end}'
MACRO_CMT_LINE = '${cmt_line}'

def snip_replace_macros_in_lines(items, text_sel, text_clip, text_filename):
    for index in range(len(items)):
        s = items[index]
        while True:
            n = s.find(MACRO_SEL)
            if n<0: break
            s = s[:n]+text_sel+s[n+len(MACRO_SEL):]

        while True:
            n = s.find(MACRO_CLIP)
            if n<0: break
            s = s[:n]+text_clip+s[n+len(MACRO_CLIP):]

        while True:
            n = s.find(MACRO_FILENAME)
            if n<0: break
            s = s[:n]+text_filename+s[n+len(MACRO_FILENAME):]

        cmt_start = ''
        cmt_end = ''
        cmt_line = ''
        lexer = app.ed.get_prop(app.PROP_LEXER_FILE)
        prop = app.lexer_proc(app.LEXER_GET_PROP, lexer)
        if prop:
            prop_str = prop.get('c_str')
            prop_line = prop.get('c_line')
            cmt_start = prop_str[0] if prop_str else ''
            cmt_end = prop_str[1] if prop_str else ''
            cmt_line = prop_line if prop_line else ''

        while True:
            n = s.find(MACRO_CMT_START)
            if n<0: break
            s = s[:n]+cmt_start+s[n+len(MACRO_CMT_START):]

        while True:
            n = s.find(MACRO_CMT_END)
            if n<0: break
            s = s[:n]+cmt_end+s[n+len(MACRO_CMT_END):]

        while True:
            n = s.find(MACRO_CMT_LINE)
            if n<0: break
            s = s[:n]+cmt_line+s[n+len(MACRO_CMT_LINE):]

        while True:
            n = s.find(MACRO_DATE)
            if n<0: break
            text_date = s[n:]
            nn = text_date.find('}')
            if nn<0: break
            text_date = text_date[len(MACRO_DATE):nn]
            text_date = datetime.now().strftime(text_date)
            s = s[:n]+text_date+s[n+nn+1:]

        if items[index]!=s:
            items[index] = s
