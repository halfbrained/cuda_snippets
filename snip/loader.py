import json
import os
import re

from cuda_snippets.snip.utils import load_json

from .snippet import Snippet, CT_SNIPPET, VS_SNIPPET
# from cuda_dev import dev


SNIP_EXTENSION = '.synw-snippet'
SNIP_EXTENSION2 = '.cuda-snippet'
SNIP_EXTENSION_ALT = '.cuda-snips'


def mkdir(*args):
    if not os.path.exists(args[0]):
        os.mkdir(*args)


def parse_vs_snippets_file(fp, lex):
    """Parser for Visual Studio/Code snippets file."""
    res = []
    with open(fp, mode='r', encoding='utf-8') as f:
        for k, v in load_json(f).items():
            try:
                t = v['body']
                if isinstance(t, str):
                    t = t.splitlines()
                res.append(Snippet(name=k, id=v['prefix'], text=t, lex=lex, t=VS_SNIPPET))
            except Exception:
                continue
    return res


def parse_snippet_file(fp):
    """Parser for standard CudaText snippet file"""
    with open(fp, mode='r', encoding='utf-8') as f:
        res = Snippet()
        res.type = CT_SNIPPET

        lines = f.read().splitlines()
        for index, line in enumerate(lines):
            if line == 'text=':
                res.text = [lines[i] for i in range(index + 1, len(lines))]
                break
            elif line.startswith('name='):
                res.name = line[5:]
            elif line.startswith('id='):
                _id = line[3:].strip(',')
                res.id = _id if isinstance(_id, list) else [_id]
            elif line.startswith('lex='):
                res.lex = line[4:].split(',')

        # check data correct
        if res.text and (res.id or res.name):
            return res
        else:
            return


def parse_simple_snippet_line(fp):
    """ Parse one-line snippet definition
            [word ][/L="My Lexer"] [/N="My Name"] text text
        If word is omitted then /N= is required.
        Quotes around lexer/name are required if value has blanks.
        Text part can has \t \n \r \\ to include chr(9) chr(10) chr(13) and '\' .
        Minimum line need to have two words or /N=name and text .
        Return
            {'id'  :'word',
             'name':'My Name',  # 'name':'word' if no /N= in line
             'lex' :'My Lexer', # 'lex' :''     if no /L= in line
             'text':['text text']
            }
    """
    def opt_val(line, opt, defv):
        optv = defv
        opt = opt if opt[0] == '/' else '/' + opt + '='
        mtch = re.match(opt + r'("[^"]+")', line)
        if mtch:
            optv = mtch.group(1)
            line = line.replace(opt + optv, '').lstrip()
            optv = optv.strip('"')
        else:
            mtch = re.match(opt + r'(\S+)', line)
            if mtch:
                optv = mtch.group(1)
                line = line.replace(opt + optv, '').lstrip()
        return optv, line

    res = []
    with open(fp, mode='r', encoding='utf-8') as f:
        for line in f.readlines():
            if not line or line[0] in ('#', ' '):
                continue

            if len(line.split()) < 2:
                continue

            key = line.split()[0] if line[:3] not in ('/N=', '/L=') else ''
            line = line[len(key):].lstrip()

            name = key
            lex = ''
            if line[:3] == '/N=':
                name, line = opt_val(line, 'N', defv=key)
            if line[:3] == '/L=':
                lex, line = opt_val(line, 'L', defv='')
            if line[:3] == '/N=':
                name, line = opt_val(line, 'N', defv=name)

            if not key and not name:
                continue

            body = line.lstrip()
            body = body.replace('\\\\', chr(0))
            body = body.replace('\\t', chr(9)).replace('\\n', chr(10)).replace('\\r', chr(13))
            body = body.replace(chr(0), '\\\\')

            if not body:
                continue
            res.append(Snippet(name=name, id=[key], lex=lex, text=body.splitlines(), t=CT_SNIPPET))
    return res


def load_snippets(basedir):
    vs_dir = os.path.join(basedir, 'snippets_vs')
    std_dir = os.path.join(basedir, 'snippets')
    mkdir(vs_dir)
    mkdir(std_dir)

    snips = {}
    glob = []  # ???? maybe not need global snippets
    # load std snips
    for root, subdirs, files in os.walk(std_dir):
        for f in files:
            fp = os.path.join(root, f)
            if f.endswith(SNIP_EXTENSION) or f.endswith(SNIP_EXTENSION2):
                res = parse_snippet_file(fp)
                if res:
                    if res.lex:
                        for lx in res.lex:
                            snips.setdefault(lx, []).append(res)
                    else:
                        glob.append(res)
            if f.endswith(SNIP_EXTENSION_ALT):
                for res in parse_simple_snippet_line(fp):
                    if res.lex:
                        snips.setdefault(res.lex, []).append(res)
                    else:
                        glob.append(res)

    # load vs snips
    for folder in os.scandir(vs_dir):
        if not os.path.isdir(os.path.join(vs_dir, folder)):
            continue

        config = os.path.join(vs_dir, folder, 'config.json')
        with open(config, 'r', encoding='utf-8') as _cfg:
            cfg = json.load(_cfg)
            files = cfg.get('files', {})
            for fn, lexs in files.items():
                fp = os.path.join(vs_dir, folder, 'snippets', fn)
                _snips = parse_vs_snippets_file(fp, lexs)
                for lx in lexs:
                    snips.setdefault(lx, []).extend(_snips)

    for lx in snips:
        snips[lx].sort()
    glob.sort()

    return snips, glob


if __name__ == '__main__':
    pass
