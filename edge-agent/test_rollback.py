from agent import EdgeAgent

def test_rollback_attack():
    # 1. Setup: Instantiate Agent and set current version to 2.0.0
    agent = EdgeAgent()
    agent.current_version = "2.0.0"
    
    # 2. Simulate: Incoming manifest with older version 1.9.9
    agent.manifest = {"version": "1.9.9"}
    
    print("[TEST] Running Rollback Attack Test...")
    
    # 3. Trigger: Manually trigger the logic you added to poll_manifest
    # Note: Depending on your exact code, you might call poll_manifest() 
    # or just the version check logic directly.
    result = agent.poll_manifest()
    
    # 4. Assert: Verify the agent rejected the update
    if agent.state == "IDLE" and result is False:
        print("[PASS] Rollback attack successfully blocked.")
    else:
        print("[FAIL] Rollback attack was NOT blocked.")

if __name__ == "__main__":
    test_rollback_attack()
