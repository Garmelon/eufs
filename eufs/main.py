import errno
import os
import stat
import threading
from pathlib import Path

import fuse

from . import euph


fuse.fuse_python_api = (0, 2)


class EuFs(fuse.Fuse):
    def __init__(self, *args, **kwargs):
        fuse.Fuse.__init__(self, *args, **kwargs)

        self.rooms = {}

        self.join_room("test")

    def join_room(self, name):
        # Not threadsafe, but using threading.Lock broke things
        if name in self.rooms:
            return

        room = euph.Room(name)
        room.start()
        self.rooms[name] = room
        print(f"Joined &{name}")

    def leave_room(self, name):
        # Not threadsafe, but using threading.Lock broke things
        if name not in self.rooms:
            return

        room = self.rooms[name]
        room.stop()
        del self.rooms[name]
        print(f"Left &{name}")

    def getattr(self, path):
        print(f"getattr: {path!r}")

        parts = Path(path).parts
        if parts == ("/",):
            print(f"  is root")
            return fuse.Stat(
                st_mode=stat.S_IFDIR | 0o755,
                st_nlink=1,
            )
        print(f"  is not root")

        roomname = parts[1]
        texts = parts[2:]

        room = self.rooms.get(roomname)
        if not room:
            print(f"  is invalid room")
            return -errno.ENOENT
        print(f"  is valid room")
        if texts == ():
            return fuse.Stat(
                st_mode=stat.S_IFDIR | 0o755,
                st_nlink=1,
            )

        msg = room.find_msg_by_texts(texts)
        if not msg:
            print(f"  is invalid msg")
            return -errno.ENOENT
        print(f"  is valid msg")

        return fuse.Stat(
            st_mode=stat.S_IFDIR | 0o755,
            st_nlink=1,
            st_ctime=msg.time,
            st_mtime=msg.time,
            st_atime=msg.time,
        )

    def readdir(self, path, offset):
        print(f"readdir: {path!r} {offset!r}")

        parts = Path(path).parts
        if parts == ("/",):
            print(f"  is root")
            yield fuse.Direntry(".")
            yield fuse.Direntry("..")
            for room in self.rooms:
                yield fuse.Direntry(room)
            return
        print(f"  is not root")

        roomname = parts[1]
        texts = parts[2:]

        room = self.rooms.get(roomname)
        if not room:
            print(f"  is invalid room")
            return
        print(f"  is valid room")

        if texts == ():
            print("  children from room")
            children = {
                mid: msg for mid, msg in room.msgs.items() if msg.parent == None
            }
        else:
            msg = room.find_msg_by_texts(texts)
            if not msg:
                print(f"  is invalid msg")
            print(f"  is valid msg")
            print("  children from msg")
            children = msg.children

        print(children)

        children = list(children.values())
        children.sort(key=lambda m: m.time)
        for child in children:
            print(child.text)
            yield fuse.Direntry(child.text)

    def mkdir(self, path, mode):
        print(f"mkdir: {path!r} {mode!r}")

        parts = Path(path).parts
        if parts == ("/",):
            print(f"  is root")
            return -errno.EEXIST
        print(f"  is not root")

        roomname = parts[1]
        texts = parts[2:]

        room = self.rooms.get(roomname)
        if not room:
            print(f"  is invalid room")
            return -errno.ENOENT
        print(f"  is valid room")

        if texts == ():
            print(f"  is no content")
            return -errno.EEXIST

        content = texts[-1]
        texts = texts[:-1]

        if texts == ():
            print("  is root message")
            room.send(content)
            return

        msg = room.find_msg_by_texts(texts)
        if not msg:
            print(f"  is invalid msg")
            return -errno.ENOENT
        print(f"  is valid msg")

        print("  is child message")
        room.send(content, parent=msg.id)


def main():
    server = EuFs(version="%prog " + fuse.__version__, dash_s_do="setsingle")

    server.parse(errex=1)
    server.main()


if __name__ == "__main__":
    main()
