from pathlib import Path
import sys
import subprocess
import typer
import tqdm

from event.event_store import EventStore
from event.events import CommandRan, FileConverted, Event, FloppyDiskCaptureConverted
from event.datatypes import FloppyDiskFormat, FloppyDiskCaptureIDSource, ProgramName
from util import PathWithExtension, get_file_metadata, floppy_disk_capture_filename_to_id

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

def run_command(command: list[str]) -> CommandRan:
    output = subprocess.run(command, check=True, text=True, capture_output=True)

    event = CommandRan(
        command=command,
        exit_code=output.returncode,
        stdout=output.stdout,
        stderr=output.stderr,
    )
    return event

def samdisk_convert(input_filepath: HFEPath, output_filepath: MGTPath | DSKPath) -> tuple[CommandRan, FileConverted]:
    command: list[str] = [
        'wine',
        str(SAMDISK_BINARY_PATH),
        str(input_filepath),
        str(output_filepath),
    ]

    command_ran_event = run_command(command)

    input_file_metadata = get_file_metadata(input_filepath.path)
    output_file_metadata = get_file_metadata(output_filepath.path)

    has_warnings = False
    has_errors = False
    for line in command_ran_event.stdout.splitlines() + command_ran_event.stderr.splitlines():
        if 'Warning:' in line:
            has_warnings = True
        if 'Error:' in line:
            has_errors = True

    file_converted_event = FileConverted(
        command_run_id=command_ran_event.command_run_id,
        input_file_metadata=input_file_metadata,
        output_file_metadata=output_file_metadata,
        program=ProgramName.samdisk,
        has_warnings=has_warnings,
        has_errors=has_errors,
    )
    return (command_ran_event, file_converted_event)

def floppy_disk_capture_convert(input_filepath: HFEPath, target_format: FloppyDiskFormat) -> tuple[CommandRan, FileConverted, FloppyDiskCaptureConverted]:
    if target_format == FloppyDiskFormat.MGT:
        output_filepath = MGTPath(input_filepath.path.parent / 'disk.mgt')
    elif target_format == FloppyDiskFormat.DSK:
        output_filepath = DSKPath(input_filepath.path.parent / 'disk.dsk')
    else:
        raise ValueError(f"Error: Unsupported target format {target_format}")

    command_ran_event, file_converted_event = samdisk_convert(input_filepath, output_filepath)

    floppy_disk_capture_converted_event = FloppyDiskCaptureConverted(
        floppy_disk_capture_id=floppy_disk_capture_filename_to_id(input_filepath.path.parent.name),
        floppy_disk_capture_id_source=FloppyDiskCaptureIDSource.hashed_directory_name,
        floppy_disk_capture_directory=str(input_filepath.path.parent.name),
        file_conversion_id=file_converted_event.file_conversion_id,
        source_format=FloppyDiskFormat.HFE,
        target_format=target_format,
        has_warnings=file_converted_event.has_warnings,
        has_errors=file_converted_event.has_errors,
    )

    return (command_ran_event, file_converted_event, floppy_disk_capture_converted_event)

def conv_dir(dirpath: Path) -> list[Event]:
    events: list[Event] = []

    hfe_filepaths = sorted(dirpath.glob('**/*.hfe'))

    print(f"Found {len(hfe_filepaths)} .hfe files to convert.")

    for hfe_filepath in tqdm.tqdm(hfe_filepaths):
        hfe_path = HFEPath(hfe_filepath)
        tqdm.tqdm.write(f"Converting {hfe_path}...")
        events += floppy_disk_capture_convert(hfe_path, FloppyDiskFormat.MGT)
        events += floppy_disk_capture_convert(hfe_path, FloppyDiskFormat.DSK)

    num_files_with_warnings = 0
    num_files_with_errors = 0

    for event in events:
        if isinstance(event, FileConverted):
            if event.has_warnings:
                num_files_with_warnings += 1
            if event.has_errors:
                num_files_with_errors += 1
    
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
