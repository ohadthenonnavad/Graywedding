import hashlib
import struct
from analysis.PluginBase import AnalysisBasePlugin
from objects.file import FileObject

class AnalysisPlugin(AnalysisBasePlugin):
    NAME = 'dxeblobverifier'
    DESCRIPTION = 'Verify DXE BLOB hash structures in firmware'
    VERSION = '1.0.0'
    DEPENDENCIES = ('file_type',)
    MIME_BLACKLIST = ()
    FILE = __file__

    def process_object(self, file_object: FileObject) -> FileObject:
        result = {
            "matches": [],
            "verified": False
        }

        try:
            with open(file_object.file_path, 'rb') as f:
                fw = f.read()
        except Exception as e:
            self.logger.warning(f"[!] Failed to read firmware: {e}")
            return file_object

        GUID_BE = bytes.fromhex('441fc9cbbca45b4a8696703451d0b053')
        RAW_SECTION_HEADER = bytes.fromhex('54000019')

        def find_all(data, sub, start=0, end=None):
            pos = start
            end = end if end is not None else len(data)
            while pos < end:
                idx = data.find(sub, pos, end)
                if idx == -1:
                    return
                yield idx
                pos = idx + 1

        fw_size = len(fw)
        base_addr = 0xFFFFFFFF - fw_size + 1

        for guid_offset in find_all(fw, GUID_BE):
            search_start = guid_offset + 16
            search_end = min(search_start + 0x200, fw_size)

            for raw_offset in find_all(fw, RAW_SECTION_HEADER, search_start, search_end):
                struct_offset = raw_offset + 4
                if struct_offset + 40 > fw_size:
                    continue

                expected_hash = fw[struct_offset:struct_offset+32]
                region_base, region_size = struct.unpack_from('<II', fw, struct_offset + 32)

                if region_size == 0:
                    continue

                region_offset = region_base - base_addr
                if region_offset < 0 or (region_offset + region_size) > fw_size:
                    continue

                region_data = fw[region_offset:region_offset + region_size]
                actual_hash = hashlib.sha256(region_data).digest()

                match = {
                    "guid_offset": guid_offset,
                    "raw_offset": raw_offset,
                    "region_base": hex(region_base),
                    "region_size": hex(region_size),
                    "hash_match": actual_hash == expected_hash,
                }

                if actual_hash == expected_hash:
                    result["verified"] = True

                result["matches"].append(match)

        file_object.processed_analysis[self.NAME] = result
        return file_object

