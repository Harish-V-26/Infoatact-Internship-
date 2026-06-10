# Week 1 — Dummy Firmware Generator
# Owner: Rishi (Edge Agent / QA)
# Branch: rishi-edge
# Creates a dummy .bin firmware file for testing the signing pipeline

import struct
import os


def create_dummy_firmware(output_path="edge-agent/dummy_firmware.bin", version="1.0.0"):
    """
    Creates a dummy firmware binary file for testing.
    Contains a simple header with version info and mock payload.
    Args:
        output_path (str): Where to save the .bin file
        version (str): Version string to embed in firmware
    """
    print(f"[*] Creating dummy firmware v{version}...")

    # Firmware header structure
    magic_bytes = b"OTA_FW"          # Magic identifier
    version_bytes = version.encode().ljust(16, b"\x00")  # 16 byte version field
    build_number = struct.pack(">I", 1)   # Build number as 4-byte big-endian int

    # Mock payload — simulates actual firmware code
    payload = (
        b"FIRMWARE_PAYLOAD_START\n"
        b"IoT Cargo Tracker Firmware\n"
        b"Version: " + version.encode() + b"\n"
        b"This is a simulated firmware binary for OTA testing.\n"
        b"In production this would contain compiled machine code.\n"
        b"FIRMWARE_PAYLOAD_END\n"
    )

    # Combine all parts
    firmware_data = magic_bytes + version_bytes + build_number + payload

    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)

    with open(output_path, "wb") as f:
        f.write(firmware_data)

    print(f"[✓] Dummy firmware created: {output_path}")
    print(f"[✓] File size: {len(firmware_data)} bytes")
    print(f"[✓] Version embedded: {version}")


if __name__ == "__main__":
    create_dummy_firmware()
