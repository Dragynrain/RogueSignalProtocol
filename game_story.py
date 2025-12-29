#!/usr/bin/env python3
"""
Story fragment discovery and persistent progress tracking system.

This module manages narrative fragments found throughout the game:
- Discovery tracking (which fragments have been found)
- Persistent storage across game sessions (rogue_signal_progress.json)
- Fragment retrieval and ordering
- Progress queries for UI display

Key features:
- Story fragments persist across runs (not tied to save files)
- Fragments discovered in order (0, 1, 2, ...)
- Progress saved immediately on discovery
- Fragment text loaded from narrative_content.json

Delegation:
- PersistentStorage: File I/O for progress data
- get_story_fragments(): Loads fragment text from narrative_content.json
"""


# Import data loading functions
from data_loading import PersistentStorage, get_story_fragments


class StoryFragmentManager:
    """
    Manages story fragment discovery with persistent progress tracking.

    Responsibilities:
    - Track which fragments have been discovered (persists across sessions)
    - Save/load progress data (rogue_signal_progress.json)
    - Query next undiscovered fragment for placement
    - Retrieve discovered fragments for display in fragments menu

    Story fragments are separate from save files - they persist even after
    death (permadeath) or game completion. This allows players to collect
    all story pieces across multiple runs.

    Attributes:
        progress_data: Dict containing discovered fragments and version
        discovered_fragments: List of fragment indices (0, 1, 2, ...) that have been found
    """

    def __init__(self):
        # Initialize progress data with defaults (PersistentStorage moved to data_loading module)
        # Cache storage instance to avoid repeated instantiation on each fragment discovery
        self._storage = PersistentStorage()
        self.progress_data = self._storage.load_data("rogue_signal_progress.json")
        if not self.progress_data:
            self.progress_data = {"discovered_story_fragments": [], "version": "0.9.1 Beta"}
        self.discovered_fragments: list[int] = self.progress_data.get(
            "discovered_story_fragments", []
        )

    def get_next_undiscovered_fragment(self) -> int | None:
        """
        Get the next fragment index that hasn't been discovered yet.

        Used by level generator to place story fragments - only undiscovered
        fragments are placed in levels.

        Returns:
            Next undiscovered fragment index (0-based), or None if all discovered
        """
        story_fragments = get_story_fragments()
        for i, _ in enumerate(story_fragments):
            if i not in self.discovered_fragments:
                return i
        return None  # All fragments discovered

    def discover_fragment(self, fragment_index: int) -> bool:
        """
        Mark a fragment as discovered and save progress immediately.

        Validates fragment index, adds to discovered list (sorted), and
        persists to rogue_signal_progress.json. This ensures progress is
        saved even if the player dies before reaching a save point.

        Args:
            fragment_index: Index of fragment to discover (0-based)

        Returns:
            True if newly discovered, False if already discovered or invalid index
        """
        if fragment_index in self.discovered_fragments:
            return False  # Already discovered

        story_fragments = get_story_fragments()
        if fragment_index < 0 or fragment_index >= len(story_fragments):
            return False  # Invalid fragment index

        self.discovered_fragments.append(fragment_index)
        self.discovered_fragments.sort()  # Keep in order

        # Save progress immediately using cached storage instance
        self.progress_data["discovered_story_fragments"] = self.discovered_fragments
        self._storage.save_data("rogue_signal_progress.json", self.progress_data)

        return True

    def get_discovered_fragments(self) -> list[tuple[int, str]]:
        """
        Get all discovered fragments in order for display in fragments menu.

        Returns:
            List of (fragment_index, fragment_text) tuples sorted by index
        """
        story_fragments = get_story_fragments()
        fragments = []
        for fragment_index in sorted(self.discovered_fragments):
            if fragment_index < len(story_fragments):
                fragments.append((fragment_index, story_fragments[fragment_index]))
        return fragments

    def get_fragment_count(self) -> tuple[int, int]:
        """
        Get fragment counts for UI display (e.g., "Fragments: 3/10").

        Returns:
            Tuple of (discovered_count, total_count)
        """
        story_fragments = get_story_fragments()
        return len(self.discovered_fragments), len(story_fragments)
