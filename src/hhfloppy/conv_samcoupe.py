from pathlib import Path
import sys
import subprocess
import typer
import tqdm

from event.event_store import EventStore
from event.events import FileConverted
from util import PathWithExtension, get_file_metadata

SAMDISK_BINARY_PATH = Path('deps/SAMdisk3811/SAMdisk.exe')

class HFEPath(PathWithExtension):
    """Path container for files with the HFE extension."""
    EXTENSION = '.hfe'

class MGTPath(PathWithExtension):
    """Path container for files with the MGT extension."""
    EXTENSION = '.mgt'

class DSKPath(PathWithExtension):
    """Path container for files with the DSK extension."""
    EXTENSION = '.dsk'

def samdisk_convert(input_filepath: HFEPath, output_filepath: MGTPath | DSKPath) -> FileConverted:
    command: list[str] = [
        'wine',
        str(SAMDISK_BINARY_PATH),
        str(input_filepath),
        str(output_filepath),
    ]

    output = subprocess.run(command, check=True, text=True, capture_output=True)

    input_file_metadata = get_file_metadata(input_filepath.path)
    output_file_metadata = get_file_metadata(output_filepath.path)

    has_warnings = False
    has_errors = False
    for line in output.stdout.splitlines() + output.stderr.splitlines():
        if 'Warning:' in line:
            has_warnings = True
        if 'Error:' in line:
            has_errors = True

    event = FileConverted(
        input_file_metadata=input_file_metadata,
        output_file_metadata=output_file_metadata,
        program='samdisk',
        command=command,
        exit_code=output.returncode,
        stdout=output.stdout,
        stderr=output.stderr,
        has_warnings=has_warnings,
        has_errors=has_errors,
    )
    return event


def conv_dir(dirpath: Path) -> list[FileConverted]:
    events: list[FileConverted] = []

    hfe_filepaths = sorted(dirpath.glob('**/*.hfe'))

    print(f"Found {len(hfe_filepaths)} .hfe files to convert.")

    for hfe_filepath in tqdm.tqdm(hfe_filepaths):
        hfe_path = HFEPath(hfe_filepath)
        mgt_path = MGTPath(hfe_filepath.parent / ('disk.mgt'))
        dsk_path = DSKPath(hfe_filepath.parent / ('disk.dsk'))

        tqdm.tqdm.write(f"Converting {hfe_path}...")
        events.append(samdisk_convert(hfe_path, mgt_path))
        events.append(samdisk_convert(hfe_path, dsk_path))

    num_files_with_warnings = sum(1 for e in events if e.has_warnings)
    num_files_with_errors = sum(1 for e in events if e.has_errors)

    print("Conversion summary:")
    print(f"  Total files converted: {len(events)}")
    print(f"  Files with warnings: {num_files_with_warnings}")
    print(f"  Files with errors: {num_files_with_errors}")

    return events


def main(dirpath: Path = typer.Argument(..., help="Directory path containing .hfe files to convert")):
    if not SAMDISK_BINARY_PATH.exists():
        sys.exit("Please download SAMdisk from https://simonowen.com/samdisk/ and place it in deps/SAMdisk3811")

    event_store = EventStore(namespace='hhfloppy', app="conv_samcoupe")

    events = conv_dir(dirpath)

    if events:
        event_store.emit_events(events)
        event_store.push()
    else:
        print("No events to push.")

if __name__ == '__main__':
    typer.run(main)
