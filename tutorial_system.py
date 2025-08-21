#!/usr/bin/env python3
"""
Tutorial System for Rogue Signal Protocol
Implements the dynamic tutorial system described in the design document
"""

from typing import Dict, List, Callable, Optional, Any
from dataclasses import dataclass
from enum import Enum

class TutorialCondition(Enum):
    """Tutorial progression conditions"""
    MOVEMENT_COMPLETED = "movement_completed"
    SHADOW_ENTERED = "shadow_entered"
    ENEMY_OBSERVED = "enemy_observed"
    EXPLOIT_USED = "exploit_used"
    STEALTH_ATTACK = "stealth_attack"
    DETECTION_EXPERIENCED = "detection_experienced"
    GATEWAY_REACHED = "gateway_reached"
    TURN_COUNT = "turn_count"
    CPU_RECOVERED = "cpu_recovered"
    HEAT_GENERATED = "heat_generated"

@dataclass
class TutorialStep:
    """Individual tutorial step"""
    title: str
    content: str
    conditions: List[TutorialCondition]
    condition_values: Dict[str, Any]  # Additional condition parameters
    completion_message: str
    hints: List[str]
    required: bool = True
    timeout_turns: Optional[int] = None

class TutorialSystem:
    """
    Manages the dynamic tutorial progression system
    Tracks player actions and provides contextual guidance
    """
    
    def __init__(self, game_instance):
        self.game = game_instance
        self.current_step = 0
        self.completed_steps = set()
        self.active = True
        self.player_stats = {
            'moves_made': 0,
            'shadows_entered': 0,
            'enemies_observed': 0,
            'exploits_used': 0,
            'stealth_attacks': 0,
            'times_detected': 0,
            'cpu_recovered': 0,
            'heat_generated': 0
        }
        
        self.tutorial_steps = self._initialize_tutorial_steps()
        
    def _initialize_tutorial_steps(self) -> List[TutorialStep]:
        """Initialize the tutorial step sequence"""
        return [
            TutorialStep(
                title="Welcome to Rogue Signal Protocol",
                content="You are a hacker's consciousness trapped in cyberspace. Your goal is to navigate this network using stealth and reach the gateway (>) without being detected.",
                conditions=[],
                condition_values={},
                completion_message="Tutorial initialized. Let's begin your training.",
                hints=["Look around the screen to familiarize yourself with the interface"]
            ),
            
            TutorialStep(
                title="Basic Movement",
                content="Use WASD keys or arrow keys to move through the network grid. Each move takes one turn, and all enemies will move after you do. Try moving around to get familiar with the controls.",
                conditions=[TutorialCondition.MOVEMENT_COMPLETED],
                condition_values={'moves_required': 5},
                completion_message="Good! You've learned basic movement.",
                hints=[
                    "Press W/↑ to move up",
                    "Press S/↓ to move down", 
                    "Press A/← to move left",
                    "Press D/→ to move right",
                    "Make at least 5 moves to continue"
                ]
            ),
            
            TutorialStep(
                title="Shadows and Stealth",
                content="Dark areas marked with ◉ are shadow zones that provide complete concealment. While in shadows, enemies cannot see you even if you're in their vision range. Find and enter a shadow zone.",
                conditions=[TutorialCondition.SHADOW_ENTERED],
                condition_values={},
                completion_message="Excellent! You're now hidden in the shadows.",
                hints=[
                    "Look for ◉ symbols on the map",
                    "Move into a shadow zone to hide",
                    "Shadows provide complete invisibility"
                ]
            ),
            
            TutorialStep(
                title="Enemy Vision and Detection",
                content="Security processes (enemies) have vision ranges shown as colored circles. The 's' is a Scanner with short-range vision. Observe how the vision range is displayed and stay out of it.",
                conditions=[TutorialCondition.ENEMY_OBSERVED],
                condition_values={},
                completion_message="You understand enemy vision ranges. Stay alert!",
                hints=[
                    "Orange circles show enemy vision",
                    "Different enemies have different vision ranges",
                    "Stay outside vision ranges to remain undetected"
                ]
            ),
            
            TutorialStep(
                title="Using Exploits",
                content="Press 1, 2, or 3 to use loaded exploits. Try using Network Scan (key 2) to reveal enemy information and patrol routes. This will help you understand the tactical situation.",
                conditions=[TutorialCondition.EXPLOIT_USED],
                condition_values={},
                completion_message="Network Scan activated! Notice how it reveals additional information.",
                hints=[
                    "Press 2 to use Network Scan",
                    "Exploits consume heat and RAM",
                    "Some exploits require targeting"
                ]
            ),
            
            TutorialStep(
                title="Resource Management",
                content="Watch your Heat and CPU levels. Heat increases when using exploits and decreases over time. CPU is your health - if it reaches 0, you're eliminated. Try generating some heat, then wait for it to cool down.",
                conditions=[TutorialCondition.HEAT_GENERATED],
                condition_values={'heat_required': 15},
                completion_message="You understand resource management. Heat will cool down over time.",
                hints=[
                    "Use exploits to generate heat",
                    "Wait (Space bar) to let heat cool down",
                    "CPU is restored by eliminating enemies"
                ]
            ),
            
            TutorialStep(
                title="Detection System", 
                content="Your detection level rises when enemies see you. If it gets too high, the Admin Avatar will spawn to hunt you down. Try getting detected briefly (but stay safe!), then hide in shadows to understand the system.",
                conditions=[TutorialCondition.DETECTION_EXPERIENCED],
                condition_values={},
                completion_message="You've experienced the detection system. Be more careful in real infiltrations!",
                hints=[
                    "Walk into an enemy's vision range briefly",
                    "Watch your detection level rise",
                    "Hide in shadows to break line of sight",
                    "High detection spawns the Admin Avatar"
                ]
            ),
            
            TutorialStep(
                title="Complete the Infiltration",
                content="Now that you understand the basics, navigate to the yellow gateway (>) to complete the tutorial. Use stealth, observe enemy patterns, and stay in the shadows. Remember: patience and observation are key to successful infiltration.",
                conditions=[TutorialCondition.GATEWAY_REACHED],
                condition_values={},
                completion_message="Tutorial complete! You're ready for real network infiltrations.",
                hints=[
                    "Find the yellow > symbol",
                    "Use shadows to avoid detection",
                    "Plan your route carefully",
                    "Take your time - rushing leads to detection"
                ]
            )
        ]
    
    def update(self, action_type: str, **kwargs):
        """Update tutorial progress based on player actions"""
        if not self.active or self.current_step >= len(self.tutorial_steps):
            return
        
        # Update player statistics
        self._update_stats(action_type, **kwargs)
        
        # Check if current step conditions are met
        current_step = self.tutorial_steps[self.current_step]
        if self._check_step_completion(current_step):
            self._complete_step()
    
    def _update_stats(self, action_type: str, **kwargs):
        """Update internal player statistics for tutorial tracking"""
        if action_type == "move":
            self.player_stats['moves_made'] += 1
        elif action_type == "enter_shadow":
            self.player_stats['shadows_entered'] += 1
        elif action_type == "observe_enemy":
            self.player_stats['enemies_observed'] += 1
        elif action_type == "use_exploit":
            self.player_stats['exploits_used'] += 1
        elif action_type == "stealth_attack":
            self.player_stats['stealth_attacks'] += 1
        elif action_type == "detected":
            self.player_stats['times_detected'] += 1
        elif action_type == "recover_cpu":
            self.player_stats['cpu_recovered'] += kwargs.get('amount', 0)
        elif action_type == "generate_heat":
            self.player_stats['heat_generated'] += kwargs.get('amount', 0)
    
    def _check_step_completion(self, step: TutorialStep) -> bool:
        """Check if the current tutorial step is completed"""
        for condition in step.conditions:
            if condition == TutorialCondition.MOVEMENT_COMPLETED:
                required_moves = step.condition_values.get('moves_required', 5)
                if self.player_stats['moves_made'] < required_moves:
                    return False
                    
            elif condition == TutorialCondition.SHADOW_ENTERED:
                if self.player_stats['shadows_entered'] == 0:
                    return False
                    
            elif condition == TutorialCondition.ENEMY_OBSERVED:
                if self.player_stats['enemies_observed'] == 0:
                    return False
                    
            elif condition == TutorialCondition.EXPLOIT_USED:
                if self.player_stats['exploits_used'] == 0:
                    return False
                    
            elif condition == TutorialCondition.STEALTH_ATTACK:
                if self.player_stats['stealth_attacks'] == 0:
                    return False
                    
            elif condition == TutorialCondition.DETECTION_EXPERIENCED:
                if self.player_stats['times_detected'] == 0:
                    return False
                    
            elif condition == TutorialCondition.HEAT_GENERATED:
                required_heat = step.condition_values.get('heat_required', 10)
                if self.player_stats['heat_generated'] < required_heat:
                    return False
                    
            elif condition == TutorialCondition.GATEWAY_REACHED:
                # This is checked externally by the game when player reaches gateway
                return False
                
            elif condition == TutorialCondition.TURN_COUNT:
                required_turns = step.condition_values.get('turns_required', 10)
                if self.game.turn < required_turns:
                    return False
        
        return True
    
    def _complete_step(self):
        """Complete the current tutorial step and advance"""
        if self.current_step < len(self.tutorial_steps):
            step = self.tutorial_steps[self.current_step]
            self.completed_steps.add(self.current_step)
            self.game.add_message(f"Tutorial: {step.completion_message}")
            self.current_step += 1
            
            # Show next step if available
            if self.current_step < len(self.tutorial_steps):
                self._show_current_step()
            else:
                self._complete_tutorial()
    
    def _show_current_step(self):
        """Display the current tutorial step"""
        if self.current_step < len(self.tutorial_steps):
            step = self.tutorial_steps[self.current_step]
            self.game.add_message(f"Tutorial: {step.title}")
            self.game.add_message(step.content)
    
    def _complete_tutorial(self):
        """Complete the entire tutorial system"""
        self.active = False
        self.game.tutorial_completed = True
        self.game.add_message("Tutorial completed! You're ready for real infiltrations.")
    
    def get_current_hints(self) -> List[str]:
        """Get hints for the current tutorial step"""
        if self.current_step < len(self.tutorial_steps):
            return self.tutorial_steps[self.current_step].hints
        return []
    
    def get_progress_info(self) -> Dict[str, Any]:
        """Get current tutorial progress information"""
        if not self.active or self.current_step >= len(self.tutorial_steps):
            return {"active": False, "completed": True}
        
        current_step = self.tutorial_steps[self.current_step]
        progress = {
            "active": True,
            "completed": False,
            "step": self.current_step + 1,
            "total_steps": len(self.tutorial_steps),
            "title": current_step.title,
            "content": current_step.content,
            "hints": current_step.hints,
            "conditions_met": self._get_conditions_status(current_step)
        }
        
        return progress
    
    def _get_conditions_status(self, step: TutorialStep) -> Dict[str, bool]:
        """Get status of conditions for current step"""
        status = {}
        
        for condition in step.conditions:
            if condition == TutorialCondition.MOVEMENT_COMPLETED:
                required = step.condition_values.get('moves_required', 5)
                status['movement'] = self.player_stats['moves_made'] >= required
            elif condition == TutorialCondition.SHADOW_ENTERED:
                status['shadow_entered'] = self.player_stats['shadows_entered'] > 0
            elif condition == TutorialCondition.ENEMY_OBSERVED:
                status['enemy_observed'] = self.player_stats['enemies_observed'] > 0
            elif condition == TutorialCondition.EXPLOIT_USED:
                status['exploit_used'] = self.player_stats['exploits_used'] > 0
            elif condition == TutorialCondition.DETECTION_EXPERIENCED:
                status['detection_experienced'] = self.player_stats['times_detected'] > 0
            elif condition == TutorialCondition.HEAT_GENERATED:
                required = step.condition_values.get('heat_required', 10)
                status['heat_generated'] = self.player_stats['heat_generated'] >= required
        
        return status
    
    def force_complete_step(self):
        """Force complete current step (for debugging/testing)"""
        if self.active and self.current_step < len(self.tutorial_steps):
            self._complete_step()
    
    def skip_tutorial(self):
        """Skip the entire tutorial"""
        self.active = False
        self.game.tutorial_completed = True
        self.current_step = len(self.tutorial_steps)
        self.game.add_message("Tutorial skipped.")
    
    def restart_tutorial(self):
        """Restart the tutorial from the beginning"""
        self.current_step = 0
        self.completed_steps.clear()
        self.active = True
        self.game.tutorial_completed = False
        self.player_stats = {
            'moves_made': 0,
            'shadows_entered': 0,
            'enemies_observed': 0,
            'exploits_used': 0,
            'stealth_attacks': 0,
            'times_detected': 0,
            'cpu_recovered': 0,
            'heat_generated': 0
        }
        self._show_current_step()


