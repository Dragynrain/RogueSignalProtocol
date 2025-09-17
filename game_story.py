#!/usr/bin/env python3
"""
Story fragment management system.
Extracted from RogueSignalProtocol.py for better organization.
"""

from typing import List, Tuple, Optional

# Import data loading functions
from data_loading import PersistentStorage, get_story_fragments


class StoryFragmentManager:
    """Manages story fragment discovery and display."""
    
    def __init__(self):
        # Initialize progress data with defaults (PersistentStorage moved to data_loading module)
        storage = PersistentStorage()
        self.progress_data = storage.load_data("rogue_signal_progress.json")
        if not self.progress_data:
            self.progress_data = {
                "discovered_story_fragments": [],
                "version": "dev"
            }
        self.discovered_fragments: List[int] = self.progress_data.get("discovered_story_fragments", [])
    
    def get_next_undiscovered_fragment(self) -> Optional[int]:
        """Get the next fragment index that hasn't been discovered yet."""
        story_fragments = get_story_fragments()
        for i in range(len(story_fragments)):
            if i not in self.discovered_fragments:
                return i
        return None  # All fragments discovered
    
    def discover_fragment(self, fragment_index: int) -> bool:
        """Discover a new story fragment and save progress."""
        if fragment_index in self.discovered_fragments:
            return False  # Already discovered
            
        story_fragments = get_story_fragments()
        if fragment_index < 0 or fragment_index >= len(story_fragments):
            return False  # Invalid fragment index
            
        self.discovered_fragments.append(fragment_index)
        self.discovered_fragments.sort()  # Keep in order
        
        # Save progress immediately
        self.progress_data["discovered_story_fragments"] = self.discovered_fragments
        storage = PersistentStorage()
        storage.save_data("rogue_signal_progress.json", self.progress_data)
        
        return True
    
    def get_discovered_fragments(self) -> List[Tuple[int, str]]:
        """Get all discovered fragments in order."""
        story_fragments = get_story_fragments()
        fragments = []
        for fragment_index in sorted(self.discovered_fragments):
            if fragment_index < len(story_fragments):
                fragments.append((fragment_index, story_fragments[fragment_index]))
        return fragments
    
    def get_fragment_count(self) -> Tuple[int, int]:
        """Get (discovered_count, total_count) for UI display."""
        story_fragments = get_story_fragments()
        return len(self.discovered_fragments), len(story_fragments)