"""
core/state.py
Shared LangGraph state definition.

PARALLEL EXECUTION NOTE:
  When multiple agents run in parallel, ALL state fields they touch
  need Annotated reducers — even read-only fields like query.
  LangGraph sees each agent returning the full state dict, so even
  unchanged fields cause conflicts if not handled with reducers.

  Solution: use keep_last reducer for all scalar fields so parallel
  writes are resolved by taking the last (identical) value.
"""

from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages


def merge_dicts(a: dict, b: dict) -> dict:
    """
    Reducer for domain_responses.
    Merges parallel agent responses into one dict.
    {"licensing": "..."} + {"onprem": "..."} = {"licensing": "...", "onprem": "..."}
    """
    merged = dict(a or {})
    merged.update(b or {})
    return merged


def keep_last(a, b):
    """
    Reducer for scalar fields written by parallel agents.
    Both agents write the same value — just keep whichever arrives last.
    """
    return b if b is not None and b != "" else a


def keep_last_bool(a, b):
    """Keep last value for boolean fields."""
    return b if b is not None else a


def keep_last_list(a, b):
    """Keep last value for list fields."""
    return b if b else a


class AgentState(TypedDict):
    """
    Shared state flowing through the entire LangGraph.
    All fields use explicit reducers to support parallel agent execution.
    """
    messages:         Annotated[list, add_messages]
    query:            Annotated[str,  keep_last]
    domains:          Annotated[list, keep_last_list]
    domain_responses: Annotated[dict, merge_dicts]
    response:         Annotated[str,  keep_last]
    routing_reason:   Annotated[str,  keep_last]
    is_multi_domain:  Annotated[bool, keep_last_bool]