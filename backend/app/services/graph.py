"""
Service: GraphService

Performs network analysis on financial transactions using NetworkX.
Detects complex typologies that are invisible in tabular data, such as:
- Circular transactions (funds returning to the originator)
- Suspicious hubs (highly connected nodes)
- Layering chains (long paths of fund transfers)
"""
from typing import Any, Dict, List

import networkx as nx
import pandas as pd

from app.interfaces.services import BaseService
from app.logging.logger import get_logger

logger = get_logger(__name__)


class GraphService(BaseService):
    """
    Constructs and analyses transaction graphs to detect AML typologies.
    """

    def build_graph(self, df: pd.DataFrame) -> nx.DiGraph:
        """
        Builds a directed graph from a transaction DataFrame.
        Nodes: Accounts (customer_id, receiver_id)
        Edges: Transactions (weight = amount)
        """
        G = nx.DiGraph()
        if df.empty or "sender_id" not in df.columns or "receiver_id" not in df.columns:
            return G

        for _, row in df.iterrows():
            sender = str(row["sender_id"])
            receiver = str(row["receiver_id"])
            amount = float(row["amount"])

            if G.has_edge(sender, receiver):
                G[sender][receiver]["weight"] += amount
                G[sender][receiver]["count"] += 1
            else:
                G.add_edge(sender, receiver, weight=amount, count=1)

        return G

    def detect_circular_transactions(
        self, G: nx.DiGraph, max_length: int = 5
    ) -> List[List[str]]:
        """
        Detects cycles in the graph up to max_length.
        A cycle indicates funds returning to the originator (circular flow).
        """
        if G.number_of_nodes() == 0:
            return []

        cycles = []
        try:
            # simple_cycles with length_bound prevents exponential time on dense graphs
            for cycle in nx.simple_cycles(G, length_bound=max_length):
                if len(cycle) <= max_length and len(cycle) > 2:
                    cycles.append(cycle)
                    if len(cycles) > 50:  # Cap at 50 to prevent OOM/timeouts
                        break
        except nx.NetworkXNoCycle:
            pass
        except Exception as e:
            logger.warning("cycle_detection_error", error=str(e))

        return cycles

    def find_hubs(self, G: nx.DiGraph, top_n: int = 5) -> List[Dict[str, Any]]:
        """
        Identifies highly connected nodes using PageRank and Degree Centrality.
        """
        if G.number_of_nodes() == 0:
            return []

        try:
            pagerank = nx.pagerank(G, weight="weight")
            in_degree = dict(G.in_degree())
            out_degree = dict(G.out_degree())

            # Sort by PageRank
            sorted_nodes = sorted(pagerank.items(), key=lambda x: -x[1])

            hubs = []
            for node, pr in sorted_nodes[:top_n]:
                hubs.append({
                    "node_id": node,
                    "pagerank": round(pr, 4),
                    "in_degree": in_degree.get(node, 0),
                    "out_degree": out_degree.get(node, 0),
                })
            return hubs
        except Exception as e:
            logger.warning("hub_detection_error", error=str(e))
            return []

    def detect_layering_chains(
        self, G: nx.DiGraph, min_length: int = 4
    ) -> List[List[str]]:
        """
        Detects long paths (chains) which may indicate layering.
        Approximated by finding longest simple paths between sources and sinks.
        """
        if G.number_of_nodes() == 0:
            return []

        sources = [n for n, d in G.in_degree() if d == 0]
        sinks = [n for n, d in G.out_degree() if d == 0]

        # If too many, sample to prevent performance issues
        sources = sources[:20]
        sinks = sinks[:20]

        chains = []
        for src in sources:
            for sink in sinks:
                if nx.has_path(G, src, sink):
                    try:
                        paths = list(nx.all_simple_paths(G, src, sink, cutoff=min_length + 2))
                        for p in paths:
                            if len(p) >= min_length:
                                chains.append(p)
                                if len(chains) > 20:
                                    break
                    except Exception:
                        pass
                if len(chains) > 20:
                    break
            if len(chains) > 20:
                break

        return chains

    def analyze_network(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Performs a full network analysis on the dataset.
        """
        G = self.build_graph(df)
        
        if G.number_of_nodes() == 0:
            return {
                "nodes": 0,
                "edges": 0,
                "circular_patterns": [],
                "hubs": [],
                "layering_chains": [],
            }

        cycles = self.detect_circular_transactions(G)
        hubs = self.find_hubs(G)
        chains = self.detect_layering_chains(G)

        return {
            "nodes": G.number_of_nodes(),
            "edges": G.number_of_edges(),
            "circular_patterns_count": len(cycles),
            "layering_chains_count": len(chains),
            "circular_patterns": cycles[:10],  # Return top 10 for payload size limits
            "hubs": hubs,
            "layering_chains": chains[:10],
        }
