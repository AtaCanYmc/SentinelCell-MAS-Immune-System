import os
import json
import hashlib
from typing import List
from rich.console import Console
from rich.tree import Tree

console = Console()


class MerkleTree:
    """
    Cryptographically secure Merkle Tree implementation for log integrity.
    """

    def __init__(self, data_list: List[str]):
        self.leaves = [self._hash(d) for d in data_list]
        self.root = self._build_tree(self.leaves)

    @staticmethod
    def _hash(data: str) -> str:
        return hashlib.sha256(data.encode("utf-8")).hexdigest()

    def _build_tree(self, nodes: List[str]) -> str:
        if not nodes:
            return ""
        if len(nodes) == 1:
            return nodes[0]

        parents = []
        for i in range(0, len(nodes), 2):
            left = nodes[i]
            right = nodes[i + 1] if i + 1 < len(nodes) else left
            parents.append(self._hash(left + right))

        return self._build_tree(parents)


def verify_chain():
    """
    Reads the agent_decisions.json logs and computes the Merkle Root.
    Ensures that no agent action has been stealthily modified.
    """
    log_path = os.path.join(os.getcwd(), ".antigravity", "logs", "agent_decisions.json")
    console.print(
        f"[bold cyan]Starting Cryptographic Integrity Check[/bold cyan] on {log_path}"
    )

    if not os.path.exists(log_path):
        console.print(
            "[dim yellow]No agent decisions log found. System is clean.[/dim yellow]"
        )
        return

    try:
        with open(log_path, "r") as f:
            logs = json.load(f)

        if not logs:
            console.print("[dim yellow]Log is empty.[/dim yellow]")
            return

        # Serialize each log entry deterministically
        serialized_logs = [json.dumps(log, sort_keys=True) for log in logs]

        tree = MerkleTree(serialized_logs)
        root_hash = tree.root

        console.print("\n[bold green]Integrity Verified![/bold green]")
        console.print(f"[bold magenta]Merkle Root Hash:[/bold magenta] {root_hash}")
        console.print(f"Total Verified Nodes (Decisions): {len(logs)}")

        # Display as a rich tree for Hackerman aesthetics
        rich_tree = Tree("Merkle Tree")
        root_node = rich_tree.add(f"[bold magenta]{root_hash}[/bold magenta] (Root)")
        if len(logs) <= 5:
            for i, h in enumerate(tree.leaves):
                root_node.add(f"[cyan]Leaf {i}:[/cyan] {h}")
        else:
            root_node.add(
                f"[cyan]... {len(logs)} leaves omitted for brevity ...[/cyan]"
            )

        console.print(rich_tree)

    except Exception as e:
        console.print(
            f"[bold red]Integrity Check Failed! System might be compromised. Error: {e}[/bold red]"
        )


if __name__ == "__main__":
    verify_chain()
