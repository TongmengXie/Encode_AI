from dotenv import load_dotenv
from portia import (
    Portia,
    default_config,
    example_tool_registry,
)

load_dotenv()

# Instantiate Portia with the default config which uses Open AI, and with some example tools.
portia = Portia(tools=example_tool_registry)
# Run the test query and print the output!
plan_run = portia.run('recommend a university in London')
print(plan_run.model_dump_json(indent=2))