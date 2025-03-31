from typing import Any, Final
from langchain_anthropic import ChatAnthropic
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.messages import AIMessageChunk, HumanMessage
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent
from dotenv import load_dotenv
from web3 import Web3, EthereumTesterProvider

from argparse import ArgumentParser

from pydantic import BaseModel, Field

from langchain_example.const import MODEL_NAME
from langchain_example.contracts import Proposal, proposal_conversion, voting_contract

global w3
global vote_contract

w3 = Web3(EthereumTesterProvider())
vote_contract = voting_contract(w3)


class CalculatorInput(BaseModel):
    a: int = Field(description="first number")
    b: int = Field(description="second number")


@tool("get_proposals", return_direct=False)
def get_proposals() -> dict[int, str]:
    """
    Get proposals from the smart contract
    Returns: dictionary key pairs of proposal indexes and name and vote counts
    """
    raw_proposals: list[tuple[bytes, int]] = (
        vote_contract.functions.getProposals().call()
    )
    proposals = [proposal_conversion(p) for p in raw_proposals]
    return {i: f"{p.name} with {p.votes} votes!" for i, p in enumerate(proposals)}


@tool("supermultiply", args_schema=CalculatorInput, return_direct=True)
def supermultiply(a: int, b: int) -> float:
    """
    Supermultiply two numbers.
    """
    return (2 * a) / (b + 10)


def multi_turn(
    model: ChatAnthropic, tools: list[TavilySearchResults], memory: MemorySaver
):
    agent_executor = create_react_agent(model, tools, checkpointer=memory)
    config = RunnableConfig(
        configurable={"thread_id": "08c55a1c-eddd-40e6-9979-593e0326ad7b"}
    )
    step: Any
    metadata: Any
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


def custom_tool(model: ChatAnthropic, tools: list[Any]):
    agent_executor = create_react_agent(model, tools)
    for chunk in agent_executor.stream(
        {"messages": [HumanMessage(content="what is the supermultiply of 2 and 3??")]},
        stream_mode="messages",
    ):
        print(chunk)


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
    parser.add_argument("-c", "--custom", action="store_true", help="custom tool")
    parsed_args = parser.parse_args()
    # INFO: https://python.langchain.com/api_reference/community/tools/langchain_community.tools.tavily_search.tool.TavilySearchResults.html
    search = TavilySearchResults(max_results=2)
    tools = [search]
    memory = MemorySaver()
    model = ChatAnthropic(model_name=MODEL_NAME, timeout=10, stop=None)
    if parsed_args.weather:
        weather(model, tools)
    if parsed_args.memory:
        multi_turn(model, tools, memory)
    if parsed_args.custom:
        custom_tool(model, tools + [supermultiply])


if __name__ == "__main__":
    main()
