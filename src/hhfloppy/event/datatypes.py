from __future__ import annotations # Needed to fix https://github.com/jcrist/msgspec/issues/924

from enum import Enum
from typing import NewType, Union
import uuid

import msgspec

PyHXCFERunID = NewType('PyHXCFERunID', uuid.UUID)
FloppyDiskCaptureID = NewType('FloppyDiskCaptureID', uuid.UUID)
CommandRunID = NewType('CommandRunID', uuid.UUID)
FileConversionID = NewType('FileConversionID', uuid.UUID)

class HHFloppyTaggedStruct(msgspec.Struct, kw_only=True, frozen=True, tag_field="type", tag=True):
    pass


class FloppyInfoFromName(HHFloppyTaggedStruct, kw_only=True, frozen=True):
    datetime: str
    operator: str
    item_identifier: str
    drive: str
    dump_index: int

    hh_asset_id: int | None
    """
    Parsed from item identifier if it is prefixed with "rh" or "hh".
    """


class FloppyInfoFromXML(HHFloppyTaggedStruct, kw_only=True, frozen=True):
    file_size: int
    number_of_tracks: int
    number_of_sides: int
    format: str
    sector_per_track: int
    sector_size: int
    bitrate: int
    rpm: int
    crc32: int


class FloppyInfoFromIMD(HHFloppyTaggedStruct, kw_only=True, frozen=True):
    parsing_success: bool
    tracks: int | None
    modes: list[str] | None
    error_count: int | None
    parsing_errors: str | None

class FileChecksums(HHFloppyTaggedStruct, kw_only=True, frozen=True):
    md5: str
    sha256: str
    blake3: str

class FileMetadata(HHFloppyTaggedStruct, kw_only=True, frozen=True):
    filename: str
    size: int
    checksums: FileChecksums


class FloppyDiskFormat(Enum):
    HFE = 'HFE'
    MGT = 'MGT'
    DSK = 'DSK'

# Add e.g. info.json here once implemented
class FloppyDiskCaptureIDSource(Enum):
    hashed_directory_name = 'hashed_directory_name'

HHFLOPPY_EVENT_DATA_CLASS_UNION = Union[
    FloppyInfoFromName,
    FloppyInfoFromXML,
    FloppyInfoFromIMD,
    FileChecksums,
    FileMetadata
]

# For sanity, try to make a decoder

_decoder = msgspec.json.Decoder(HHFLOPPY_EVENT_DATA_CLASS_UNION)


class ProgramName(Enum):
    pyhxcfe = 'pyhxcfe'
    samdisk = 'samdisk'
    a8rawconv = 'a8rawconv'
