import uefitool
import sys
import hashlib
import struct

# Path to your firmware binary
firmware_path = "FWDB/dellinspiron.bin"  # Replace with your actual path

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
    return fit_result

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


if __name__ == "__main__":
    ok = verify_dxe_blob(firmware_path)
    if ok:
        print("[+] DXE BLOB verified successfully.")
    else:
        print("[-] DXE BLOB verification failed.")
