
import asyncio
import json
import sys
import os
from unittest.mock import MagicMock, patch

# Add src to path
sys.path.insert(0, os.path.abspath("apps/sidecar/src"))

from sidecar.main import SidecarServer

async def test_rpc():
    print("Testing Sidecar RPC...")
    
    # Mock config
    config = {"environment": "test"}
    server = SidecarServer(config)
    
    # Test 1: Initialize
    print("\n[Test 1] initialize")
    req = {
        "jsonrpc": "2.0",
        "method": "initialize",
        "params": {},
        "id": 1
    }
    resp = await server._handle_request(MagicMock(method="initialize", params={}, id=1))
    print(f"Response: {resp.result}")
    assert resp.result["status"] == "ok"
    assert resp.result["capabilities"]["credential_store"] == True
    
    # Test 2: Init Credential Sync
    print("\n[Test 2] init_credential_sync")
    params = {
        "api_base_url": "http://localhost:8000",
        "auth_token": "fake_token",
        "master_key": "fake_master_key"
    }
    # Mock CredentialSyncClient to avoid file ops and network
    with patch("sidecar.main.CredentialSyncClient") as MockClient:
        mock_instance = MockClient.return_value
        mock_instance.sync_all.return_value = []
        
        resp = await server._handle_request(MagicMock(method="init_credential_sync", params=params, id=2))
        print(f"Response: {resp.result}")
        assert resp.result["success"] == True
        assert server.credential_client is not None
        
        # Test 3: Sync All Credentials
        print("\n[Test 3] sync_all_credentials")
        # Mock sync_all to return a future
        f = asyncio.Future()
        f.set_result([])
        mock_instance.sync_all.return_value = f
        
        resp = await server._handle_request(MagicMock(method="sync_all_credentials", params={}, id=3))
        print(f"Response: {resp.result}")
        assert resp.result["success"] == True
        mock_instance.sync_all.assert_called_once()

        # Test 4: Publish Content
        print("\n[Test 4] publish_content")
        from sidecar.platforms.base import PublishResult
        
        # Mock publish executor
        mock_publish_result = PublishResult(
            success=True,
            platform_post_id="xhs_12345",
            platform_post_url="https://xiaohongshu.com/discovery/item/12345"
        )
        
        # We need to mock the execute_publish method on the server's publish_executor
        with patch.object(server.publish_executor, 'execute_publish', return_value=mock_publish_result) as mock_publish:
            publish_params = {
                "platform": "xiaohongshu",
                "account_id": "test_user",
                "title": "Test Title",
                "content": "Test Content",
                "images": ["/tmp/test.jpg"]
            }
            
            resp = await server._handle_request(MagicMock(method="publish_content", params=publish_params, id=4))
            print(f"Response: {resp.result}")
            
            assert resp.result["success"] == True
            assert resp.result["post_id"] == "xhs_12345"
            
            # Verify arguments
            mock_publish.assert_called_once()
            call_args = mock_publish.call_args
            assert call_args.kwargs['platform'] == "xiaohongshu"
            assert call_args.kwargs['account_id'] == "test_user"
            assert call_args.kwargs['content']['title'] == "Test Title"

        # Test 5: Verify Profile Sync Client Initialization
        print("\n[Test 5] verify_profile_sync_init")
        from sidecar.scheduler import get_sync_scheduler
        scheduler = get_sync_scheduler()
        # It should have been set during Test 2 (init_credential_sync)
        # Note: Since we patched CredentialSyncClient in Test 2, we need to check if ProfileSyncClient was also initialized.
        # But wait, in Test 2 we only patched sidecar.main.CredentialSyncClient.
        # ProfileSyncClient is instantiated directly in _handle_init_credential_sync.
        # However, since we are running in the same process, we can check the scheduler singleton.
        
        # But Test 2 was run inside a patch context. The side effect on scheduler persists?
        # Yes, get_sync_scheduler() returns a global singleton.
        
        if scheduler._profile_sync_client:
            print("ProfileSyncClient is set on scheduler.")
            assert scheduler._profile_sync_client.api_base_url == "http://localhost:8000"
        else:
            print("ProfileSyncClient is NOT set on scheduler (might be due to mocking in Test 2).")
            # Let's call init_credential_sync again without mocking CredentialSyncClient 
            # (or mock it but allow the rest of the method to run)
            
            # We need to mock ProfileSyncClient to avoid network calls if it were to be used immediately
            with patch("sidecar.main.ProfileSyncClient") as MockProfileClient, \
                 patch("sidecar.main.CredentialSyncClient"):
                
                params = {
                    "api_base_url": "http://localhost:8000",
                    "auth_token": "fake_token",
                    "master_key": "fake_master_key"
                }
                await server._handle_request(MagicMock(method="init_credential_sync", params=params, id=5))
                
                assert scheduler._profile_sync_client is not None
                print("ProfileSyncClient successfully initialized and set on scheduler.")

    print("\nAll tests passed!")

if __name__ == "__main__":
    asyncio.run(test_rpc())
