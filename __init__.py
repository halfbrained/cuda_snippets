import os
import json
import webbrowser
import cudatext as ct
from cuda_snippets.dlg_lexers_compare import DlgLexersCompare
from cuda_snippets.dlg_search import DlgSearch
from cuda_snippets.snip import load_snippets, get_word
from cuda_snippets import vs


class Command:
    def __init__(self):
        self.vs_exts = None
        self.dlg_search = DlgSearch()
        self.last_snippet = None
        self.do_load_snippets()
        self.add_menu_items()

    def do_load_snippets(self):
        base_dir = ct.app_path(ct.APP_DIR_DATA)
        self.snippets, self.glob = load_snippets(base_dir)

    @property
    def lex_snippets(self):
        lexer = ct.ed.get_prop(ct.PROP_LEXER_CARET)
        return self.snippets.get(lexer, []) + self.glob

    def on_key(self, ed_self, code, state):
        if code != 9:
            return  # tab-key=9
        if state != '':
            return  # pressed any meta keys

        name = get_word(ed_self)
        if not name:
            return

        items = [i for i in self.lex_snippets if name in i.id]  # leave snips for name

        if not items:
            return

        # delete name in text
        carets = ed_self.get_carets()
        x0, y0, x1, y1 = carets[0]
        ed_self.delete(x0 - len(name), y0, x0, y0)
        ed_self.set_caret(x0 - len(name), y0)

        if len(items) > 1:
            self.menu_dlg(items)
            return False  # block tab-key

        # insert
        items[0].insert(ed_self)
        return False  # block tab-key

    def menu_dlg(self, items):
        names = [str(item) for item in items]
        if not names:
            ct.msg_status('No snippets for current lexer')
            return
        try:
            focused = items.index(self.last_snippet)
        except ValueError:
            focused = 0
        i = ct.dlg_menu(ct.MENU_LIST, names, focused=focused, caption='Snippets')
        if i is None:
            return
        self.last_snippet = items[i]
        self.last_snippet.insert(ct.ed)

    def do_menu(self):
        self.menu_dlg(self.lex_snippets)

    def install_vs_snip(self):
        # load vs snippets list
        if not self.vs_exts:
            ct.msg_status("Loading VS Snippets list. Please wait...", process_messages=True)
            self.vs_exts = vs.get_all_snip_exts()
            if not self.vs_exts:
                print("Can't download VS Snippets. Try again later...")
                return
        # show dlg
        self.dlg_search.set_vs_exts(self.vs_exts)
        data = self.dlg_search.show()
        if not data:
            return
        DlgLexersCompare(data).show()
        self.do_load_snippets()

    @staticmethod
    def del_markers():
        ct.ed.markers(ct.MARKERS_DELETE_ALL)

    def add_menu_items(self):
        if 'cuda_snippets' in [i['tag'] for i in ct.menu_proc('text', ct.MENU_ENUM)]:
            return

        ct.menu_proc("text", ct.MENU_ADD,
                     caption='-',
                     tag='cuda_snippets'
                     )
        ct.menu_proc("text", ct.MENU_ADD,
                     caption='Delete snippet markers',
                     command=self.del_markers,
                     # hotkey=hotkey,
                     tag='cuda_snippets'
                     )

    def vs_local_dirs(self):

        dir = os.path.join(ct.app_path(ct.APP_DIR_DATA), 'snippets_vs')
        if not os.path.isdir(dir):
            return []

        rec = []
        obj = os.scandir(dir)
        for item in obj:
            if item.is_dir():
                fn = os.path.join(item.path, 'config.json')
                if os.path.isfile(fn):
                    with open(fn, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        name = data.get('display_name', '')
                        data = data.get('links', '')
                        if data:
                            url = data.get('bugs', '')
                            if not url:
                                url = data.get('repository', '')
                                if url.endswith('.git'):
                                    url = s[:-4]
                        if name and url:
                            rec += [(name, url, item.path)]

        rec = sorted(rec, key=lambda r: r[0])
        return rec


    def issues_vs(self):

        rec = self.vs_local_dirs()
        if not rec:
            ct.msg_status('No VSCode snippets found')
            return

        mnu = [s[0] for s in rec]
        res = ct.dlg_menu(ct.MENU_LIST, mnu, caption='Visit page of snippets')
        if res is None:
            return

        url = rec[res][1]
        webbrowser.open_new_tab(url)
        ct.msg_status('URL opened: '+url)


    def remove_vs_snip(self):

        rec = self.vs_local_dirs()
        if not rec:
            ct.msg_status('No VSCode snippets found')
            return

        mnu = [s[0] for s in rec]
        res = ct.dlg_menu(ct.MENU_LIST, mnu, caption='Delete snippets')
        if res is None:
            return

        dir = rec[res][2]
        import shutil
        shutil.rmtree(dir)
        ct.msg_status('Removed snippets; restart CudaText to forget about this package')
     
