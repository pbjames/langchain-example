from uuid import UUID
from langchain_anthropic import ChatAnthropic
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import BaseTool
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent
from dotenv import load_dotenv

from argparse import ArgumentParser


def multi_turn(
    model: ChatAnthropic, tools: list[TavilySearchResults], memory: MemorySaver
):
    agent_executor = create_react_agent(model, tools, checkpointer=memory)
    config = RunnableConfig(run_id=UUID("2578368d-a567-4635-a470-1b75cd1c41ec"))
    for step, metadata in agent_executor.stream(
        {"messages": [HumanMessage(content="hi im bob!")]},
        stream_mode="messages",
        config=config,
    ):
        if metadata["langgraph_node"] == "agent" and (text := step.text()):
            print(text, end="|")

    for chunk in agent_executor.stream(
        {"messages": [HumanMessage(content="whats my name?")]}, config=config
    ):
        print(chunk)
        print("----")


def weather(model: ChatAnthropic, tools: list[TavilySearchResults]):
    agent_executor = create_react_agent(model, tools)
    # response = agent_executor.invoke(
    #    {"messages": [HumanMessage(content="whats the weather in uk birmingham?")]},
    # )
    for chunk in agent_executor.stream(
        {"messages": [HumanMessage(content="whats my name?")]}, stream_mode="messages"
    ):
        print(chunk)


def main():
    if not load_dotenv():
        raise EnvironmentError(".env required")
    parser = ArgumentParser()
    parser.add_argument("-v", "--verbose", action="store_true", help="debug output")
    parser.add_argument("-w", "--weather", action="store_true", help="weather example")
    parser.add_argument("-m", "--memory", action="store_true", help="multi-turn")
    parsed_args = parser.parse_args()
    # INFO: https://python.langchain.com/api_reference/community/tools/langchain_community.tools.tavily_search.tool.TavilySearchResults.html
    search = TavilySearchResults(max_results=2)
    tools = [search]
    memory = MemorySaver()
    model = ChatAnthropic(
        model_name="claude-3-7-sonnet-20250219", timeout=10, stop=None
    )
    if parsed_args.weather:
        weather(model, tools)
    if parsed_args.memory:
        multi_turn(model, tools, memory)


if __name__ == "__main__":
    main()
