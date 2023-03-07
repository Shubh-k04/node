#!/usr/bin/env python
#
# Copyright (C) 2005-2019 Intel Corporation
#
# SPDX-License-Identifier: GPL-2.0-only OR BSD-3-Clause
#

from __future__ import print_function
import os
import sys
import shutil
import fnmatch
import subprocess
import shlex


def run_shell(cmd):
    print("\n>>", cmd)
    os.system(shlex.quote(cmd))


if sys.platform == 'win32':
    def read_registry(path, depth=0xFFFFFFFF, statics={}):
        try:
            import _winreg
        except ImportError:
            import winreg as _winreg
        parts = path.split('\\')
        hub = parts[0]
        path = '\\'.join(parts[1:])
        if not statics:
            statics['hubs'] = {'HKLM': _winreg.HKEY_LOCAL_MACHINE, 'HKCL': _winreg.HKEY_CLASSES_ROOT}

        def enum_nodes(curpath, level):
            if level < 1:
                return {}
            res = {}
            try:
                aKey = _winreg.OpenKey(statics['hubs'][hub], curpath, 0, _winreg.KEY_READ | _winreg.KEY_WOW64_64KEY)
            except WindowsError:
                return res

            try:
                i = 0
                while True:
                    name, value, _ = _winreg.EnumValue(aKey, i)
                    i += 1
                    res[name] = value
            except WindowsError:
                pass

            keys = []
            try:
                i = 0
                while True:
                    key = _winreg.EnumKey(aKey, i)
                    i += 1
                    keys.append(key)
            except WindowsError:
                pass

            _winreg.CloseKey(aKey)

            for key in keys:
                res[key] = enum_nodes(curpath + '\\' + key, level - 1)

            return res

        return enum_nodes(path, depth)


def get_vs_versions():  # https://www.mztools.com/articles/2008/MZ2008003.aspx
    if sys.platform != 'win32':
        return []
    versions = []

    hkcl = read_registry(r'HKCL', 1)
    for key in hkcl:
        if 'VisualStudio.DTE.' in key:
            version = key.split('.')[2]
            if int(version) >= 12:
                versions.append(version)

    if not versions:
        print("No Visual Studio version found")
    return sorted(versions)


def detect_cmake():
    if sys.platform == 'darwin':
        path, err = subprocess.Popen("which cmake", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
        if not path.strip():
            path, err = subprocess.Popen("which xcrun", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
            if not path.strip():
                print("No cmake and no XCode found...")
                return None
            return 'xcrun cmake'
    return 'cmake'


def main():
    import argparse
    parser = argparse.ArgumentParser()
    vs_versions = get_vs_versions()
    parser.add_argument("-d", "--debug", help="specify debug build configuration (release by default)", action="store_true")
    parser.add_argument("-c", "--clean", help="delete any intermediate and output files", action="store_true")
    parser.add_argument("-v", "--verbose", help="enable verbose output from build process", action="store_true")
    parser.add_argument("-pt", "--ptmark", help="enable anomaly detection support", 
