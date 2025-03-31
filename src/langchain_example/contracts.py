from importlib.abc import Traversable
from typing import Any, Final

from ens.ens import HexStr
from pydantic import BaseModel, Field
from web3.eth import Contract
from web3 import Web3
from solcx import compile_source

PROPOSALS = ["hello", "world", "sigmaboy"]


class Proposal(BaseModel):
    name: str = Field(description="name of the proposal")
    votes: int = Field(description="number of votes for proposal")


def contract_string() -> str:
    import importlib.resources as pkg_resources
    from langchain_example import resources

    contract_source = pkg_resources.files(resources) / "Voting.sol"
    with contract_source.open("r") as fp:
        return fp.read()


def str2bytes32(s: str) -> bytes:
    s_bytes = s.encode("ascii")[:32]
    padding = b"\x00" * (32 - len(s_bytes))
    return Web3.to_bytes(hexstr=HexStr((s_bytes + padding).hex()))


def proposal_conversion(proposal: tuple[bytes, int]) -> Proposal:
    pbytes, pint = proposal
    return Proposal(name=pbytes.rstrip(b"\x00").decode("ascii"), votes=pint)


def voting_contract(w3: Web3) -> Contract:
    compiled_sol = compile_source(
        contract_string(),
        output_values=["abi", "bin"],
    )
    contract_id, contract_iface = compiled_sol.popitem()
    example_abi = contract_iface["abi"]
    example_byt = contract_iface["bin"]
    example_contract = w3.eth.contract(abi=example_abi, bytecode=example_byt)
    tx_hash = example_contract.constructor(
        proposalNames=[str2bytes32(s) for s in PROPOSALS]
    ).transact()
    tx_receipt: Any = w3.eth.wait_for_transaction_receipt(tx_hash)
    return w3.eth.contract(address=tx_receipt.contractAddress, abi=example_abi)
