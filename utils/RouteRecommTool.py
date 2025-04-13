import argparse
import json
import os
from typing import Literal, Type
from dotenv import load_dotenv
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
)
from portia.cli import CLIExecutionHooks
from pydantic import BaseModel, Field
from portia.llm_wrapper import LLMWrapper
from portia.config import LLM_TOOL_MODEL_KEY


class RouteRecommInput(BaseModel):
    """Input for the RouteRecomm."""

    query: str = Field(
        ..., description="User query where transportation, destination and route shape should be extracted"
    )


class RouteRecommTool(Tool[str]):
    """
    """

    id: str = "user_id"
    name: str = "user_name"
    description: str = "Generates a real and effort-saving route in a tourist destination city in real world, consulting Google Map API. In your returned list, always give 1. real place names suitable for the theme and fits effortlessly within the route, 2. coordinates that exactly match the place, and 3. recommendation reason."
    args_schema: Type[BaseModel] = RouteRecommInput
    output_schema: tuple[str, str] = (
        "json",
        "a list of places to be visited in sequence"
    )

    def run(
        self,
        context: ToolRunContext,
        query: str,
    ) -> bool:
        llm = LLMWrapper.for_usage(LLM_TOOL_MODEL_KEY, context.config).to_langchain()
        messages = [
            SystemMessage(
                content='''You are an expert in tourist guidance. 
                The user will describe the city they want to visit and you should extract their destination, means of transportation and route shape."
                if any of the above information is absent, ask for clarification.
                The return should be adherent to this format: 
                "route_shape": {
                    "type": "array",
                    "items": {
                    "enum": [
                        "line",
                        "closed_circle"
                    ],
                    "type": "string"
                    },
                    "description": "The shape of the route to generate."
                },
                "destination_city": {
                    "type": "string",
                    "description": "The tourist destination city for the route."
                },
                "transportation_type": {
                    "type": "array",
                    "items": {
                    "enum": [
                        "walk",
                        "drive",
                        "public transport"
                    ],
                    "type": "string"
                    },
                    "description": "The type of transportation for the route."}

                User query is as the following:
                '''+query
            )
        ]
        response = llm.invoke(messages)
        destination =  response.content.split("\n")[-1].strip().get('destination')
        transportation = response.content.split("\n")[-1].strip().get('transportation')
        route_shape =  response.content.split("\n")[-1].strip().get('route_shape')
        
        if transportation is None:
            return MultipleChoiceClarification(
                plan_run_id=context.plan_run_id,
                user_guidance=(
                    "Could you clarify what type of route are you expecting?:\n"
                ),
                argument_name="route_shape",
                options=["closed_circle", "line"],
            )
        return destination, transportation, route_shape
