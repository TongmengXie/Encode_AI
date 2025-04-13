from dotenv import load_dotenv
import os
import argparse
import json
import os
from typing import Literal, Type
from langchain.schema import HumanMessage, SystemMessage

from portia import (
    DefaultToolRegistry,
    InMemoryToolRegistry,
    MultipleChoiceClarification,
    Portia,
    McpToolRegistry,
    Config,
    Tool,
    ToolHardError,
    ToolRunContext,
    PlanRunState    
)
from portia.cli import CLIExecutionHooks
from pydantic import BaseModel, Field
from portia.llm_wrapper import LLMWrapper
from portia.config import LLM_TOOL_MODEL_KEY

import importlib

tools = [
    "utils.RouteRecommTool",
    # "ContentGenTool",
    # "UserMatchTool",
    # "DestinationRecommTool",
    # "BlogGenTool"
]

tool_instances = []
from utils.RouteRecommTool import RouteRecommTool


load_dotenv()
PORTIA_API_KEY = os.getenv("PORTIA_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

def main(query):
    config = Config.from_default(default_log_level="INFO")

    tools = (
        DefaultToolRegistry(
            config=config,
        )
        # + InMemoryToolRegistry.from_local_tools(
        #     [RouteRecommTool()]
        # )
    )

    portia = Portia(config=config, tools=tools, execution_hooks=CLIExecutionHooks())
    # Run the test query and print the output!
    plan = portia.plan(
        f"""
You are an expert in tourist guidance. The user will describe the city they want to visit and you should generate a real, meaningful route, and visualize it on a map.

# Output Format

- Display the generated route on OpenStreetMap in an HTML format.
- Provide options for the user to download the map and route details.
- Confirm the availability of different formats (e.g., PDF, GPX, KML). 

# Steps

1. Receive the city description from the user.
2. Create a route based on the user's description.
3. Visualize the route using OpenStreetMap embedded in an HTML page.
4. Include buttons or links for downloading the route in various formats such as PDF, GPX, and KML.

# Notes

- Ensure the HTML page is well-structured for easy viewing and interaction.
- Verify that the downloadable formats are correctly referenced and clickable.

The user query is as follows: {query}
"""
    )
    print("Plan:")
    print(plan.model_dump_json(indent=2))
    
    
    carry_on = input("Please verify the plan, 0 for cancelling, 1 for going: ")
    if int(carry_on) == 1:
        plan_run = portia.run_plan(plan)
        # Check if the plan run was paused due to raised clarifications
        while plan_run.state == PlanRunState.NEED_CLARIFICATION:
            # If clarifications are needed, resolve them before resuming the plan run
            for clarification in plan_run.get_outstanding_clarifications():
                # For each clarification, prompt the user for input
                print(f"{clarification.user_guidance}")
                user_input = input("Please enter a value:\n" +
                                    (("\n".join(clarification.options) + "\n") 
                                        if isinstance(clarification, MultipleChoiceClarification)
                                        else ""))
                # Resolve the clarification with the user input
                plan_run = portia.resolve_clarification(clarification, user_input, plan_run)

            # Once clarifications are resolved, resume the plan run
            plan_run = portia.run(plan_run)
            print(plan_run.model_dump_json(indent=2))
        try:
            plan_run = portia.run(plan_run)
        except:
            print(plan_run.model_dump_json(indent=2))

if __name__ == "__main__":
    # main("I want to visit London today in a closed circle that takes almost 2 hours. Sakura themed")
    query = input("Hello! This is a trip advisor, please type your query: \n")
    main(query)
    