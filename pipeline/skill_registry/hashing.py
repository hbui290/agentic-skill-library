import hashlib
import stat
from pathlib import Path


class UnsafeCatalogPath(RuntimeError):
    pass


def _field(digest: object, value: bytes) -> None:
    digest.update(len(value).to_bytes(8, "big"))
    digest.update(value)


def tree_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    for item in sorted(path.rglob("*"), key=lambda current: current.relative_to(path).as_posix().encode()):
        relative = item.relative_to(path).as_posix()
        if relative.split("/")[-1] == ".DS_Store":
            continue
        if item.is_symlink():
            raise UnsafeCatalogPath(f"symlink rejected: {relative}")
        mode = item.stat().st_mode
        kind = b"d" if item.is_dir() else b"f"
        _field(digest, relative.encode())
        _field(digest, kind)
        _field(digest, b"1" if mode & stat.S_IXUSR else b"0")
        if item.is_file():
            _field(digest, item.read_bytes())
    return digest.hexdigest()
