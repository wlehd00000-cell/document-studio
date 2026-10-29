"""Shared local I/O, bundled with its owner for plugin and standalone installs."""
import json
import os
from pathlib import Path
import tempfile
import time


def replace_file(source,destination):
    for attempt in range(5):
        try:
            os.replace(source,destination);return
        except PermissionError:
            if attempt==4:raise
            time.sleep(.025*(2**attempt))


def atomic_json(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.NamedTemporaryFile(mode='w',encoding='utf-8',dir=path.parent,
                                     suffix='.tmp',delete=False) as handle:
        temporary=Path(handle.name)
        json.dump(value,handle,ensure_ascii=False,indent=2);handle.write('\n')
        handle.flush();os.fsync(handle.fileno())
    try:replace_file(temporary,path)
    finally:
        if temporary.exists():temporary.unlink()
