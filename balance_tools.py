#!/usr/bin/env python3
"""
Rogue Signal Protocol - Balance Analysis Tools
Utilities for analyzing and validating game balance.
"""

import json
import os
import sys
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass
import matplotlib.pyplot as plt
import numpy as np

@dataclass
class BalanceIssue:
    """Represents a potential balance issue."""
    severity: str  # "warning", "error", "info"
    category: str
    description: str
    affected_items: List[str]
    suggested_fix: str

class BalanceAnalyzer:
    """Analyzes game balance from JSON data files."""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.exploits_data = {}
        self.enemies_data = {}
        self.classes_data = {}
        self.networks_data = {}
        self.balance_data = {}
        self.issues: List[BalanceIssue] = []
        
    def load_data(self) -> bool:
        """Load all JSON data files."""
        try:
            with open(f"{self.data_dir}/exploits.json", 'r') as f:
                self.exploits_data = json.load(f)
            with open(f"{self.data_dir}/enemies.json", 'r') as f:
                self.enemies_data = json.load(f)
            with open(f"{self.data_dir}/classes.json", 'r') as f:
                self.classes_data = json.load(f)
            with open(f"{self.data_dir}/networks.json", 'r') as f:
                self.networks_data = json.load(f)
            with open(f"{self.data_dir}/balance.json", 'r') as f:
                self.balance_data = json.load(f)
            return True
        except FileNotFoundError as e:
            print(f"Error loading data files: {e}")
            return False
    
    def analyze_all(self) -> List[BalanceIssue]:
        """Run all balance analysis checks."""
        self.issues = []
        
        self.analyze_exploit_balance()
        self.analyze_enemy_progression()
        self.analyze_class_balance()
        self.analyze_network_difficulty()
        self.analyze_economy_balance()
        self.analyze_ram_constraints()
        self.analyze_heat_economy()
        
        return self.issues
    
    def analyze_exploit_balance(self) -> None:
        """Analyze exploit power levels and costs."""
        print("Analyzing exploit balance...")
        
        # Extract all exploits
        all_exploits = []
        for category in self.exploits_data.values():
            for exploit_id, exploit in category.items():
                exploit['id'] = exploit_id
                exploit['category'] = category
                all_exploits.append(exploit)
        
        # Check damage per heat ratio
        for exploit in all_exploits:
            if 'damage_base' in exploit and 'heat_generated' in exploit:
                damage = exploit['damage_base']
                heat = exploit['heat_generated']
                
                if heat == 0:
                    self.issues.append(BalanceIssue(
                        "warning", "exploit_balance",
                        f"Exploit {exploit['id']} has no heat cost",
                        [exploit['id']],
                        "Add appropriate heat cost"
                    ))
                else:
                    dph_ratio = damage / heat
                    
                    # Flag exploits with unusual damage/heat ratios
                    if dph_ratio > 3.0:
                        self.issues.append(BalanceIssue(
                            "warning", "exploit_balance",
                            f"Exploit {exploit['id']} has high damage/heat ratio: {dph_ratio:.2f}",
                            [exploit['id']],
                            "Consider increasing heat cost or reducing damage"
                        ))
                    elif dph_ratio < 1.0:
                        self.issues.append(BalanceIssue(
                            "info", "exploit_balance",
                            f"Exploit {exploit['id']} has low damage/heat ratio: {dph_ratio:.2f}",
                            [exploit['id']],
                            "Consider decreasing heat cost or increasing damage"
                        ))
        
        # Check RAM costs
        ram_costs = [e.get('ram_cost', 0) for e in all_exploits]
        max_ram = max(self.classes_data[c]['stats']['max_ram'] 
                     for c in self.classes_data)
        
        for exploit in all_exploits:
            ram_cost = exploit.get('ram_cost', 0)
            if ram_cost > max_ram:
                self.issues.append(BalanceIssue(
                    "error", "exploit_balance",
                    f"Exploit {exploit['id']} RAM cost ({ram_cost}) exceeds max possible RAM ({max_ram})",
                    [exploit['id']],
                    f"Reduce RAM cost to {max_ram} or below"
                ))
    
    def analyze_enemy_progression(self) -> None:
        """Analyze enemy power progression across levels."""
        print("Analyzing enemy progression...")
        
        level_enemies = {}
        
        # Group enemies by level
        for level_key, enemies in self.enemies_data.items():
            if level_key.startswith('level_'):
                level_num = int(level_key.split('_')[1])
                level_enemies[level_num] = enemies
        
        # Check HP progression
        level_hp_ranges = {}
        for level, enemies in level_enemies.items():
            hp_values = [enemy['hp'] for enemy in enemies.values()]
            level_hp_ranges[level] = (min(hp_values), max(hp_values), np.mean(hp_values))
        
        # Validate progression
        for level in sorted(level_hp_ranges.keys())[:-1]:
            current_max = level_hp_ranges[level][1]
            next_min = level_hp_ranges[level + 1][0]
            
            if current_max >= next_min:
                self.issues.append(BalanceIssue(
                    "warning", "enemy_progression",
                    f"Level {level} max HP ({current_max}) >= Level {level+1} min HP ({next_min})",
                    [f"level_{level}", f"level_{level+1}"],
                    "Adjust HP values to ensure clear progression"
                ))
        
        # Check damage progression
        for level, enemies in level_enemies.items():
            damage_values = [enemy['damage'] for enemy in enemies.values()]
            avg_damage = np.mean(damage_values)
            
            # Check for enemies with 0 damage (except honeypots)
            for enemy_id, enemy in enemies.items():
                if enemy['damage'] == 0 and 'honeypot' not in enemy_id.lower():
                    self.issues.append(BalanceIssue(
                        "info", "enemy_progression", 
                        f"Enemy {enemy_id} has 0 damage",
                        [enemy_id],
                        "Verify this is intentional (e.g., honeypot)"
                    ))
    
    def analyze_class_balance(self) -> None:
        """Analyze player class balance."""
        print("Analyzing class balance...")
        
        # Calculate power scores for each class
        class_scores = {}
        for class_id, class_data in self.classes_data.items():
            stats = class_data['stats']
            
            # Simple power score calculation
            power_score = (
                stats['max_hp'] * 0.5 +
                stats['max_cpu'] * 0.3 + 
                stats['heat_capacity'] * 0.4 +
                stats['max_ram'] * 5 +
                stats['detection_resistance'] * 2
            )
            
            class_scores[class_id] = power_score
        
        # Check for outliers
        scores = list(class_scores.values())
        mean_score = np.mean(scores)
        std_score = np.std(scores)
        
        for class_id, score in class_scores.items():
            if abs(score - mean_score) > 2 * std_score:
                status = "overpowered" if score > mean_score else "underpowered"
                self.issues.append(BalanceIssue(
                    "warning", "class_balance",
                    f"Class {class_id} appears {status} (score: {score:.1f}, mean: {mean_score:.1f})",
                    [class_id],
                    f"Rebalance stats to bring closer to mean score"
                ))
        
        # Check starting equipment
        for class_id, class_data in self.classes_data.items():
            starting_exploits = class_data.get('starting_equipment', {}).get('exploits', [])
            total_ram = 0
            
            for exploit_id in starting_exploits:
                # Find exploit in data
                exploit_found = False
                for category in self.exploits_data.values():
                    if exploit_id in category:
                        total_ram += category[exploit_id].get('ram_cost', 0)
                        exploit_found = True
                        break
                
                if not exploit_found:
                    self.issues.append(BalanceIssue(
                        "error", "class_balance",
                        f"Class {class_id} references unknown exploit {exploit_id}",
                        [class_id],
                        "Remove invalid exploit or add to exploits.json"
                    ))
            
            max_ram = class_data['stats']['max_ram']
            if total_ram > max_ram:
                self.issues.append(BalanceIssue(
                    "error", "class_balance",
                    f"Class {class_id} starting exploits exceed RAM capacity ({total_ram} > {max_ram})",
                    [class_id],
                    "Reduce starting exploits or increase max_ram"
                ))
    
    def analyze_network_difficulty(self) -> None:
        """Analyze network difficulty progression."""
        print("Analyzing network difficulty...")
        
        network_levels = {}
        for network_id, network_data in self.networks_data.items():
            if network_id.startswith('network_'):
                level_num = int(network_id.split('_')[1])
                network_levels[level_num] = network_data
        
        # Check detection rate progression
        detection_rates = {}
        for level, network in network_levels.items():
            rate = network.get('detection_rate', {}).get('passive_increase', 0)
            detection_rates[level] = rate
        
        # Validate rates decrease (lower = harder)
        for level in sorted(detection_rates.keys())[:-1]:
            current_rate = detection_rates[level]
            next_rate = detection_rates[level + 1]
            
            if current_rate <= next_rate:
                self.issues.append(BalanceIssue(
                    "warning", "network_difficulty",
                    f"Network {level} detection rate ({current_rate}) should be higher than Network {level+1} ({next_rate})",
                    [f"network_{level}", f"network_{level+1}"],
                    "Adjust detection rates for proper difficulty progression"
                ))
        
        # Check enemy count progression
        for level, network in network_levels.items():
            enemy_count = network.get('enemy_count', [0, 0])
            min_enemies, max_enemies = enemy_count
            
            if min_enemies > max_enemies:
                self.issues.append(BalanceIssue(
                    "error", "network_difficulty",
                    f"Network {level} min enemies ({min_enemies}) > max enemies ({max_enemies})",
                    [f"network_{level}"],
                    "Fix enemy count range"
                ))
    
    def analyze_economy_balance(self) -> None:
        """Analyze the game's CPU economy."""
        print("Analyzing economy balance...")
        
        # Calculate CPU rewards from enemies
        total_cpu_rewards = {}
        for level_key, enemies in self.enemies_data.items():
            if level_key.startswith('level_'):
                level_num = int(level_key.split('_')[1])
                cpu_rewards = [enemy.get('cpu_reward', 0) for enemy in enemies.values()]
                total_cpu_rewards[level_num] = {
                    'min': min(cpu_rewards),
                    'max': max(cpu_rewards),
                    'avg': np.mean(cpu_rewards)
                }
        
        # Check for reasonable reward progression
        for level in sorted(total_cpu_rewards.keys())[:-1]:
            current_avg = total_cpu_rewards[level]['avg']
            next_avg = total_cpu_rewards[level + 1]['avg']
            
            if next_avg <= current_avg:
                self.issues.append(BalanceIssue(
                    "warning", "economy_balance",
                    f"Level {level+1} CPU rewards not higher than Level {level}",
                    [f"level_{level}", f"level_{level+1}"],
                    "Increase CPU rewards for higher level enemies"
                ))
        
        # Check for enemies with very low/high rewards
        for level_key, enemies in self.enemies_data.items():
            for enemy_id, enemy in enemies.items():
                cpu_reward = enemy.get('cpu_reward', 0)
                hp = enemy.get('hp', 1)
                
                # Reward per HP ratio
                if hp > 0:
                    reward_ratio = cpu_reward / hp
                    if reward_ratio < 0.5:
                        self.issues.append(BalanceIssue(
                            "info", "economy_balance",
                            f"Enemy {enemy_id} has low CPU/HP ratio: {reward_ratio:.2f}",
                            [enemy_id],
                            "Consider increasing CPU reward"
                        ))
                    elif reward_ratio > 3.0:
                        self.issues.append(BalanceIssue(
                            "info", "economy_balance", 
                            f"Enemy {enemy_id} has high CPU/HP ratio: {reward_ratio:.2f}",
                            [enemy_id],
                            "Consider decreasing CPU reward"
                        ))
    
    def analyze_ram_constraints(self) -> None:
        """Analyze RAM usage constraints."""
        print("Analyzing RAM constraints...")
        
        # Get all exploit RAM costs
        exploit_costs = []
        for category in self.exploits_data.values():
            for exploit in category.values():
                cost = exploit.get('ram_cost', 0)
                if cost > 0:
                    exploit_costs.append(cost)
        
        # Check against class RAM limits
        for class_id, class_data in self.classes_data.items():
            max_ram = class_data['stats']['max_ram']
            
            # Count how many exploits can be loaded
            loadable_exploits = [cost for cost in exploit_costs if cost <= max_ram]
            
            if len(loadable_exploits) < 3:
                self.issues.append(BalanceIssue(
                    "warning", "ram_constraints",
                    f"Class {class_id} can only load {len(loadable_exploits)} exploits",
                    [class_id],
                    "Increase max_ram or reduce exploit costs"
                ))
            
            # Check for impossible combinations
            min_viable_loadout = sum(sorted(exploit_costs)[:3])
            if min_viable_loadout > max_ram:
                self.issues.append(BalanceIssue(
                    "error", "ram_constraints",
                    f"Class {class_id} cannot load minimum viable loadout",
                    [class_id],
                    f"Increase max_ram to at least {min_viable_loadout}"
                ))
    
    def analyze_heat_economy(self) -> None:
        """Analyze heat generation vs capacity."""
        print("Analyzing heat economy...")
        
        # Get heat capacities
        heat_capacities = []
        for class_data in self.classes_data.values():
            capacity = class_data['stats']['heat_capacity']
            heat_capacities.append(capacity)
        
        min_capacity = min(heat_capacities)
        
        # Check exploit heat costs
        for category in self.exploits_data.values():
            for exploit_id, exploit in category.items():
                heat_cost = exploit.get('heat_generated', 0)
                
                if heat_cost > min_capacity * 0.8:
                    self.issues.append(BalanceIssue(
                        "warning", "heat_economy",
                        f"Exploit {exploit_id} uses {heat_cost}°C (>{min_capacity * 0.8:.0f}°C threshold)",
                        [exploit_id],
                        "Consider reducing heat cost for accessibility"
                    ))
                
                # Check for zero-heat exploits
                if heat_cost == 0 and 'damage_base' in exploit:
                    self.issues.append(BalanceIssue(
                        "info", "heat_economy",
                        f"Damage exploit {exploit_id} has no heat cost",
                        [exploit_id],
                        "Consider adding heat cost for balance"
                    ))
    
    def generate_report(self) -> str:
        """Generate a formatted balance report."""
        report = ["=" * 60]
        report.append("ROGUE SIGNAL PROTOCOL - BALANCE ANALYSIS REPORT")
        report.append("=" * 60)
        report.append("")
        
        # Summary
        error_count = len([i for i in self.issues if i.severity == "error"])
        warning_count = len([i for i in self.issues if i.severity == "warning"])
        info_count = len([i for i in self.issues if i.severity == "info"])
        
        report.append(f"SUMMARY:")
        report.append(f"  Errors: {error_count}")
        report.append(f"  Warnings: {warning_count}")
        report.append(f"  Info: {info_count}")
        report.append(f"  Total Issues: {len(self.issues)}")
        report.append("")
        
        # Group issues by category
        by_category = {}
        for issue in self.issues:
            if issue.category not in by_category:
                by_category[issue.category] = []
            by_category[issue.category].append(issue)
        
        # Report by category
        for category, issues in by_category.items():
            report.append(f"{category.upper().replace('_', ' ')}:")
            report.append("-" * (len(category) + 1))
            
            for issue in issues:
                severity_marker = {"error": "❌", "warning": "⚠️", "info": "ℹ️"}
                marker = severity_marker.get(issue.severity, "•")
                
                report.append(f"{marker} {issue.description}")
                if issue.affected_items:
                    report.append(f"   Affected: {', '.join(issue.affected_items)}")
                report.append(f"   Fix: {issue.suggested_fix}")
                report.append("")
        
        return "\n".join(report)
    
    def generate_charts(self, output_dir: str = "balance_charts") -> None:
        """Generate balance analysis charts."""
        import matplotlib.pyplot as plt
        import os
        
        os.makedirs(output_dir, exist_ok=True)
        
        # Enemy HP progression chart
        self._chart_enemy_progression(output_dir)
        
        # Class balance radar chart
        self._chart_class_balance(output_dir)
        
        # Exploit cost distribution
        self._chart_exploit_costs(output_dir)
        
        # Detection rate progression
        self._chart_detection_rates(output_dir)
    
    def _chart_enemy_progression(self, output_dir: str) -> None:
        """Chart enemy HP and damage progression."""
        levels = []
        hp_avgs = []
        damage_avgs = []
        
        for level_key, enemies in self.enemies_data.items():
            if level_key.startswith('level_'):
                level_num = int(level_key.split('_')[1])
                hp_values = [enemy['hp'] for enemy in enemies.values()]
                damage_values = [enemy['damage'] for enemy in enemies.values()]
                
                levels.append(level_num)
                hp_avgs.append(np.mean(hp_values))
                damage_avgs.append(np.mean(damage_values))
        
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))
        
        ax1.plot(levels, hp_avgs, 'b-o', label='Average HP')
        ax1.set_title('Enemy HP Progression')
        ax1.set_xlabel('Level')
        ax1.set_ylabel('HP')
        ax1.grid(True)
        
        ax2.plot(levels, damage_avgs, 'r-o', label='Average Damage')
        ax2.set_title('Enemy Damage Progression')
        ax2.set_xlabel('Level')
        ax2.set_ylabel('Damage')
        ax2.grid(True)
        
        plt.tight_layout()
        plt.savefig(f"{output_dir}/enemy_progression.png", dpi=300, bbox_inches='tight')
        plt.close()
    
    def _chart_class_balance(self, output_dir: str) -> None:
        """Chart class stat comparison."""
        classes = list(self.classes_data.keys())
        stats = ['max_hp', 'max_cpu', 'heat_capacity', 'max_ram']
        
        fig, axes = plt.subplots(2, 2, figsize=(12, 10))
        axes = axes.flatten()
        
        for i, stat in enumerate(stats):
            values = [self.classes_data[c]['stats'][stat] for c in classes]
            
            axes[i].bar(classes, values)
            axes[i].set_title(f'{stat.replace("_", " ").title()}')
            axes[i].tick_params(axis='x', rotation=45)
        
        plt.tight_layout()
        plt.savefig(f"{output_dir}/class_balance.png", dpi=300, bbox_inches='tight')
        plt.close()
    
    def _chart_exploit_costs(self, output_dir: str) -> None:
        """Chart exploit RAM and heat cost distributions."""
        ram_costs = []
        heat_costs = []
        
        for category in self.exploits_data.values():
            for exploit in category.values():
                ram_costs.append(exploit.get('ram_cost', 0))
                heat_costs.append(exploit.get('heat_generated', 0))
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
        
        ax1.hist(ram_costs, bins=10, alpha=0.7, color='blue')
        ax1.set_title('RAM Cost Distribution')
        ax1.set_xlabel('RAM Cost (GB)')
        ax1.set_ylabel('Number of Exploits')
        
        ax2.hist(heat_costs, bins=10, alpha=0.7, color='red')
        ax2.set_title('Heat Cost Distribution')
        ax2.set_xlabel('Heat Generated (°C)')
        ax2.set_ylabel('Number of Exploits')
        
        plt.tight_layout()
        plt.savefig(f"{output_dir}/exploit_costs.png", dpi=300, bbox_inches='tight')
        plt.close()
    
    def _chart_detection_rates(self, output_dir: str) -> None:
        """Chart detection rate progression."""
        levels = []
        rates = []
        
        for network_id, network_data in self.networks_data.items():
            if network_id.startswith('network_'):
                level_num = int(network_id.split('_')[1])
                rate = network_data.get('detection_rate', {}).get('passive_increase', 0)
                levels.append(level_num)
                rates.append(rate)
        
        plt.figure(figsize=(10, 6))
        plt.plot(levels, rates, 'g-o', linewidth=2, markersize=8)
        plt.title('Detection Rate Progression (Lower = Harder)')
        plt.xlabel('Network Level')
        plt.ylabel('Turns per 1% Detection Increase')
        plt.grid(True, alpha=0.3)
        
        # Add annotations
        for i, (level, rate) in enumerate(zip(levels, rates)):
            plt.annotate(f'{rate}', (level, rate), textcoords="offset points", 
                        xytext=(0,10), ha='center')
        
        plt.savefig(f"{output_dir}/detection_rates.png", dpi=300, bbox_inches='tight')
        plt.close()

def main():
    """Main function for running balance analysis."""
    if len(sys.argv) > 1:
        data_dir = sys.argv[1]
    else:
        data_dir = "data"
    
    analyzer = BalanceAnalyzer(data_dir)
    
    if not analyzer.load_data():
        print("Failed to load data files. Exiting.")
        return 1
    
    print("Running balance analysis...")
    issues = analyzer.analyze_all()
    
    # Generate report
    report = analyzer.generate_report()
    print(report)
    
    # Save report to file
    with open("balance_report.txt", "w") as f:
        f.write(report)
    
    # Generate charts if matplotlib is available
    try:
        analyzer.generate_charts()
        print("\nBalance charts saved to balance_charts/")
    except ImportError:
        print("\nMatplotlib not available - skipping chart generation")
    
    # Return exit code based on severity
    error_count = len([i for i in issues if i.severity == "error"])
    if error_count > 0:
        print(f"\n❌ {error_count} errors found - fix before release!")
        return 1
    else:
        print(f"\n✅ No critical errors found")
        return 0

if __name__ == "__main__":
    sys.exit(main())