import sys
import os

# Add apps/sidecar/src to sys.path to mimic the environment
sys.path.append("/Users/mac/saas/ai-creator/apps/sidecar/src")
sys.path.append("/Users/mac/saas/ai-creator/packages/agent-core/src")

try:
    from sidecar.browser.stagehand_client import StagehandClient
    print(f"Is Available: {StagehandClient.is_available()}")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
