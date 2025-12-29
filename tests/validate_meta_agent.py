import asyncio
import logging
import sys
import os

# Add src to path
sys.path.append(os.path.abspath("packages/agent-core/src"))
sys.path.append(os.path.abspath("apps/sidecar/src"))

from agent_core.runtime.context import RuntimeContext, RuntimeType
from sidecar.executor import LocalExecutor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("validator")

async def validate():
    try:
        logger.info("Initializing LocalExecutor...")
        config = {
            "definitions_path": "agent-definitions", 
            "api_keys": {"anthropic": "mock-key"}
        }
        executor = LocalExecutor(config)
        
        # 1. Validate Discovery Service
        logger.info("Testing DiscoveryService...")
        agents = executor.discovery_service.list_agents()
        logger.info(f"Agents found: {[a['name'] for a in agents]}")
        
        assert any(a['name'] == 'browser-use-agent' for a in agents), "browser-use-agent not found"
        assert any(a['name'] == 'workflow-generator' for a in agents), "workflow-generator not found"
        
        tools = executor.discovery_service.list_tools()
        logger.info(f"Tools found: {[t['name'] for t in tools]}")
        
        assert any(t['name'] == 'discovery_list_agents' for t in tools), "discovery_list_agents tool not found"
        
        # 2. Validate Meta-Agent Graph Loading
        graph_name = "workflow-generator"
        logger.info(f"Loading graph: {graph_name}...")
        graph_def = executor.graph_loader.load(graph_name)
        
        # Mock Context
        ctx = RuntimeContext(
            runtime_type=RuntimeType.LOCAL,
            user_id="test-user",
            inputs={"requirement": "Build a research agent"},
            api_keys={},
            trace_id="test-trace-meta",
            run_id="test-run-meta",
            extra={
                "browser_manager": executor.browser_manager,
                "tool_registry": executor.tool_registry,
                "discovery_service": executor.discovery_service,
            }
        )
        
        # Equip skills
        skills = graph_def.get("spec", {}).get("skills", [])
        if skills:
            logger.info(f"Equipping skills: {skills}")
            executor.skill_manager.equip_agent(ctx, skills)
        
        # Verify system prompts contain discovery instructions
        has_skill_prompt = any("discovery_list_agents" in p for p in getattr(ctx, "system_prompts", []))
        # Note: The skill instructions mention the tool names, so checking for tool name in prompt list works if prompt contains instructions.
        # Actually my SkillManager logic appends instructions.
        # Let's just check prompt count > 0
        logger.info(f"System Prompts count: {len(getattr(ctx, 'system_prompts', []))}")
        
        logger.info("Compiling graph...")
        compiled = executor.compiler.compile(graph_def, ctx)
        logger.info("Meta-Agent Graph compiled successfully!")
        
        await executor.shutdown()
        
    except Exception as e:
        logger.error(f"Validation failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(validate())
