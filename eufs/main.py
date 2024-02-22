import errno
import os
import stat

import fuse

fuse.fuse_python_api = (0, 2)


# For debugging

f = open("log.txt", "w")


def log(str):
    f.write(f"{str}\n")
    f.flush()


hello_path = "/hello"
hello_str = b"Hello World!\n"


class MyStat(fuse.Stat):
    def __init__(self):
        self.st_mode = 0
        self.st_ino = 0
        self.st_dev = 0
        self.st_nlink = 0
        self.st_uid = 0
        self.st_gid = 0
        self.st_size = 0
        self.st_atime = 0
        self.st_mtime = 0
        self.st_ctime = 0


class HelloFS(fuse.Fuse):
    def getattr(self, path):
        log(f"getattr: {path!r}")
        st = MyStat()
        if path == "/":
            st.st_mode = stat.S_IFDIR | 0o755
            st.st_nlink = 2
        elif path == hello_path:
            st.st_mode = stat.S_IFREG | 0o444
            st.st_nlink = 1
            st.st_size = len(hello_str)
        else:
            return -errno.ENOENT
        return st

    def readdir(self, path, offset):
        log(f"readdir: {path!r} {offset!r}")
        for r in ".", "..", hello_path[1:]:
            yield fuse.Direntry(r)

    def open(self, path, flags):
        log(f"open: {path!r} {flags!r}")
        if path != hello_path:
            return -errno.ENOENT
        accmode = os.O_RDONLY | os.O_WRONLY | os.O_RDWR
        if (flags & accmode) != os.O_RDONLY:
            return -errno.EACCES

    def read(self, path, size, offset):
        log(f"read: {path!r} {size!r} {offset!r}")
        if path != hello_path:
            return -errno.ENOENT
        slen = len(hello_str)
        if offset < slen:
            if offset + size > slen:
                size = slen - offset
            buf = hello_str[offset : offset + size]
        else:
            buf = b""
        return buf


from . import euph

def main():
    # server = HelloFS(version="%prog " + fuse.__version__, dash_s_do="setsingle")

    # server.parse(errex=1)
    # server.main()

    room = euph.Room("test")
    room.start()
    pass


if __name__ == "__main__":
    main()
