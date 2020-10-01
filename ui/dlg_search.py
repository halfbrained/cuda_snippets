import time
import threading

import cudatext as ct
from cuda_snippets.vs import vs
from cuda_snippets.timer import Timer

# from cuda_dev import dev


lock = threading.Lock()


class Th(threading.Thread):
    """Thread class with a stop() method. The thread itself has to check
    regularly for the stopped() condition."""

    def __init__(self,  *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._stop_event = threading.Event()

    def stop(self, timeout=None):
        self._stop_event.set()

    def is_stopped(self):
        return self._stop_event.is_set()


class DlgSearch:
    def __init__(self):
        self.data = None
        self.th_get_exts = None
        self._last = []
        self.exts = []
        self.need_update_lst = False
        self.t_update_lst = Timer(
            callback=self.update_lst,
            interval=1000
        )

        w, h = 600, 400
        self.h = ct.dlg_proc(0, ct.DLG_CREATE)
        ct.dlg_proc(self.h, ct.DLG_PROP_SET,
                    prop={'cap': 'Search snippets',
                          'w': w,
                          'h': h,
                          'resize': False,
                          "keypreview": True,
                          'on_key_down': self.press_key,
                          'on_hide': lambda *args, **kwargs: self.t_update_lst.stop(),
                          }
                    )

        self.g1 = ct.dlg_proc(self.h, ct.DLG_CTL_ADD, 'panel')
        ct.dlg_proc(self.h, ct.DLG_CTL_PROP_SET, index=self.g1,
                    prop={
                        'name': 'g1',
                        'h': 30,
                        'a_l': ('', '['),
                        'a_r': ('', ']'),
                        'a_t': ('', '['),
                         }
                    )

        self.g2 = ct.dlg_proc(self.h, ct.DLG_CTL_ADD, 'panel')
        ct.dlg_proc(self.h, ct.DLG_CTL_PROP_SET, index=self.g2,
                    prop={
                        'name': 'g2',
                        'a_l': ('', '['),
                        'a_r': ('', ']'),
                        'a_t': ('g1', ']'),
                        'a_b': ('', ']'),
                         }
                    )

        self.ls = ct.dlg_proc(self.h, ct.DLG_CTL_ADD, 'listbox')
        ct.dlg_proc(self.h, ct.DLG_CTL_PROP_SET, index=self.ls,
                    prop={
                        'name': 'ls',
                        'p': 'g2',
                        'align': ct.ALIGN_CLIENT,
                        'sp_l': 5,
                        'sp_r': 5,
                        'sp_t': 5,
                        'on_click_dbl': self.install,
                        'on_click': self.load_description,
                         }
                    )

        self.sp = ct.dlg_proc(self.h, ct.DLG_CTL_ADD, 'splitter')
        ct.dlg_proc(self.h, ct.DLG_CTL_PROP_SET, index=self.sp,
                    prop={
                        'name': 'sp',
                        'p': 'g2',
                        'align': ct.ALIGN_BOTTOM,
                         }
                    )

        self.memo = ct.dlg_proc(self.h, ct.DLG_CTL_ADD, 'memo')
        ct.dlg_proc(self.h, ct.DLG_CTL_PROP_SET, index=self.memo,
                    prop={
                        'name': 'ls',
                        'h': 60,
                        'ex0': True,
                        'ex1': True,
                        'p': 'g2',
                        'align': ct.ALIGN_BOTTOM,
                        'sp_l': 5,
                        'sp_r': 5,
                        'sp_b': 5,
                        'tab_stop': False,
                         }
                    )

        self.b = ct.dlg_proc(self.h, ct.DLG_CTL_ADD, 'button')
        ct.dlg_proc(self.h, ct.DLG_CTL_PROP_SET, index=self.b,
                    prop={
                        'name': 'b',
                        'w': 60,
                        'a_l': None,
                        'a_r': ('g1', ']'),
                        'a_t': ('g1', '['),
                        'sp_a': 5,
                        'p': 'g1',
                        'cap': 'Search',
                        'on_change': self.search,
                        'tab_stop': False,
                         }
                    )

        self.edit = ct.dlg_proc(self.h, ct.DLG_CTL_ADD, 'edit')
        ct.dlg_proc(self.h, ct.DLG_CTL_PROP_SET, index=self.edit,
                    prop={
                        'name': 'edit',
                        'a_l': ('g1', '['),
                        'a_r': ('b', '['),
                        'a_t': ('g1', '['),
                        'sp_a': 5,
                        'p': 'g1',
                        'tab_order': 0,
                         }
                    )

    def show(self):
        ct.dlg_proc(self.h, ct.DLG_SHOW_MODAL)
        ct.dlg_proc(self.h, ct.DLG_FREE)
        return self.data

    def press_key(self, id_dlg, id_ctl, data='', info=''):
        # dev(id_ctl)
        if id_ctl == 13:
            if self.is_focused(self.edit):
                self.search()
            elif self.is_focused(self.ls) and self.item_index >= 0:
                self.install()
        elif id_ctl == 40 and not self.is_focused(self.ls):
            self.set_focus(self.ls)
            self.item_index += 1
            self.load_description()
        elif id_ctl == 38 and self.item_index == 0:
            self.set_focus(self.edit)

    def is_focused(self, ctl):
        return ct.dlg_proc(self.h, ct.DLG_CTL_PROP_GET, index=ctl)['focused']

    def set_focus(self, ctl):
        ct.dlg_proc(self.h, ct.DLG_CTL_FOCUS, index=ctl)

    @property
    def text(self):
        return ct.dlg_proc(self.h, ct.DLG_CTL_PROP_GET, index=self.edit)['val']

    @property
    def item_index(self):
        return int(ct.dlg_proc(self.h, ct.DLG_CTL_PROP_GET, index=self.ls)['val'])

    @item_index.setter
    def item_index(self, v):
        ct.dlg_proc(self.h, ct.DLG_CTL_PROP_SET, index=self.ls, prop={'val': v})

    def set_items(self, items):
        items = '\t'.join(items)
        ct.dlg_proc(self.h, ct.DLG_CTL_PROP_SET, index=self.ls, prop={'items': items})

    def load_description(self, *args, **kwargs):
        descr = self.exts[self.item_index].description
        ct.dlg_proc(self.h, ct.DLG_CTL_PROP_SET, index=self.memo, prop={'val': descr})

    def install(self, *args, **kwargs):
        self.th_get_exts.stop()
        ext = self.exts[self.item_index]

        ct.dlg_proc(self.h, ct.DLG_HIDE)
        ct.msg_status(' '.join(["Installing: ", ext.display_name, ext.version]), process_messages=True)

        res = vs.download(ext.url)
        if not res:
            ct.msg_box(' '.join(["Can't download: ", ext.display_name, ext.version]), ct.MB_OK+ct.MB_OK)
            return
        self.data = vs.prepare_vs_snips(res)
        # dev(self.data)

    def get_exts(self, name):
        i = 1
        while True:
            ext = vs.get_extensions(name, page_size=30, page_number=i)
            if len(ext) == 0:
                return
            i += 1
            with lock:
                self.exts.extend(ext)
            self.need_update_lst = True

    def search(self, *args, **kwargs):
        """Find extensions."""
        if self.th_get_exts and not self.th_get_exts.is_stopped():
            self.th_get_exts.stop()

        self.exts = []
        name = self.text
        if not name:
            return
        self.th_get_exts = Th(target=self.get_exts, args=(name,))
        self.th_get_exts.start()
        self.t_update_lst.start()

    def update_lst(self, *args):
        try:
            if not self.need_update_lst:
                return

            self.need_update_lst = False
            i = self.item_index

            with lock:
                need_save_pos = True if i >= 0 and self._last[i] == self.exts[i] else False
                self._last = self.exts.copy()

            # update items of lst
            items = [' '.join([e.display_name, e.version]) for e in self._last]
            self.set_items(items)

            # save position
            if need_save_pos:
                ct.dlg_proc(self.h, ct.DLG_CTL_PROP_SET, index=self.ls, prop={'val': i})

        except Exception as ex:
            print(ex)
            self.t_update_lst.stop()


if __name__ == '__main__':
    d = DlgSearch().show()