# Integration functions for the main game
def integrate_tutorial_with_game(game_instance):
    """Integrate tutorial system with main game instance"""
    game_instance.tutorial_system = TutorialSystem(game_instance)
    
    # Override certain game methods to trigger tutorial updates
    original_move_player = game_instance.move_player
    original_process_turn = game_instance.process_turn
    original_use_exploit = game_instance.use_exploit
    original_attack_enemy = game_instance.attack_enemy
    
    def tutorial_move_player(dx, dy):
        if game_instance.tutorial_system.active:
            game_instance.tutorial_system.update("move")
            
            # Check if player entered shadow
            new_x = game_instance.player.x + dx
            new_y = game_instance.player.y + dy
            if (game_instance.game_map.is_valid_position(new_x, new_y) and
                game_instance.game_map.is_shadow(new_x, new_y)):
                game_instance.tutorial_system.update("enter_shadow")
        
        return original_move_player(dx, dy)
    
    def tutorial_process_turn():
        if game_instance.tutorial_system.active:
            # Check if player can see any enemies (for observation tutorial)
            player_vision = game_instance.player.get_vision_range()
            for enemy in game_instance.enemies:
                distance = max(abs(enemy.x - game_instance.player.x), 
                             abs(enemy.y - game_instance.player.y))
                if distance <= player_vision:
                    game_instance.tutorial_system.update("observe_enemy")
                    break
        
        return original_process_turn()
    
    def tutorial_use_exploit(exploit_key):
        if game_instance.tutorial_system.active:
            game_instance.tutorial_system.update("use_exploit")
            
            # Check heat generation
            if exploit_key in EXPLOITS:
                heat_cost = EXPLOITS[exploit_key].heat
                game_instance.tutorial_system.update("generate_heat", amount=heat_cost)
        
        return original_use_exploit(exploit_key)
    
    def tutorial_attack_enemy(enemy):
        if game_instance.tutorial_system.active:
            # Check if it's a stealth attack
            if (enemy.state == EnemyState.UNAWARE and 
                (game_instance.game_map.is_shadow(game_instance.player.x, game_instance.player.y) or
                 game_instance.player.is_invisible())):
                game_instance.tutorial_system.update("stealth_attack")
        
        return original_attack_enemy(enemy)
    
    # Replace methods with tutorial-aware versions
    game_instance.move_player = tutorial_move_player
    game_instance.process_turn = tutorial_process_turn
    game_instance.use_exploit = tutorial_use_exploit
    game_instance.attack_enemy = tutorial_attack_enemy
    
    # Start tutorial
    if game_instance.level == 0:  # Tutorial level
        game_instance.tutorial_system._show_current_step()


