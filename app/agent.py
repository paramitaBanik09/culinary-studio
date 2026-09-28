# Copyright 2026 Google LLC
# Culinary Studio Agent definition

import json
from pathlib import Path

from a2ui.basic_catalog.provider import BasicCatalog
from a2ui.schema.manager import A2uiSchemaManager
from google.adk.agents import Agent
from google.adk.apps import App
from google.adk.code_executors import AgentEngineSandboxCodeExecutor
from google.adk.memory.vertex_ai_memory_bank_service import VertexAiMemoryBankService
from google.adk.models import Gemini
from google.adk.tools.function_tool import FunctionTool
from google.adk.tools.load_memory_tool import LoadMemoryResponse
from google.adk.tools.preload_memory_tool import preload_memory_tool
from google.adk.tools.tool_context import ToolContext
from google.genai import types

from app.a2ui_utils import a2ui_callback
from app.tools import (
    PROJECT_ID,
    add_menu_item,
    calculate_plate_cost,
    generate_dish_image,
    generate_dish_video,
    list_menu_items,
    search_recipe_inspiration,
)

# Load Agent Engine resource name from deployment_metadata.json if available
deployment_metadata_path = Path(__file__).parent.parent / "deployment_metadata.json"
agent_engine_resource_name = None
agent_engine_id = "811903575205609472"

if deployment_metadata_path.exists():
    try:
        metadata = json.loads(deployment_metadata_path.read_text())
        agent_engine_resource_name = metadata.get("remote_agent_runtime_id")
        if agent_engine_resource_name:
            agent_engine_id = agent_engine_resource_name.split("/")[-1]
    except Exception:
        pass

# Code Executor sandbox
code_executor = AgentEngineSandboxCodeExecutor(
    agent_engine_resource_name=agent_engine_resource_name
)

# Memory Bank Service for Vertex AI Memory Bank integration
memory_service = VertexAiMemoryBankService(
    project=PROJECT_ID,
    location="us-east1",
    agent_engine_id=agent_engine_id,
)


async def load_memory(query: str, tool_context: ToolContext) -> LoadMemoryResponse:
    """Loads the memory for the current user.

    Args:
        query: The query to load the memory for.
        tool_context: ADK ToolContext.

    Returns:
        A list of memory results.
    """
    try:
        search_memory_response = await tool_context.search_memory(query)
        return LoadMemoryResponse(memories=search_memory_response.memories)
    except ValueError:
        try:
            user_id = getattr(tool_context, "user_id", None) or "web-user"
            search_memory_response = await memory_service.search_memory(
                app_name="app", user_id=user_id, query=query
            )
            return LoadMemoryResponse(memories=search_memory_response.memories)
        except Exception:
            return LoadMemoryResponse(memories=[])
    except Exception:
        return LoadMemoryResponse(memories=[])


custom_load_memory_tool = FunctionTool(load_memory)

# Build A2UI system prompt using A2uiSchemaManager version 0.8
schema_manager = A2uiSchemaManager(
    version="0.8",
    catalogs=[BasicCatalog.get_config("0.8")],
)

INSTRUCTION = schema_manager.generate_system_prompt(
    role_description=(
        "You are Culinary Studio, an expert AI consultant for modern cafes, bistros, and restaurants. "
        "Your mission is to help restaurant owners design innovative menus, optimize food costs and margins, and curate visual dish presentations."
    ),
    workflow_description=(
        "Analyze requests, query or update menu items, perform plate cost calculations, search recipe inspiration, "
        "or generate dish images. You have access to Python code execution in a secure sandbox and persistent conversation memory. "
        "Return structured UI when appropriate."
    ),
    ui_description=(
        "Keep every surface tiny and flat: ONE Card > ONE Column > a few Text rows. "
        "Never nest a Card inside a Card. "
        "Use ONLY these components: Card, Column, Row, Text, and Image. Do not use "
        "Table or Heading (unsupported), or Buttons, actions, or forms (they do "
        "nothing in adk web). "
        "You may include one Image component, but only when you have a public https "
        "URL for the image (for example the URL an image tool returns after uploading "
        "to a public bucket). Set the Image url to that exact https link, for example "
        '{"Image": {"url": {"literalString": "https://..."}}}. Never point an '
        "Image at a bare filename, an artifact name, or a non-http(s) path. If you do "
        "not have a public URL, add a short Text line noting the image instead. "
        "No markdown in text; use the usageHint property ('h1', 'h2', 'body') for "
        "headings and emphasis. "
        "Output ONLY the raw A2UI JSON array — no prose, and never wrap it in "
        "<a2a_datapart_json> tags or 'kind'/'data'/'metadata' objects."
    ),
    include_schema=True,
    include_examples=True,
)

root_agent = Agent(
    name="root_agent",
    model=Gemini(
        model="gemini-flash-latest",
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction=INSTRUCTION,
    code_executor=code_executor,
    after_model_callback=a2ui_callback,
    tools=[
        list_menu_items,
        add_menu_item,
        calculate_plate_cost,
        generate_dish_image,
        generate_dish_video,
        search_recipe_inspiration,
        custom_load_memory_tool,
        preload_memory_tool,
    ],
)

app = App(
    root_agent=root_agent,
    name="app",
)
