from __future__ import annotations # Needed to fix https://github.com/jcrist/msgspec/issues/924

import datetime
from typing import Literal, NewType, Union
import uuid

import msgspec
from msgspec import field

from .datatypes import HHFLOPPY_EVENT_DATA_CLASS_UNION, FileMetadata, FloppyInfoFromIMD, FloppyInfoFromName, FloppyInfoFromXML, HHFloppyTaggedStruct

EVENT_VERSION = 8
EVENT_NAMESPACE = 'hhfloppy'

class Event(HHFloppyTaggedStruct, kw_only=True, frozen=True):
    """Base class for events."""

    event_version: int = EVENT_VERSION
    event_timestamp: datetime.datetime = field(default_factory=datetime.datetime.now)
    event_namespace: str = EVENT_NAMESPACE
    event_id: uuid.UUID = field(default_factory=uuid.uuid7)

class TestEvent(Event, kw_only=True, frozen=True):
    test_data: str

PyHXCFERunId = NewType('PyHXCFERunId', uuid.UUID)

# Add e.g. info.json here once implemented
FloppyDiskCaptureIDSource = Literal['hashed_directory_name']

class PyHXCFEERunStarted(Event, frozen=True):
    """
    Event triggered when pyhxcfe starts processing.
    """
    pyhxcfe_run_id: PyHXCFERunId
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
    pyhxcfe_run_id: PyHXCFERunId
    floppy_disk_capture_id: uuid.UUID
    floppy_disk_capture_id_source: FloppyDiskCaptureIDSource
    floppy_disk_capture_directory: str
    success: bool
    formats: list[str]
    files_metadata: list[FileMetadata] | None = None

class FloppyDiskCaptureSummarized(Event, frozen=True):
    """
    Event triggered when a floppy disk capture has been summarized.
    """
    pyhxcfe_run_id: PyHXCFERunId
    floppy_disk_capture_id: uuid.UUID
    floppy_disk_capture_id_source: FloppyDiskCaptureIDSource
    floppy_disk_capture_directory: str

    name_info: FloppyInfoFromName
    xml_info: FloppyInfoFromXML
    imd_info: FloppyInfoFromIMD


class PyHXCFEERunFinished(Event, frozen=True):
    """
    Event triggered when pyhxcfe finishes processing.
    """
    pyhxcfe_run_id: PyHXCFERunId

FileConversionProgram = Literal['pyhxcfe', 'samdisk', 'a8rawconv']

class FileConverted(Event, frozen=True):
    """
    Event triggered when a file has been converted.
    """
    input_file_metadata: FileMetadata
    output_file_metadata: FileMetadata
    program: FileConversionProgram
    command: list[str]
    exit_code: int
    stdout: str
    stderr: str
    has_warnings: bool
    has_errors: bool

HHFLOPPY_EVENT_CLASS_UNION = Union[
    TestEvent,
    PyHXCFEERunStarted,
    FloppyDiskCaptureDirectoryConverted,
    FloppyDiskCaptureSummarized,
    PyHXCFEERunFinished,
    FileConverted
]

# For sanity, try to make a decoder

event_decoder = msgspec.json.Decoder(HHFLOPPY_EVENT_CLASS_UNION | HHFLOPPY_EVENT_DATA_CLASS_UNION)
