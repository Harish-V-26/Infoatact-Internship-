import time
import json
import hashlib

class EdgeAgent:
    def __init__(self):
        # Module 1: State Machine Initialization
        self.state = "IDLE"
        self.manifest = None
        print(f"[STATE] Agent started in status: {self.state}")

    def change_state(self, new_state):
        print(f"\n[STATE TRANSITION] {self.state} ──> {new_state}")
        self.state = new_state

    # Module 2: Manifest Poller
    def poll_manifest(self):
        self.change_state("POLLING")
        print("[POLLER] Checking secure server for new firmware updates...")
        time.sleep(1.5)  # Simulating network latency
        
        # Simulating an update manifest JSON payload received from a server
        mock_server_manifest = {
            "version": "2.0.0",
            "firmware_size_bytes": 120,
            "chunk_size_bytes": 32,
            "payload_data": "CRITICAL_UPDATE_DATA_PACKET_ABC_XYZ_SECURITY_PATCH_999_DUMMY_FIRMWARE_COMPLETED_SUCCESSFULLY_END",
            "expected_sha256": "" 
        }
        
        # Pre-calculating the correct hash of the payload for verification safety
        payload_bytes = mock_server_manifest["payload_data"].encode()
        mock_server_manifest["expected_sha256"] = hashlib.sha256(payload_bytes).hexdigest()
        
        self.manifest = mock_server_manifest
        print(f"[POLLER] New update manifest found! Target Version: {self.manifest['version']}")
        print(f"[POLLER] Manifest Content: {json.dumps(self.manifest, indent=2)}")

    # Module 3: Chunked Secure Downloader
    def download_firmware_chunked(self):
        if not self.manifest:
            print("[ERROR] No update manifest available to download.")
            return

        self.change_state("DOWNLOADING")
        raw_data = self.manifest["payload_data"]
        chunk_size = self.manifest["chunk_size_bytes"]
        
        assembled_firmware = ""
        total_length = len(raw_data)
        
        print(f"[DOWNLOADER] Initiating chunked download. Total size: {total_length} bytes. Chunk budget: {chunk_size} bytes.")
        
        # Processing file download sequentially in chunks to protect limited Edge Device RAM
        for i in range(0, total_length, chunk_size):
            chunk = raw_data[i:i+chunk_size]
            assembled_firmware += chunk
            print(f"  └─► Downloaded chunk [{i//chunk_size + 1}]: '{chunk}' ({len(chunk)} bytes)")
            time.sleep(0.8) # Simulate chunk stream delay
            
        print("[DOWNLOADER] Stream terminated. All pieces assembled locally.")
        self.verify_download(assembled_firmware)

    def verify_download(self, downloaded_data):
        self.change_state("VERIFYING")
        print("[SECURITY] Calculating SHA-256 fingerprint integrity checksum...")
        time.sleep(1)
        
        calculated_hash = hashlib.sha256(downloaded_data.encode()).hexdigest()
        expected_hash = self.manifest["expected_sha256"]
        
        print(f"  ├─ Calculated Hash: {calculated_hash}")
        print(f"  ├─ Expected Hash:   {expected_hash}")
        
        if calculated_hash == expected_hash:
            print("\n[SUCCESS] Verification passed! Signature matches perfectly. System Safe.")
            self.change_state("IDLE")
        else:
            print("\n[CRITICAL ERROR] Integrity Verification failed! Data corruption detected.")
            self.change_state("FAULT")

# --- Execution Simulation ---
if __name__ == "__main__":
    # Initialize the edge lifecycle
    agent = EdgeAgent()
    
    # 1. Trigger Polling State
    agent.poll_manifest()
    
    # 2. Trigger Downloader and Verification States
    agent.download_firmware_chunked()
