﻿import zipfile
from collections import namedtuple
import os
import shutil
import json
import requests
import tempfile
import threading as th
from typing import Dict

# from cuda_dev import dev


lock_exts = th.Lock()
TEMPDIR = os.path.join(tempfile.gettempdir(), 'cudatext')
TEMPFILE = os.path.join(TEMPDIR, 'sn.vsix')
URL = "https://marketplace.visualstudio.com/_apis/public/gallery/extensionquery"
HEAD = {
    "accept": "application/json;api-version=3.0-preview.1",
    "accept-encoding": "gzip, deflate, br",
    "content-type": "application/json",
}


def mkdir(*args):
    if not os.path.exists(args[0]):
        os.mkdir(*args)


# make temp directory
mkdir(TEMPDIR)


def make_exts_list(src):
    """Make Extension list.
    """
    # dev(src)
    extensions = src.get('results')[0].get("extensions")
    extensions_list = []
    for e in extensions:
        if 'Snippets' not in e.get("categories"):
            continue
        _url = None
        for k in e.get("versions")[0].get("files"):
            if k.get("assetType") == "Microsoft.VisualStudio.Services.VSIXPackage":
                _url = k.get('source')
                break
        if not _url:
            continue
        stat = 0
        statistic = e.get("statistics")
        if statistic:
            for k in statistic:
                if k.get("statisticName") == 'install':
                    stat = k.get("value", 0)
                    break
        ext = {
            'name': e.get("extensionName", '-'),
            'display_name': e.get("displayName", '-'),
            'description': e.get("shortDescription", ''),
            'version': e.get("versions", [{}])[0].get("version", ''),
            'url': _url,
            'stat': stat,
            }
        extensions_list.append(ext)
    return extensions_list


def query_extensions_by_name(name='', page_size=100, page_number=1):
    """Get snippets extensions list by name.

    :param name: name for search snippets extensions
    :param page_size: max count of extensions for return
    :param page_number: which page will be return
    :return: list of Extension objects or empty list
    """
    payload = {
        "assetTypes": [],
        "filters": [
            {
                "criteria": [
                    {"filterType": 8, "value": "Microsoft.VisualStudio.Code"},
                    {"filterType": 10, "value": name},
                    {"filterType": 12, "value": "37888"},
                    {"filterType": 5, "value": "Snippets"},
                ],
                "direction": 2,
                "pageSize": page_size,
                "pageNumber": page_number,
                "sortBy": 0,
                "sortOrder": 0,
            }
        ],
        "flags": 870,
    }
    r = requests.post(URL, headers=HEAD, json=payload)
    if r.status_code == 200:
        return make_exts_list(r.json())
    else:
        return []


def query_all_snips_extensions(page_size=50, page_number=1):
    payload = {
        "filters": [
            {
                "criteria": [
                    {"filterType": 8, "value": "Microsoft.VisualStudio.Code"},
                    {"filterType": 10, "value": 'target:"Microsoft.VisualStudio.Code" '},
                    {"filterType": 12, "value": "37888"},
                    {"filterType": 5, "value": "Snippets"},
                ],
                "pageSize": page_size,
                "pageNumber": page_number,
                "sortBy": 4,
                "sortOrder": 0,
            }
        ],
        "assetTypes": [],
        "flags": 870,
    }
    r = requests.post(URL, headers=HEAD, json=payload)
    if r.status_code == 200:
        return make_exts_list(r.json())
    else:
        return []


def get_all_snip_exts():
    result = []

    def get_res(page_number):
        res = query_all_snips_extensions(500, page_number)
        if not res:
            return
        with lock_exts:
            result.extend(res)

    # dev.tstart()
    threds = []
    try:
        for i in range(1, 10):
            t = th.Thread(target=get_res, args=(i,))
            threds.append(t)
            t.start()
        for i in threds:
            i.join()
        # dev.tstop()
        # dev(len(result))
    except requests.exceptions.ConnectionError:
        print("Connection error :(")
    return result


def prepare_vs_snips(f):
    if not zipfile.is_zipfile(f):
        print('It is not a zip file')
        return
    with zipfile.ZipFile(f) as _zip:
        with _zip.open('extension/package.json') as package:
            _f = package.read().decode('utf8')
            js = json.loads(_f)
            vs = {
                'ext': f,
                'name': js.get('name'),
                'version': js.get('version'),
                'display_name': js.get('displayName'),
                'description': js.get('description'),
            }
            contributes = js.get('contributes')
            if not contributes:
                return
            files = {}
            snips = contributes.get('snippets')
            if not snips:
                print("Sorry, but this package doesn't have any snippets.")
                return
            for sn in snips:
                lang = sn['language']
                path = sn['path']
                if path.find('.') == 0:
                    path = path.replace('.', 'extension', 1)
                paths = files.get(lang, [])
                paths.append(path)
                files[lang] = paths
            vs['files'] = files
            return vs


def download(url, file_name=TEMPFILE):
    """Download extension by url, and save into file_name"""
    with open(file_name, "wb") as file:
        r = requests.get(url)
        if r.status_code == 200:
            file.write(r.content)
            return prepare_vs_snips(file_name)


def install_vs_snips(path, vs: Dict):
    pkg_dir = os.path.join(path, vs.get('name'))
    snp_dir = os.path.join(pkg_dir, 'snippets')
    # make snippet dir
    mkdir(path)
    mkdir(pkg_dir)
    mkdir(snp_dir)
    # make config dict
    config = vs.copy()
    config.pop('files', '')
    config.pop('ext', '')
    # config['snippets'] = {}
    config['files'] = {}
    files = vs.get('files', {})
    file_paths = set()
    for k, v in files.items():
        for fp in v:
            file_name = fp.split('/')[-1]
            config['files'].setdefault(file_name, []).append(k)
            file_paths.add(fp)

    # save config.json
    with open(os.path.join(pkg_dir, 'config.json'), "w") as f:
        json.dump(config, f, indent=2)
    # exstract files
    with zipfile.ZipFile(TEMPFILE) as zf:
        for fp in file_paths:
            src = zf.open(fp)
            with open(os.path.join(snp_dir, fp.split('/')[-1]), 'wb') as f:
                shutil.copyfileobj(src, f)


if __name__ == '__main__':
    allse = get_all_snip_exts()
    print(len(allse))
    # print(allse[0])
    # q = query_all_snips_extensions(page_size=1)
