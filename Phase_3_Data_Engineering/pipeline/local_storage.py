
from pathlib import Path
import hashlib
import pandas as pd


BACKUP_ROOT = Path(__file__).resolve().parents[1] / "azure_backup"


def resolve_local_path(file_path):
    """Resolve a relative storage path safely within the backup directory."""
    root = BACKUP_ROOT.resolve()
    path = (root / file_path).resolve()

    if not path.is_relative_to(root):
        raise ValueError(f"Invalid storage path: {file_path}")

    return path


def load_csv(file_path):
    """Load a CSV from the local backup."""
    return pd.read_csv(resolve_local_path(file_path))


def read_bytes(file_path):
    """Read the original file bytes."""
    return resolve_local_path(file_path).read_bytes()


def file_exists(file_path):
    """Check whether a local file exists."""
    return resolve_local_path(file_path).is_file()


def get_checksum(file_path):
    """Calculate SHA-256 from the original file bytes."""
    return hashlib.sha256(read_bytes(file_path)).hexdigest()


def upload_file(file_path, content):
    """Write a new file without overwriting existing data."""
    path = resolve_local_path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    if isinstance(content, str):
        content = content.encode("utf-8")

    with path.open("xb") as file:
        file.write(content)

    print(f"LOCAL UPLOADED: {file_path}")



class LocalDownload:
    """Mimic the Azure download response."""

    def __init__(self, content):
        self.content = content

    def readall(self):
        return self.content


class LocalFileClient:
    """Provide local equivalents of Azure file operations."""

    def __init__(self, file_path):
        self.file_path = file_path
        self.path = resolve_local_path(file_path)

    def exists(self):
        return self.path.is_file()

    def download_file(self):
        return LocalDownload(read_bytes(self.file_path))

    def create_file(self, **kwargs):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("xb"):
            pass

    def append_data(self, data, offset, length):
        if offset != 0 or length != len(data):
            raise ValueError("Unsupported local append operation")

        with self.path.open("r+b") as file:
            file.seek(offset)
            file.write(data)

    def flush_data(self, length):
        if self.path.stat().st_size != length:
            raise RuntimeError("Local file length mismatch")


class LocalFilesystem:
    """Provide a filesystem interface compatible with existing calls."""

    def get_file_client(self, file_path):
        return LocalFileClient(file_path)

