
#example of chars: "()[]{}"
def find_matching_bracket(line, from_x, chars):
    if not from_x in range(len(line)): return
    ch = line[from_x]
    pos = chars.find(ch)
    if pos<0: return
    
    if pos%2==0:
        ch_end = chars[pos+1]
        down = True
    else:
        ch_end = chars[pos-1]
        down = False 

    to_x = from_x
    cnt = 0
    
    while True:
        for pos in (range(to_x, len(line)) if down else
                    range(to_x, -1, -1)):
            ch_now = line[pos]
            if ch_now==ch:
                cnt+=1
            elif ch_now==ch_end:
                cnt-=1
                if cnt==0:
                    return pos
     
