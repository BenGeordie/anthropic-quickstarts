#!/usr/bin/env python3
"""
Script to sort ASSISTANT blocks in chat.md by elapsed time in descending order.
Only sorts ASSISTANT blocks that have elapsed times and are NOT "Tool Use" blocks.
Groups related TOOL blocks and Tool Use blocks with their corresponding ASSISTANT blocks.
"""

import os
import re
import sys
from typing import List, Optional


def parse_elapsed_time(content: str) -> Optional[float]:
    """Extract elapsed time from the beginning of ASSISTANT block content."""
    # Look for pattern like "(2.34 sec.)" at the beginning of the content
    match = re.match(r"\((\d+\.?\d*)\s*sec\.\)", content.strip())
    if match:
        return float(match.group(1))
    return None


def is_tool_use_block(content: str) -> bool:
    """Check if an ASSISTANT block is a Tool Use block."""
    return content.strip().startswith("**Tool Use:**")


def parse_chat_file(file_path: str) -> List[dict]:
    """Parse the chat.md file into structured blocks."""
    with open(file_path, encoding="utf-8") as f:
        content = f.read()

    # Split by block separators
    blocks = content.split("\n---\n")

    parsed_blocks = []
    for i, block in enumerate(blocks):
        block = block.strip()
        if not block:
            continue

        lines = block.split("\n")
        if not lines:
            continue

        # Identify block type
        first_line = lines[0].strip()
        if first_line.startswith("## USER"):
            block_type = "USER"
        elif first_line.startswith("## ASSISTANT"):
            block_type = "ASSISTANT"
        elif first_line.startswith("## TOOL"):
            block_type = "TOOL"
        else:
            block_type = "OTHER"

        # Get the content (everything after the header and timestamp)
        content_lines = []
        timestamp_line = None

        for j, line in enumerate(lines[1:], 1):
            if line.strip().startswith("*") and line.strip().endswith("*") and j == 1:
                timestamp_line = line
            elif j > 1 or not timestamp_line:
                content_lines.append(line)

        block_content = "\n".join(content_lines)

        parsed_blocks.append(
            {
                "type": block_type,
                "header": first_line,
                "timestamp": timestamp_line,
                "content": block_content,
                "original_index": i,
                "raw_block": block,
            }
        )

    return parsed_blocks


def group_related_blocks(blocks: list[dict]) -> list[tuple[float, list[dict]]]:
    """Group blocks that should stay together when sorting."""
    groups = []
    i = 0

    while i < len(blocks):
        current_block = blocks[i]

        if current_block["type"] == "ASSISTANT":
            # Check if this is a sortable ASSISTANT block (has elapsed time and is not Tool Use)
            elapsed_time = parse_elapsed_time(current_block["content"])
            is_tool_use = is_tool_use_block(current_block["content"])

            if elapsed_time is not None and not is_tool_use:
                # This is a sortable ASSISTANT block
                group = (elapsed_time, [])

                # Check if preceded by a TOOL block
                if i > 0 and blocks[i - 1]["type"] == "TOOL":
                    group[1].append(blocks[i - 1])

                # Add the ASSISTANT block
                group[1].append(current_block)

                # Check if followed by Tool Use ASSISTANT block
                if (
                    i + 1 < len(blocks)
                    and blocks[i + 1]["type"] == "ASSISTANT"
                    and is_tool_use_block(blocks[i + 1]["content"])
                ):
                    group[1].append(blocks[i + 1])

                groups.append(group)
        i += 1

    return groups


def blocks_to_text(groups: list[tuple[float, list[dict]]]) -> str:
    """Convert grouped blocks back to text format."""
    result_parts = []

    for group in groups:
        result_parts.append(f"# {group[0]:.2f} sec.")
        for block in group[1]:
            result_parts.append(block["content"])

    return "\n\n---\n\n".join(result_parts)


def main():
    if len(sys.argv) != 2:
        print("Usage: python sort_chat.py <path_to_chat.md>")
        sys.exit(1)

    input_file = sys.argv[1]

    if not os.path.exists(input_file):
        print(f"Error: File {input_file} does not exist")
        sys.exit(1)

    # Create output file path
    input_dir = os.path.dirname(input_file)
    output_file = os.path.join(input_dir, "chat-sorted.md")

    try:
        # Parse the chat file
        blocks = parse_chat_file(input_file)

        # Group related blocks
        groups = group_related_blocks(blocks)

        # Sort groups by elapsed time
        sorted_groups = sorted(groups, key=lambda group: group[0], reverse=True)

        # Convert back to text
        sorted_text = blocks_to_text(sorted_groups)

        # Write to output file
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(sorted_text)

        print(f"Sorted chat saved to: {output_file}")

        print(f"Sorted {len(sorted_groups)} ASSISTANT blocks by elapsed time")

    except Exception as e:
        print(f"Error processing file: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
