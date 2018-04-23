
SNIP_NAME='name'
SNIP_ID='id'
SNIP_LEX='lex'
SNIP_TEXT='text'

def parse_snippet_file(text):
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
