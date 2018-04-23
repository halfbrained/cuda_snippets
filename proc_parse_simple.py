import re

def parse_simple_snippet_line(line):
    """ Parse one-line snippet definition
            word [/L="My Lexer"] [/N="My Name"] text text
        Quotes around lexer/name are required if value has blanks.
        Text part can has \t \n \r \\ to include chr(9) chr(10) chr(13) and '\' .
        Min line need to have two words.
        Return
            {'id'  :'word',
             'name':'My Name',  # 'name':'word' if no /N= in line
             'lex' :'My Lexer', # 'lex' :''     if no /L= in line
             'text':['text text']
            }
    """
    key     = line.split()[0]
    line    = line[len(key):].lstrip()

    def opt_val(line, opt, defv):
        optv    = defv
        opt     = opt if opt[0]=='/' else '/'+opt+'='
        mtch= re.match(opt+r'("[^"]+")', line)
        if mtch:
            optv    = mtch.group(1)
            line    = line.replace(opt+optv, '').lstrip()
            optv    = optv.strip('"')
        else:
            mtch= re.match(opt+r'(\S+)', line)
            if mtch:
                optv    = mtch.group(1)
                line    = line.replace(opt+optv, '').lstrip()
        return optv,line

    name    = key
    lex     = ''
    if line[:3]=='/N=':
        name,line   = opt_val(line, 'N', defv=key)
    if line[:3]=='/L=':
        lex,line    = opt_val(line, 'L', defv='')
    if line[:3]=='/N=':
        name,line   = opt_val(line, 'N', defv=name)

    body    = line.lstrip()
    body    = body.replace('\\\\', chr(0))
    body    = body.replace('\\t', chr(9)).replace('\\n', chr(10)).replace('\\r', chr(13))
    body    = body.replace(chr(0), '\\')
    return {'id':key, 'name':name, 'lex':lex, 'text':body.splitlines() }