if __name__ == "__main__":
    # Test the tutorial system
    print("Tutorial System Test")
    
    # Mock game instance for testing
    class MockGame:
        def __init__(self):
            self.turn = 0
            self.level = 0
            self.tutorial_completed = False
            self.messages = []
            
        def add_message(self, message):
            print(f"Game Message: {message}")
            self.messages.append(message)
    
    # Test tutorial progression
    mock_game = MockGame()
    tutorial = TutorialSystem(mock_game)
    
    print("Testing tutorial step progression...")
    
    # Test movement
    for i in range(6):
        tutorial.update("move")
        print(f"Move {i+1}: Step {tutorial.current_step}")
    
    # Test shadow entry
    tutorial.update("enter_shadow")
    print(f"Shadow entered: Step {tutorial.current_step}")
    
    # Test enemy observation
    tutorial.update("observe_enemy")
    print(f"Enemy observed: Step {tutorial.current_step}")
    
    # Test exploit usage
    tutorial.update("use_exploit")
    tutorial.update("generate_heat", amount=20)
    print(f"Exploit used: Step {tutorial.current_step}")
    
    # Test detection
    tutorial.update("detected")
    print(f"Detection experienced: Step {tutorial.current_step}")
    
    print(f"\nTutorial Progress: {tutorial.get_progress_info()}")
