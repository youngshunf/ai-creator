import asyncio
import logging
import sys
import os

# Add src to path
sys.path.append(os.path.abspath("packages/agent-core/src"))
sys.path.append(os.path.abspath("apps/sidecar/src"))

from agent_core.graph.loader import GraphLoader
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
        
        graph_name = "browser-use-agent"
        logger.info(f"Loading graph: {graph_name}...")
        graph_def = executor.graph_loader.load(graph_name)
        logger.info("Graph loaded successfully.")
        
        # Mock Context
        ctx = RuntimeContext(
            runtime_type=RuntimeType.LOCAL,
            user_id="test-user",
            inputs={"goal": "Test Goal"},
            api_keys={},
            trace_id="test-trace",
            run_id="test-run",
            extra={
                "browser_manager": executor.browser_manager,
                "tool_registry": executor.tool_registry,
            }
        )
        
        # Equip skills manually since we are bypassing executor.execute logic
        skills = graph_def.get("spec", {}).get("skills", [])
        if skills:
            logger.info(f"Equipping skills: {skills}")
            executor.skill_manager.equip_agent(ctx, skills)
            
        logger.info("Compiling graph...")
        compiled = executor.compiler.compile(graph_def, ctx)
        logger.info("Graph compiled successfully!")
        
        print("\nGraph Structure:")
        print(f"Nodes: {list(compiled.node_functions.keys())}")
        # compiled.graph is LangGraph Runnable
        # We can't easily inspect edges from Runnable, but if compile() succeeded, structure is valid.
        
        await executor.shutdown()
        
    except Exception as e:
        logger.error(f"Validation failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(validate())
