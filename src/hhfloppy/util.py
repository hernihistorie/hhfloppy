import hashlib
import uuid
import subprocess
from pathlib import Path

import blake3

from event.datatypes import FileChecksums, FileMetadata, FloppyDiskCaptureID

FLOPPY_DISK_CAPTURE_FILENAME_UUID_NAMESPACE = uuid.UUID('019a9df8-6505-7032-923f-12a806f8bdbf')

def get_git_version() -> str:
    """Get the current git revision, with -dirty suffix if there are uncommitted changes."""
    try:
        # Get the short commit hash
        result = subprocess.run(
            ['git', 'rev-parse', '--short', 'HEAD'],
            capture_output=True,
            text=True,
            check=True,
            cwd=Path(__file__).parent
        )
        version = result.stdout.strip()
        
        # Check if there are uncommitted changes
        result = subprocess.run(
            ['git', 'diff-index', '--quiet', 'HEAD', '--'],
            cwd=Path(__file__).parent
        )
        
        # If exit code is non-zero, there are uncommitted changes
        if result.returncode != 0:
            version += '-dirty'
        
        return version
    except (subprocess.CalledProcessError, FileNotFoundError):
        # If git is not available or not a git repo, return unknown
        return 'unknown'

def floppy_disk_capture_filename_to_id(filename: str) -> FloppyDiskCaptureID:
    """Convert a floppy disk capture filename to a UUID based on its name."""
    if filename.endswith('_parsed'):
        filename = filename.removesuffix('_parsed')
    return FloppyDiskCaptureID(uuid.uuid5(namespace=FLOPPY_DISK_CAPTURE_FILENAME_UUID_NAMESPACE, name=filename))


class PathWithExtension():
    """Path container for files with a specific extension."""
    EXTENSION = ''

    def __init__(self, path: Path):
        if path.suffix.lower() != self.EXTENSION:
            raise ValueError(f"Error: Expected {self.EXTENSION} file, got {path}")
        self.path = path

    def __str__(self):
        return str(self.path)


def get_file_metadata(file_path: Path) -> FileMetadata:
    """Compute metadata (filename, size, checksums) for a file."""
    md5_hash = hashlib.md5()
    sha256_hash = hashlib.sha256()
    blake3_hash = blake3.blake3()

    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            md5_hash.update(chunk)
            sha256_hash.update(chunk)
            blake3_hash.update(chunk)

    return FileMetadata(
        filename=file_path.name,
        size=file_path.stat().st_size,
        checksums=FileChecksums(
            md5=md5_hash.hexdigest(),
            sha256=sha256_hash.hexdigest(),
            blake3=blake3_hash.hexdigest()
        )
    )


def get_directory_files_metadata(directory: Path) -> list[FileMetadata]:
    """Collect metadata for all files in a directory."""
    files_metadata: list[FileMetadata] = []
    for file_path in sorted(directory.iterdir()):
        if file_path.is_file():
            files_metadata.append(get_file_metadata(file_path))
    return files_metadata
