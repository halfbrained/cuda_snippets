import os
import json

#DBG
import datetime

import cudatext as ct
from cuda_snippets import vs

from cudax_lib import get_translation
_   = get_translation(__file__)  # I18N


DATA_DIR = ct.app_path(ct.APP_DIR_DATA)
MAIN_SNIP_DIR = os.path.join(DATA_DIR, 'snippets_ct')
SNIP_DIRS = [
    MAIN_SNIP_DIR,
    os.path.join(DATA_DIR, 'snippets_vs'),
]

TYPE_PKG = 101
TYPE_GROUP = 102 

#TODO check for proper filenames for filesystem
#TODO handle same name packages

def log(s):
    if True:
        now = datetime.datetime.now()
        with open('/media/q/cu.log', 'a', encoding='utf-8') as f:
            f.write(now.strftime("%H:%M:%S ") + s + '\n')

#class DlgLexersCompare:
class DlgSnipMan:
    def __init__(self, select_lex=None):
        self.select_lex = select_lex # select first group with this lexer, mark in menus
        
        self.packages = self._load_packages()
        self._sort_pkgs()
        self.file_snippets = {} # tuple (<pkg path>,<group>) : snippet dict
        self.modified = [] # (type, name)

        w, h = 500, 400
        self.h = ct.dlg_proc(0, ct.DLG_CREATE)
        ct.dlg_proc(self.h, ct.DLG_PROP_SET, 
                    prop={'cap': _('Add snippet'),
                        'w': w,
                        'h': h,
                        'resize': True,
                        #"keypreview": True,
                        }
                    )
                    
 
        ### Controls
        
        # Cancel | Ok
        self.n_ok = ct.dlg_proc(self.h, ct.DLG_CTL_ADD, 'button')
        ct.dlg_proc(self.h, ct.DLG_CTL_PROP_SET, index=self.n_ok,
                    prop={
                        'name': 'ok',
                        'a_l': None,
                        'a_t': None,
                        'a_r': ('', ']'),
                        'a_b': ('',']'),
                        'w': 30,
                        #'h_max': 30,
                        'w_min': 60,
                        'sp_a': 6,
                        #'sp_t': 6,
                        'autosize': True,
                        'cap': 'OK',  
                        }
                    )
                    
        self.n_cancel = ct.dlg_proc(self.h, ct.DLG_CTL_ADD, 'button')
        ct.dlg_proc(self.h, ct.DLG_CTL_PROP_SET, index=self.n_cancel,
                    prop={
                        'name': 'cancel',
                        'a_l': None,
                        'a_t': ('ok', '-'),
                        'a_r': ('ok', '['),
                        'a_b': ('',']'),
                        'w': 30,
                        #'h_max': 30,
                        'w_min': 60,
                        'sp_a': 6,
                        #'sp_t': 6,
                        'autosize': True,
                        'cap': 'Cancel',  
                        }
                    )
                    
        # Main
        n = ct.dlg_proc(self.h, ct.DLG_CTL_ADD, 'group')
        ct.dlg_proc(self.h, ct.DLG_CTL_PROP_SET, index=n,
                    prop={
                        'name': 'parent',
                        'a_l': ('','['),
                        'a_t': ('','['),
                        'a_r': ('',']'),
                        'a_b': ('cancel','['),
                        #'align': ct.ALIGN_CLIENT,
                        'sp_a': 3,
                        #'sp_b': 40,
                        }
                    )
                    
                    
        n = ct.dlg_proc(self.h, ct.DLG_CTL_ADD, 'label')
        ct.dlg_proc(self.h, ct.DLG_CTL_PROP_SET, index=n,
                    prop={
                        'name': 'pkg_label',
                        'p': 'parent',
                        'a_l': ('', '['),
                        'a_t': ('','['),
                        'w_min': 80,
                        'sp_a': 3,
                        'sp_t': 6,
                        'cap': 'Package: ',  
                        }
                    )
                    
        self.n_package = ct.dlg_proc(self.h, ct.DLG_CTL_ADD, 'combo_ro')
        ct.dlg_proc(self.h, ct.DLG_CTL_PROP_SET, index=self.n_package,
                    prop={
                        'name': 'packages',
                        'p': 'parent',
                        'a_l': ('pkg_label', ']'),
                        'a_t': ('pkg_label','-'),
                        'a_r': ('',']'),
                        'sp_a': 3,
                        'act': True,
                        'on_change': self._on_package_selected,
                        #'on_change': lambda *args, **vargs: print(f' --sel'),
                        #'on_change': 'module=cuda_snippets;cmd=_del;',
                        }
                    )
                    
                    
        n = ct.dlg_proc(self.h, ct.DLG_CTL_ADD, 'label')
        ct.dlg_proc(self.h, ct.DLG_CTL_PROP_SET, index=n,
                    prop={
                        'name': 'grp_label',
                        'p': 'parent',
                        'a_l': ('', '['),
                        'a_t': ('packages',']'),
                        'w_min': 80,
                        'sp_a': 3,
                        'sp_t': 6,
                        'cap': 'Group: ',  
                        }
                    )
                    
        self.n_groups = ct.dlg_proc(self.h, ct.DLG_CTL_ADD, 'combo_ro')
        ct.dlg_proc(self.h, ct.DLG_CTL_PROP_SET, index=self.n_groups,
                    prop={
                        'name': 'groups',
                        'p': 'parent',
                        'a_l': ('grp_label', ']'),
                        'a_t': ('grp_label','-'),
                        'a_r': ('',']'),
                        'sp_a': 3,
                        'act': True,
                        'on_change': self._on_group_selected,
                        'en': False,
                        }
                    )
                    
                    
        n = ct.dlg_proc(self.h, ct.DLG_CTL_ADD, 'label')
        ct.dlg_proc(self.h, ct.DLG_CTL_PROP_SET, index=n,
                    prop={
                        'name': 'lex_label',
                        'p': 'parent',
                        'a_l': ('', '['),
                        'a_t': ('groups',']'),
                        'w_min': 80,
                        'sp_a': 3,
                        'sp_t': 6,
                        'sp_l': 30,
                        'cap': 'Group\'s lexers: ',  
                        }
                    )
                    
        self.n_lex = ct.dlg_proc(self.h, ct.DLG_CTL_ADD, 'edit')
        ct.dlg_proc(self.h, ct.DLG_CTL_PROP_SET, index=self.n_lex,
                    prop={
                        'name': 'lexers',
                        'p': 'parent',
                        'a_l': ('lex_label', ']'),
                        'a_t': ('lex_label','-'),
                        'a_r': ('',']'),
                        'sp_a': 3,
                        'en': False,
                        }
                    )
                    
                    
        n = ct.dlg_proc(self.h, ct.DLG_CTL_ADD, 'label')
        ct.dlg_proc(self.h, ct.DLG_CTL_PROP_SET, index=n,
                    prop={
                        'name': 'snip_label',
                        'p': 'parent',
                        'a_l': ('', '['),
                        'a_t': ('lexers',']'),
                        'w_min': 80,
                        'sp_a': 3,
                        'sp_t': 6,
                        'cap': 'Snippet: ',  
                        }
                    )
                    
        self.n_snippets = ct.dlg_proc(self.h, ct.DLG_CTL_ADD, 'combo_ro')
        ct.dlg_proc(self.h, ct.DLG_CTL_PROP_SET, index=self.n_snippets,
                    prop={
                        'name': 'snippets',
                        'p': 'parent',
                        'a_l': ('snip_label', ']'),
                        'a_t': ('snip_label','-'),
                        'a_r': ('',']'),
                        'sp_a': 3,
                        'on_change': self._on_snippet_selected,
                        'act': True,
                        'en': False,
                        'cap': 'lol?',
                        'hint': 'crap!',
                        }
                    )
                    
                    
        n = ct.dlg_proc(self.h, ct.DLG_CTL_ADD, 'label')
        ct.dlg_proc(self.h, ct.DLG_CTL_PROP_SET, index=n,
                    prop={
                        'name': 'alias_label',
                        'p': 'parent',
                        'a_l': ('', '['),
                        'a_t': ('snippets',']'),
                        'w_min': 80,
                        'sp_a': 3,
                        'sp_t': 6,
                        'sp_l': 30,
                        'cap': 'Snippet\'s alias: ',  
                        }
                    )
                    
        self.n_alias = ct.dlg_proc(self.h, ct.DLG_CTL_ADD, 'edit')
        ct.dlg_proc(self.h, ct.DLG_CTL_PROP_SET, index=self.n_alias,
                    prop={
                        'name': 'alias',
                        'p': 'parent',
                        'a_l': ('alias_label', ']'),
                        'a_t': ('alias_label','-'),
                        'a_r': ('',']'),
                        'sp_a': 3,
                        'en': False,
                        }
                    )
                    
                    
        self.n_edit = ct.dlg_proc(self.h, ct.DLG_CTL_ADD, 'editor')
        ct.dlg_proc(self.h, ct.DLG_CTL_PROP_SET, index=self.n_edit,
                    prop={
                        'name': 'editor',
                        'p': 'parent',
                        'a_l': ('', '['),
                        'a_t': ('alias',']'),
                        'a_r': ('',']'),
                        'a_b': ('',']'),
                        'sp_a': 3,
                        'sp_t': 6,
                        'en': False
                        }
                    )
        h_ed = ct.dlg_proc(self.h, ct.DLG_CTL_HANDLE, index=self.n_edit)
        self.ed = ct.Editor(h_ed)
        self.ed.set_prop(ct.PROP_UNPRINTED_SHOW, True)
        self.ed.set_prop(ct.PROP_UNPRINTED_SPACES, True)
        self.ed.set_prop(ct.PROP_TAB_SPACES, False)
                    
        self._fill_forms(init_lex_sel=self.select_lex) # select first group with specified lexer if any
        
    def _fill_forms(self, init_lex_sel=None, sel_pkg_path=None, sel_group=None, sel_snip=None):
        # fill packages
        items = [pkg.get('name') for pkg in self.packages]
        self.pkg_items = [*items] #TODO use
        
        # select first group with <lexer>
        if init_lex_sel:
            found = False
            for pkg in self.packages:
                for fn,lexs in pkg.get('files', {}).items():
                    if init_lex_sel in lexs:
                        if not found:
                            found = True
                            sel_pkg_path = pkg['path']
                            sel_group = fn
                        break
                if found:
                    break
        # select package with specified lexer
        if self.select_lex:
            for i,pkg in enumerate(self.packages):
                for fn,lexs in pkg.get('files', {}).items():
                    if self.select_lex in lexs:
                        items[i] += f'   (*{self.select_lex})'
                        break
        
        items.insert(0, '[New...]')
        items = '\t'.join(items)
        props = {'items': items,}
        
        sel_pkg_ind = -1
        sel_pkg = None
        # select package, if specified
        if sel_pkg_path: # select new package:
            # fine selected package
            for i,pkg in enumerate(self.packages):
                if pkg['path'] == sel_pkg_path:
                    sel_pkg_ind = i
                    sel_pkg = pkg
                    props['val'] = 1 + sel_pkg_ind
                    break
                    
        ct.dlg_proc(self.h, ct.DLG_CTL_PROP_SET, index=self.n_package, prop=props)
        if sel_pkg_ind >= 0:
            self._on_package_selected(-1,-1)

        # select group
        if sel_pkg != None  and sel_group  and sel_group in sel_pkg.get('files', {}):
            sel_group_ind = 1 + self._groups_items.index(sel_group)
            ct.dlg_proc(self.h, ct.DLG_CTL_PROP_SET, index=self.n_groups, prop={'val': sel_group_ind})
            self._on_group_selected(-1,-1)
            
            # select snippet
            if sel_snip != None  and sel_snip in self.snip_items:
                sel_snip_ind = 1 + self.snip_items.index(sel_snip)
                ct.dlg_proc(self.h, ct.DLG_CTL_PROP_SET, index=self.n_snippets, prop={'val': sel_snip_ind})
                self._on_snippet_selected(-1,-1)
            

    def show_add_snip(self):
        ct.dlg_proc(self.h, ct.DLG_SHOW_MODAL)
        ct.dlg_proc(self.h, ct.DLG_FREE)
        '!!! changed'
        return False
        
    def _on_snippet_selected(self, id_dlg, id_ctl, data='', info=''):
        print('snip sel')
        pkg = self._get_sel_pkg()
        snips_fn,lexers = self._get_sel_group(pkg)
        #snips = self.file_snippets.get(pkg['path'])
        snip_name,snip = self._get_sel_snip(pkg, snips_fn)
        
        if snip_name == 'new' and snip == None:
            self._create_snip(pkg, snips_fn)
            return

        print(f' snip sel:{snip_name}: {snip}')

        ct.dlg_proc(self.h, ct.DLG_CTL_PROP_SET, index=self.n_alias, prop={
                    'val': snip.get('prefix', ''),
                    'en': True,
                })
        ct.dlg_proc(self.h, ct.DLG_CTL_PROP_SET, index=self.n_edit, prop={
                    'en': True,
                })
        body = snip.get('body', [])
        txt = '\n'.join(body)  if type(body) == list else  body
        self.ed.set_text_all(txt)
                    
        
    def _on_group_selected(self, id_dlg, id_ctl, data='', info=''):
    #def _on_package_selected(self, *args, **vargs):
        print('group sel')
        #print(f'combo sel:{args}, {vargs}')
        # disable all below 'group'
        for n in [self.n_alias, self.n_edit]:
            ct.dlg_proc(self.h, ct.DLG_CTL_PROP_SET, index=n, prop={
                        'val': None,
                        'en': False,
                    })
        self.ed.set_text_all('')
        
        pkg = self._get_sel_pkg()
        snips_fn,lexers = self._get_sel_group(pkg) # filename:,lexers:,snippets:

        if snips_fn == 'new'  and lexers == None:
            self._create_group(pkg)
            return

        print(f' * selected B:group: {snips_fn}, lexers:{lexers}')

        if self.file_snippets.get((pkg['path'],snips_fn)) == None:
            self._load_package_snippets(pkg['path'])
            print(f'   + loaded group snips')
        else:
            print(f'   + group snps already laoded: {self.file_snippets}')

        
        ### fill groups
        # lexers
        ct.dlg_proc(self.h, ct.DLG_CTL_PROP_SET, index=self.n_lex, prop={
                    'val': ', '.join(lexers),
                    'en': True,
                })
                
        # snippet names
        snip_items = [name for name,val in self.file_snippets.get((pkg['path'],snips_fn)).items() 
                                                            if 'body' in val and 'prefix' in val]
        snip_items.sort()
        self.snip_items = [*snip_items]
        
        snip_items.insert(0, '[New...]')
        snip_items = '\t'.join(snip_items)
        ct.dlg_proc(self.h, ct.DLG_CTL_PROP_SET, index=self.n_snippets, prop={
                    'val': None, # selected item
                    'items': snip_items,
                    'en': True,
                })
        
    def _on_package_selected(self, id_dlg, id_ctl, data='', info=''):
    #def _on_package_selected(self, *args, **vargs):
        print('pkg sel')
        #print(f'combo sel:{args}, {vargs}')
        # disable all below 'group'
        for n in [self.n_lex, self.n_snippets, self.n_alias, self.n_edit]:
            ct.dlg_proc(self.h, ct.DLG_CTL_PROP_SET, index=n, prop={
                        'val': None,
                        'en': False,
                        'items': None,
                    })
        self.ed.set_text_all('')
        
        pkg = self._get_sel_pkg()
        
        if pkg == 'new':
            changed = self._create_pkg()
            return

        print(f' * selected pkg: {pkg["name"]}')

        # fill groups
        items = list(pkg['files'])
        items.sort()
        self._groups_items = [*items] #TODO reset when resetting
        
        # select package with specified lexer
        if self.select_lex and items:
            for i,lexs in enumerate(pkg.get('files', {}).values()):
                if self.select_lex in lexs:
                    items[i] += f'   (*{self.select_lex})'
        
        items.insert(0, '[New...]')
        items = '\t'.join(items)
        ct.dlg_proc(self.h, ct.DLG_CTL_PROP_SET, index=self.n_groups, prop={
                    'val': None,
                    'en': True,
                    'items': items,
                })
                
    def _create_snip(self, pkg, snips_fn):
        print(f' ~~~ new C:snip ~~~: {pkg["path"]};  group:{snips_fn}')
        name = ct.dlg_input('New snippet name:', '')
        print(f' snip name: {name}')

        
        #TODO check if exists
        if name:
            snips = self.file_snippets.get((pkg['path'], snips_fn))
            print(f'  snips:{snips}')

            if snips != None:
                snips[name] = {'prefix':'alias', 'body':''}
                self.modified.append((TYPE_GROUP, pkg['path'], name))
                
                # select new snip
                self._fill_forms(sel_pkg_path=pkg['path'], sel_group=snips_fn, sel_snip=name)
                
                
    def _create_group(self, pkg):
        print(f' ~~~ create new B:Group ===')
        lex = ct.ed.get_prop(ct.PROP_LEXER_FILE)
        name = lex  if lex else  'snippets'
        #TODO check if exists
        name = ct.dlg_input('New snippet group name:', name)
        print(f'new group name:{name}')
            
        if name: #TODO add to modifieds (group and package)
            if not name.endswith('.json'):
                name += '.json'
            if name in pkg:
                print(f'package already has group {name}')
            
            pkg['files'][name] = [lex]
            self.file_snippets[(pkg['path'], name)] = {} #TODO check if exists
            self.modified.append((TYPE_PKG, pkg['path']))
            self.modified.append((TYPE_GROUP, pkg['path'], name))
            
            # select new group
            self._fill_forms(sel_pkg_path=pkg['path'], sel_group=name)
            
    #TODO check if exists
    def _create_pkg(self):
        print(f' ~~~ create new package ===') # TODO sort after new, select new
        lex = ct.ed.get_prop(ct.PROP_LEXER_FILE)
        name = 'New_'+lex  if lex else  'NewPackage'
        name = ct.dlg_input('New package name:', name)
        print(f'new pkg name:{name}')

            
        if name: #TODO add to modifieds
            newpkg = {'name': name,
                        'files': {}, 
                        'path': os.path.join(MAIN_SNIP_DIR, name)}
            self.packages.append(newpkg) # update packages and select new
            self._sort_pkgs()
            self.modified.append((TYPE_PKG, newpkg['path']))
            # select new package
            self._fill_forms(sel_pkg_path=newpkg['path'])
            
        
    def _load_package_snippets(self, package_path):
        for pkg in self.packages:
            if pkg.get('path') != package_path:
                continue
            for snips_fn in pkg.get('files', {}): # filename, lexers
                snips_path = os.path.join(package_path, 'snippets', snips_fn)
                if not os.path.exists(snips_path):
                    print(f' ERR: snips_path not file:{snips_path}')
                    continue
                
                with open(snips_path, 'r', encoding='utf-8') as f:
                    snips = json.load(f)
                print(f' * loaded snips:{len(snips)}')

                self.file_snippets[(package_path,snips_fn)] = snips
            return
        else:
            print(' ERR: no suck pkg: {package_path}')

        
    def _load_packages(self):
        res = [] # list of configs
        for path in SNIP_DIRS:
            if not os.path.exists(path):
                return
            for pkg in os.scandir(path):
                if not pkg.is_dir():
                    continue
                cfg_path = os.path.join(pkg, 'config.json')
                if not os.path.exists(cfg_path):
                    print("{} - it isn't package".format(cfg_path))
                    return
                    
                with open(cfg_path, 'r', encoding='utf8') as f:
                    cfg = json.load(f)
                #lexers = set()
                #for lx in cfg.get('files', {}).values():
                    #lexers.update(lx)
                #cfg.update(
                    #{'path': pkg, 'type': sn_type, 'lexers': lexers, 'loaded': False}
                #)
                cfg['path'] = pkg.path #TODO remove path before saving
                res.append(cfg)
        return res
        
    def _sort_pkgs(self):
        self.packages.sort(key=lambda pkg: pkg.get('name'))
        
    def _get_sel_snip(self, pkg, snip_fn):
        p = ct.dlg_proc(self.h, ct.DLG_CTL_PROP_GET, index=self.n_snippets)
        isel = int(p['val'])
        if isel == 0:
            return 'new',None
        else:
            name = self.snip_items[isel-1] # new is first
            snip = self.file_snippets[(pkg['path'], snip_fn)][name]
            return name,snip
        
    def _get_sel_group(self, pkg):
        p = ct.dlg_proc(self.h, ct.DLG_CTL_PROP_GET, index=self.n_groups)
        isel = int(p['val'])
        if isel == 0:
            return 'new',None
        else:
            filename = self._groups_items[isel-1]
            lexers = pkg['files'][filename]
            return filename,lexers
        
    def _get_sel_pkg(self):
        p = ct.dlg_proc(self.h, ct.DLG_CTL_PROP_GET, index=self.n_package)
        isel = int(p['val'])
        if isel == 0:
            return 'new'
        else:
            return self.packages[isel-1]
        

