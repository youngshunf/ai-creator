import sys
import os
import traceback

sys.path.append("/Users/mac/saas/ai-creator/apps/sidecar/src")
sys.path.append("/Users/mac/saas/ai-creator/packages/agent-core/src")

def check():
    print("Checking stagehand import...")
    try:
        import stagehand
        print("Stagehand imported successfully")
    except ImportError:
        print("Stagehand import failed")
        return False
    except Exception as e:
        print(f"Stagehand import error: {e}")
        return False

    print("Checking LLM Config...")
    try:
        from agent_core.llm.config import LLMConfigManager
        config_manager = LLMConfigManager()
        llm_config = config_manager.load()
        print(f"Config loaded: {llm_config}")
        print(f"API Token: {llm_config.api_token}")
        return bool(llm_config.api_token)
    except Exception as e:
        print(f"LLM Config check failed: {e}")
        traceback.print_exc()
        return False

print(f"Result: {check()}")
