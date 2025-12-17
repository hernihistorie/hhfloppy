from __future__ import annotations # Needed to fix https://github.com/jcrist/msgspec/issues/924

import datetime
from typing import NewType, Union
import uuid

import msgspec
from msgspec import field

from .datatypes import HHFLOPPY_EVENT_DATA_CLASS_UNION, CommandRunID, FileConversionID, FileMetadata, FloppyDiskFormat, FloppyInfoFromIMD, FloppyInfoFromName, FloppyInfoFromXML, HHFloppyTaggedStruct, FloppyDiskCaptureIDSource, FloppyDiskCaptureID, PyHXCFERunID, ProgramName

EVENT_VERSION = 10
EVENT_NAMESPACE = 'hhfloppy'

EventID = NewType('EventID', uuid.UUID)
class Event(HHFloppyTaggedStruct, kw_only=True, frozen=True):
    """Base class for events."""

    event_version: int = EVENT_VERSION
    event_timestamp: datetime.datetime = field(default_factory=datetime.datetime.now)
    event_namespace: str = EVENT_NAMESPACE
    event_id: EventID = field(default_factory=lambda: EventID(uuid.uuid7()))

class TestEvent(Event, kw_only=True, frozen=True):
    test_data: str

class PyHXCFEERunStarted(Event, frozen=True):
    """
    Event triggered when pyhxcfe starts processing.
    """
    pyhxcfe_run_id: PyHXCFERunID
    command: list[str]
    user: str | None
    host: str | None
    start_time: str
    git_revision: str

class FloppyDiskCaptureDirectoryConverted(Event, frozen=True):
    """
    Event triggered when a floppy disk capture has been converted
    using hxcfe.
    """
    pyhxcfe_run_id: PyHXCFERunID
    floppy_disk_capture_id: FloppyDiskCaptureID
    floppy_disk_capture_id_source: FloppyDiskCaptureIDSource
    floppy_disk_capture_directory: str
    success: bool
    formats: list[str]
    files_metadata: list[FileMetadata] | None = None

class FloppyDiskCaptureSummarized(Event, frozen=True):
    """
    Event triggered when a floppy disk capture has been summarized.
    """
    pyhxcfe_run_id: PyHXCFERunID
    floppy_disk_capture_id: FloppyDiskCaptureID
    floppy_disk_capture_id_source: FloppyDiskCaptureIDSource
    floppy_disk_capture_directory: str

    name_info: FloppyInfoFromName
    xml_info: FloppyInfoFromXML
    imd_info: FloppyInfoFromIMD


class PyHXCFEERunFinished(Event, frozen=True):
    """
    Event triggered when pyhxcfe finishes processing.
    """
    pyhxcfe_run_id: PyHXCFERunID

class CommandRan(Event, frozen=True):
    """
    Event triggered when an external command has been run.
    """
    command: list[str]
    exit_code: int
    stdout: str
    stderr: str
    command_run_id: CommandRunID = field(default_factory=lambda: CommandRunID(uuid.uuid7()))

class FileConverted(Event, frozen=True):
    """
    Event triggered when a file has been converted.
    """
    input_file_metadata: FileMetadata
    output_file_metadata: FileMetadata
    command_run_id: CommandRunID
    program: ProgramName
    has_warnings: bool
    has_errors: bool
    file_conversion_id: FileConversionID = field(default_factory=lambda: FileConversionID(uuid.uuid7()))

class FloppyDiskCaptureConverted(Event, frozen=True):
    """
    Event triggered when a floppy disk capture has been converted from one format to another.
    """
    floppy_disk_capture_id: FloppyDiskCaptureID
    floppy_disk_capture_id_source: FloppyDiskCaptureIDSource
    floppy_disk_capture_directory: str
    file_conversion_id: FileConversionID
    source_format: FloppyDiskFormat
    target_format: FloppyDiskFormat
    has_warnings: bool
    has_errors: bool

HHFLOPPY_EVENT_CLASS_UNION = Union[
    TestEvent,
    PyHXCFEERunStarted,
    FloppyDiskCaptureDirectoryConverted,
    FloppyDiskCaptureSummarized,
    PyHXCFEERunFinished,
    CommandRan,
    FileConverted,
    FloppyDiskCaptureConverted,
]

event_decoder = msgspec.json.Decoder(HHFLOPPY_EVENT_CLASS_UNION | HHFLOPPY_EVENT_DATA_CLASS_UNION)
