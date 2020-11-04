# from cuda_dev import dev
import os
import shutil
import webbrowser
from threading import Thread

import cudatext as ct
# dev.tstart()
from cuda_snippets import snip as sn
# dev.tstop()

DATA_DIR = ct.app_path(ct.APP_DIR_DATA)


class ThSnippetsLoader(Thread):
    def __init__(self):
        super().__init__()
        self.snippets = {}
        self.glob = []

    def run(self):
        self.snippets, self.glob = sn.load_snippets(DATA_DIR)


class Command:
    def __init__(self):
        self.vs_exts = None
        self.dlg_search = None
        self.last_snippet = None
        self.add_menu_items()

    def on_start(self, ed_self):
        self.th = ThSnippetsLoader()
        self.th.start()

    @property
    def lex_snippets(self):
        lexer = ct.ed.get_prop(ct.PROP_LEXER_CARET)
        return self.th.snippets.get(lexer, []) + self.th.glob

    def on_key(self, ed_self, code, state):
        if code != 9:
            return  # tab-key=9
        if state != '':
            return  # pressed any meta keys

        name = sn.get_word(ed_self)
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
        # need import here, not at the top, for faster load cudatext
        from cuda_snippets import vs
        from cuda_snippets.dlg_search import DlgSearch
        from cuda_snippets.dlg_lexers_compare import DlgLexersCompare

        if not self.dlg_search:
            self.dlg_search = DlgSearch()

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
        self.on_start(0)

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

    @staticmethod
    def vs_local_dirs():
        vs_dir = os.path.join(DATA_DIR, 'snippets_vs')
        if not os.path.isdir(vs_dir):
            return []

        rec = []
        for folder, data in sn.load_vs_snip_exts(vs_dir):
            name = data.get('display_name', '') + ' ' + data.get('version', '')
            url = ''
            lnk = data.get('links', '')
            if lnk:
                url = lnk.get('bugs', '') or lnk.get('repository', '')
                if url.endswith('.git'):
                    url = url[:-4]
            if name:
                rec += [{'name': name, 'url': url, 'dir': folder.path}]

        rec.sort(key=lambda r: r['name'])
        return rec

    def issues_vs(self):
        rec = self.vs_local_dirs()
        if not rec:
            ct.msg_status('No VSCode snippets found')
            return

        mnu = [s['name']+'\t'+s['url'] for s in rec]
        res = ct.dlg_menu(ct.MENU_LIST_ALT, mnu, caption='Visit page of snippets')
        if res is None:
            return

        url = rec[res]['url']
        if not url:
            ct.msg_status("No URL found")
            return
        ct.msg_status('Opened: '+url)
        webbrowser.open_new_tab(url)

    def remove_vs_snip(self):
        rec = self.vs_local_dirs()

        if not rec:
            ct.msg_status('No VSCode snippets found')
            return

        mnu = [s['name'] for s in rec]
        res = ct.dlg_menu(ct.MENU_LIST, mnu, caption='Remove snippets')
        if res is None:
            return

        vs_snip_dir = rec[res]['dir']
        shutil.rmtree(vs_snip_dir)
        ct.msg_status('Snippets folder removed; restart CudaText to forget about it')
