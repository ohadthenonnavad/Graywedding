import uefitool
from uefitool import FitParser
import sys
import hashlib
import struct

# Path to your firmware binary
firmware_path = "FWDB/dell5310.bin"  # Replace with your actual path

def fit_security_parser(fw_path):
    # Create the parser instance
    parser = uefitool.FitParser()
    # Load the firmware file
    if not parser.load_file(firmware_path):
        print(f"Failed to load firmware file: {firmware_path}")
        sys.exit(1)             
    # Parse the FIT table
    fit_result = parser.parse_fit()
    # Print results
    
    # Get NVRAM offset and size
    offset, size = parser.get_nvram_region()
    print(f"NVRAM region found at offset 0x{offset:X} with size {size} bytes")
    
    return fit_result

BIOS_REGION_OFFSET = 0x1000000  # Adjust if your platform maps BIOS differently

def extract_nvram_bytes(firmware_path):
    from uefitool import FitParser

    parser = FitParser()
    if not parser.load_file(firmware_path):
        raise RuntimeError("Failed to load firmware")

    rel_offset, size = parser.get_nvram_region()
    abs_offset = BIOS_REGION_OFFSET + rel_offset

    print(f"NVRAM found at firmware file offset 0x{abs_offset:X}, size {size} bytes")

    with open(firmware_path, "rb") as f:
        f.seek(abs_offset)
        nvram_bytes = f.read(size)

    return nvram_bytes

def verify_dxe_blob(firmware_path: str) -> bool:
    """
    Scans a firmware image for a known GUID and verifies SHA256 hashes
    of one or more DXE BLOB structures following RAW section headers.
    Works for now, did not reverse engineer the protocol in the end. 
    
    Args:
        firmware_path: Path to the firmware .bin file

    Returns:
        True if any hash verification succeeds, False otherwise
    """
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

    try:
        with open(firmware_path, 'rb') as f:
            fw = f.read()
    except Exception as e:
        print(f"[!] Failed to read firmware: {e}")
        return False

    fw_size = len(fw)
    base_addr = 0xFFFFFFFF - fw_size + 1

    print(f"[+] Firmware size: {fw_size:#x}")
    print(f"[+] Base address assumption: {base_addr:#x}")

    verified = False

    for guid_offset in find_all(fw, GUID_BE):
        print(f"[+] Found target GUID at offset: {guid_offset:#x}")
        search_start = guid_offset + 16
        search_end = min(search_start + 0x200, fw_size)

        for raw_offset in find_all(fw, RAW_SECTION_HEADER, search_start, search_end):
            print(f"[+] Found RAW section at offset: {raw_offset:#x}")

            struct_offset = raw_offset + 4
            if struct_offset + 40 > fw_size:
                print(f"[-] Not enough data for full structure at {struct_offset:#x}")
                continue
        
            expected_hash = fw[struct_offset:struct_offset+32]
            region_base, region_size = struct.unpack_from('<II', fw, struct_offset + 32)

            print(f"[+] Parsed region base: {region_base:#x}, size: {region_size:#x}")
            if region_size == 0:
                print(f"[-] Skipping structure with size 0 at offset {struct_offset:#x}")
                continue

            region_offset = region_base - base_addr
            if region_offset < 0 or (region_offset + region_size) > fw_size:
                print(f"[-] Region out of firmware bounds (offset: {region_offset:#x})")
                continue

            region_data = fw[region_offset:region_offset + region_size]
            actual_hash = hashlib.sha256(region_data).digest()

            if actual_hash == expected_hash:
                print(f"[✓] Hash matches for region at offset {region_offset:#x}")
                verified = True
            else:
                print(f"[✗] Hash mismatch at {region_offset:#x}")
                print(f"    Expected: {expected_hash.hex()}")
                print(f"    Actual  : {actual_hash.hex()}")

    if not verified:
        print("[-] No matching hash structure validated")

    return verified

# EFI Variable Header format (UEFI Spec 2.7):
# struct EFI_VARIABLE_HEADER {
#   UINT32 StartId;          // 4 bytes (usually 0x55AA)
#   UINT32 State;            // 4 bytes
#   UINT32 Attributes;       // 4 bytes
#   UINT32 NameSize;         // 4 bytes (in bytes, UTF-16 encoded)
#   UINT32 DataSize;         // 4 bytes
#   WCHAR VariableName[];    // NameSize bytes (UTF-16LE string)
#   UINT8 VariableData[];    // DataSize bytes
# };

EFI_VAR_HDR_FORMAT = "<IIIII"  # little endian, 5 uint32
EFI_VAR_HDR_SIZE = struct.calcsize(EFI_VAR_HDR_FORMAT)

def parse_nvram_variables(nvram_bytes):
    offset = 0
    vars = []

    while offset + EFI_VAR_HDR_SIZE <= len(nvram_bytes):
        # Parse header
        start_id, state, attributes, name_size, data_size = struct.unpack_from(EFI_VAR_HDR_FORMAT, nvram_bytes, offset)
        
        # Validate StartId for sanity (0x55AA or 0xFEFEFEFE or so depending on firmware)
        # Some firmwares use different start signatures, adjust as needed
        if start_id != 0x55AA:
            # Not a valid variable header? Skip or break
            break
        
        offset += EFI_VAR_HDR_SIZE

        # Variable Name UTF-16LE string
        name_bytes = nvram_bytes[offset : offset + name_size]
        try:
            variable_name = name_bytes.decode('utf-16le').rstrip('\x00')
        except UnicodeDecodeError:
            variable_name = "<Invalid UTF16>"

        offset += name_size

        # Variable data
        variable_data = nvram_bytes[offset : offset + data_size]
        offset += data_size

        vars.append({
            "Name": variable_name,
            "Attributes": attributes,
            "DataSize": data_size,
            "Data": variable_data,
        })

        # Align offset to 4 or 8 bytes boundary if needed (some implementations pad variables)
        # Adjust alignment per your firmware behavior
        alignment = 4
        if offset % alignment != 0:
            offset += alignment - (offset % alignment)

    return vars


if __name__ == "__main__":
    ok = verify_dxe_blob(firmware_path)
    fit_security_parser(firmware_path)
    
    nvram_bytes = extract_nvram_bytes(firmware_path)
    print(nvram_bytes)
    variables = parse_nvram_variables(nvram_bytes)
    
    print(variables)
    if ok:
        print("[+] DXE BLOB verified successfully.")
    else:
        print("[-] DXE BLOB verification failed.")
