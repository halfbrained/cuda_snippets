import os
import cudatext as ct
import cudatext_cmd
from .proc_snip_macros import *
from .proc_brackets import *

SNIP_MAX_POINTS = 40


def insert_snip_into_editor(ed, snip_lines):
    items = list(snip_lines) #copy list value
    if not items: return
    
    carets = ed.get_carets()
    if len(carets)!=1: return
    x0, y0, x1, y1 = carets[0]

    tab_spaces = ed.get_prop(ct.PROP_TAB_SPACES)
    tab_size = ed.get_prop(ct.PROP_TAB_SIZE)

    text_sel = ed.get_text_sel()
    text_clip = ct.app_proc(ct.PROC_GET_CLIP, '')
    text_filename = os.path.basename(ed.get_filename())
    
    #strip file-ext
    n = text_filename.rfind('.')
    if n>=0:
        text_filename = text_filename[:n]

    #delete selection
    if text_sel:
        #sort coords (x0/y0 is left)
        if (y1>y0) or ((y1==y0) and (x1>=x0)):
            pass
        else:
            x0, y0, x1, y1 = x1, y1, x0, y0 
        ed.delete(x0, y0, x1, y1)
        ed.set_caret(x0, y0) 
    
    #apply indent to lines from second
    x_col, y_col = ed.convert(ct.CONVERT_CHAR_TO_COL, x0, y0)
    indent = ' '*x_col
    
    if not tab_spaces:
        indent = indent.replace(' '*tab_size, '\t')
    
    for i in range(1, len(items)):
        items[i] = indent+items[i]

    #replace tab-chars
    if tab_spaces:
        indent = ' '*tab_size
        items = [item.replace('\t', indent) for item in items]

    #parse macros
    snip_replace_macros_in_lines(items, text_sel, text_clip, text_filename)
    
    #parse tabstops ${0}, ${0:text}
    stops = []
    for index in range(len(items)):
        s = items[index]
        while True:
            digit = 0
            deftext = ''
            
            n = s.find('${')
            if n<0: break
            
            n_end = find_matching_bracket(s, n+1, '{}')
            if n_end is None:
                print('Incorrect brackets ${..}') 
                return
            
            text_in = s[n+2:n_end]
            nested = False
            nested_shift = 0
            
            #find nested ins-point
            nn = text_in.find('${')
            if nn>=0:
                n = n+2+nn
                n_end = find_matching_bracket(s, n+1, '{}')
                if n_end is None:
                    print('Incorrect nested brackets ${..}') 
                    return
                
                text_in = s[n+2:n_end]
                nested = True
                
            try:
                if ':' in text_in:
                    _separ = text_in.split(':')
                    digit = int(_separ[0])
                    deftext = _separ[1]
                else:
                    digit = int(text_in)
            except:
                print('Incorrect ins-point index: '+s)
                return

            if nested:
                nested_shift = len(str(digit))+3
            
            #delete spec-chars                    
            s = s[:n]+deftext+s[n_end+1:]
            items[index] = s
            
            stops += [(digit, deftext, index, n-nested_shift)]
    #print('tabstops', stops)        
    
    #insert    
    ed.insert(x0, y0, '\n'.join(items))
    
    #place markers
    mark_placed = False
    ed.markers(ct.MARKERS_DELETE_ALL)

    #list: 0,max,max-1,...,3,2,1
    digit_list = [0] + list(range(SNIP_MAX_POINTS, 0, -1))
    
    for digit in digit_list: #order of stops: 1..max, 0
        for stop in reversed(stops): #reversed is for Emmet: many stops with ${0}
            if stop[0]==digit:
                pos_x = stop[3]
                pos_y = stop[2]
                if pos_y==0:
                    pos_x += x0
                pos_y += y0
                deftext = stop[1]
                ed.markers(ct.MARKERS_ADD, pos_x, pos_y, digit, len(deftext))
                mark_placed = True
    
    if mark_placed:
        ed.set_prop(ct.PROP_TAB_COLLECT_MARKERS, '1')
        ed.cmd(cudatext_cmd.cmd_Markers_GotoLastAndDelete)
