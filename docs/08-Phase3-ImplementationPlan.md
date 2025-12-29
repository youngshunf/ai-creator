# Phase 3: Meta-Agent Implementation Plan

## Goal
Implement a Meta-Agent that can generate executable Agent Graphs (YAML) from natural language descriptions. This requires the agent to "know" what tools and other agents are available.

## User Review Required
> [!IMPORTANT]
> This phase introduces a new module `agent_core.discovery` and new tools.

## Proposed Changes

### `packages/agent-core/src/agent_core/discovery/`
#### [NEW] [service.py](file:///Users/mac/saas/ai-creator/packages/agent-core/src/agent_core/discovery/service.py)
- Implement `DiscoveryService`:
    - `list_agents()`: Scans `agent-definitions` directory.
    - `list_tools()`: Scans `ToolRegistry`.
    - `get_agent_details(name)`: Returns full agent YAML/JSON.
    - `get_tool_details(name)`: Returns tool schema.

### `packages/agent-core/src/agent_core/tools/`
#### [NEW] [discovery.py](file:///Users/mac/saas/ai-creator/packages/agent-core/src/agent_core/tools/discovery.py)
- Implement `AgentDiscoveryTool`: Wraps `DiscoveryService.list_agents` and `get_agent_details`.
- Implement `ToolDiscoveryTool`: Wraps `DiscoveryService.list_tools` and `get_tool_details`.

### `agent-definitions/skills/`
#### [NEW] [workflow-generator.md](file:///Users/mac/saas/ai-creator/agent-definitions/skills/workflow-generator.md)
- System Prompt: Instructions on how to construct a valid `Graph` YAML.
    - Explanation of `inputs`, `state`, `nodes`, `edges`.
    - Rules for `llm_generate` and `tool_executor` usage.
    - Example of a valid graph.

### `agent-definitions/`
#### [NEW] [workflow-generator.yaml](file:///Users/mac/saas/ai-creator/agent-definitions/workflow-generator.yaml)
- The Meta-Agent Graph.
- **Inputs**: `requirement` (str).
- **Nodes**:
    - `planner`: Uses `workflow-generator` skill + `discovery` tools to generate YAML.
- **Outputs**: `graph_yaml` (str).

## Verification Plan

### Automated Tests
- **Discovery Service Test**: `tests/test_discovery.py`
    - Verify it correctly finds `browser-use-agent` and existing tools.
- **Meta-Agent Test**: `tests/test_meta_agent.py`
    - Initialize `workflow-generator` graph.
    - Mock LLM response with a predefined YAML.
    - Verify output is valid YAML.
