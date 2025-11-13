#!/usr/bin/env python3
"""
Wiki Content Generator for Rogue Signal Protocol

Automatically generates wiki pages from game JSON files.
Run this script to update the wiki content with the latest game data.

Usage:
    python docs/generate_wiki.py
"""

import json
from pathlib import Path


def load_game_content():
    """Load game_content.json"""
    content_path = Path("game_content.json")
    with open(content_path) as f:
        return json.load(f)


def generate_enemy_database(content):
    """Generate Enemy-Database.md from game_content.json"""
    enemies = content["enemy_types"]

    md = ["# Enemy Database\n"]
    md.append("Complete reference for all enemy types in Rogue Signal Protocol.\n")
    md.append("## Overview\n")
    md.append(
        f"There are **{len(enemies)} unique enemy types** with different behaviors, stats, and threat levels.\n"
    )

    # Group enemies by behavior
    static_enemies = []
    mobile_enemies = []
    special_enemies = []

    for enemy_id, enemy in enemies.items():
        if enemy["symbol"] == "A":
            special_enemies.append((enemy_id, enemy))
        elif enemy["movement"] == "STATIC":
            static_enemies.append((enemy_id, enemy))
        else:
            mobile_enemies.append((enemy_id, enemy))

    md.append("## Enemy Types\n")

    # Static Enemies
    md.append("### Static Enemies\n")
    md.append("Stationary enemies that guard fixed positions.\n")
    for enemy_id, enemy in static_enemies:
        md.append(f"#### {enemy['name']} ({enemy['symbol']})\n")
        md.append("**Stats:**\n")
        md.append(f"- CPU: {enemy['cpu']}\n")
        md.append(f"- Vision: {enemy['vision']} tiles\n")
        md.append(f"- Damage: {enemy['damage']}\n")
        md.append(f"- Movement: {enemy['movement']}\n")
        md.append(f"\n{enemy['description']}\n")

        # Tactical notes
        if enemy["symbol"] == "S":
            md.append("**Tactical Notes:**\n")
            md.append("- Cannot attack but alerts nearby enemies\n")
            md.append("- Extended vision range makes them dangerous sentries\n")
            md.append("- Eliminate early if stealth approach required\n")
        elif enemy["symbol"] == "F":
            md.append("**Tactical Notes:**\n")
            md.append("- Extremely high CPU makes them hard to kill\n")
            md.append("- Often blocks critical paths\n")
            md.append("- Consider avoiding rather than fighting\n")
        md.append("\n")

    # Mobile Enemies
    md.append("### Mobile Enemies\n")
    md.append("Enemies that patrol or pursue actively.\n")
    for enemy_id, enemy in mobile_enemies:
        md.append(f"#### {enemy['name']} ({enemy['symbol']})\n")
        md.append("**Stats:**\n")
        md.append(f"- CPU: {enemy['cpu']}\n")
        md.append(f"- Vision: {enemy['vision']} tiles\n")
        md.append(f"- Damage: {enemy['damage']}\n")
        md.append(f"- Movement: {enemy['movement']}\n")
        md.append(f"\n{enemy['description']}\n")

        # Tactical notes based on type
        if enemy["symbol"] == "P":
            md.append("**Tactical Notes:**\n")
            md.append("- Shows next 3 planned moves - highly predictable\n")
            md.append("- Easy to avoid with proper timing\n")
            md.append("- Alerts other enemies when detecting player\n")
        elif enemy["symbol"] == "B":
            md.append("**Tactical Notes:**\n")
            md.append("- Unpredictable movement makes them dangerous\n")
            md.append("- Lower stats compensate for chaos factor\n")
            md.append("- Can accidentally discover you in blind spots\n")
        elif enemy["symbol"] == "H":
            md.append("**Tactical Notes:**\n")
            md.append("- Highest vision range of standard enemies\n")
            md.append("- Very dangerous in combat (15 damage)\n")
            md.append("- Avoid or ambush from blind spots\n")
        elif enemy["symbol"] == "V":
            md.append("**Tactical Notes:**\n")
            md.append("- No direct damage but inflicts virus status\n")
            md.append("- Virus deals 3 CPU per turn for 3-10 turns\n")
            md.append("- Use Antivirus exploit to cure infection\n")
        elif enemy["symbol"] == "I":
            md.append("**Tactical Notes:**\n")
            md.append("- Slows your movement on contact\n")
            md.append("- No damage but tactical nuisance\n")
            md.append("- Use Antivirus exploit to remove slow effect\n")
        md.append("\n")

    # Special Enemies (Boss)
    md.append("### Boss Enemy\n")
    md.append("Special enemy that only appears under specific conditions.\n")
    for enemy_id, enemy in special_enemies:
        md.append(f"#### {enemy['name']} ({enemy['symbol']})\n")
        md.append("**Stats:**\n")
        md.append(f"- CPU: {enemy['cpu']}\n")
        md.append(f"- Vision: {enemy['vision']} tiles\n")
        md.append(f"- Damage: {enemy['damage']}\n")
        md.append(
            f"- Damage Resistance: {enemy.get('damage_resistance_percent', 0)}% (min {enemy.get('damage_resistance_min', 0)})\n"
        )
        md.append(f"- Movement: {enemy['movement']}\n")
        md.append(f"\n{enemy['description']}\n")
        md.append("\n**Spawn Conditions:**\n")
        md.append("- Appears on Military Backbone (Level 3) at high trace levels\n")
        md.append("- Can spawn when trace reaches critical thresholds\n")
        md.append("\n**Tactical Notes:**\n")
        md.append("- **EXTREMELY DANGEROUS** - avoid if possible\n")
        md.append("- 50% damage resistance makes it very tanky\n")
        md.append("- 45 damage can kill you in 3 hits\n")
        md.append("- Best strategy: Keep trace low to prevent spawning\n")
        md.append("- If spawned: Use System Hop to escape, avoid direct combat\n")
        md.append("\n")

    # Stats comparison table
    md.append("## Stats Comparison\n")
    md.append("| Enemy | Symbol | CPU | Vision | Damage | Movement |\n")
    md.append("|-------|--------|-----|--------|--------|----------|\n")

    # Sort by CPU
    sorted_enemies = sorted(enemies.items(), key=lambda x: x[1]["cpu"])
    for enemy_id, enemy in sorted_enemies:
        movement = enemy["movement"].title()
        md.append(
            f"| {enemy['name']} | {enemy['symbol']} | {enemy['cpu']} | {enemy['vision']} | {enemy['damage']} | {movement} |\n"
        )

    md.append("\n## Movement Behaviors\n")
    md.append("### STATIC\n")
    md.append("Remains in one position. Does not move unless pushed by game mechanics.\n")
    md.append("\n### PATROL\n")
    md.append("Follows predetermined routes. Shows next 3 planned moves for player prediction.\n")
    md.append("\n### RANDOM\n")
    md.append("Moves unpredictably. Can change direction at any moment.\n")
    md.append("\n### VIRUS\n")
    md.append("Special movement pattern for Virus enemies. Wanders while seeking targets.\n")
    md.append("\n### ADMIN\n")
    md.append("Advanced AI behavior. Relentlessly pursues player with optimal pathfinding.\n")

    md.append("\n## Detection & Alert System\n")
    md.append("All enemies have three awareness states:\n")
    md.append("\n### Unaware (Yellow)\n")
    md.append("- Default state\n")
    md.append("- Following normal behavior pattern\n")
    md.append("- Has not detected player\n")
    md.append("\n### Alert (Orange)\n")
    md.append("- Investigating suspicious activity\n")
    md.append("- Lasts 1 turn only\n")
    md.append("- Can escalate to hostile if player seen again\n")
    md.append("\n### Hostile (Red)\n")
    md.append("- Actively pursuing player\n")
    md.append("- Alerts nearby enemies within 8 tile radius\n")
    md.append("- Uses optimal pathfinding to chase\n")

    md.append("\n## Tips & Strategies\n")
    md.append("1. **Know your enemy:** Study movement patterns and vision ranges\n")
    md.append("2. **Use blind spots:** Hide in monitoring dead zones to avoid detection\n")
    md.append("3. **Watch the queue:** Enemy movement predictions show 3 moves ahead\n")
    md.append("4. **Ambush bonus:** Attacking from blind spots grants +10 damage\n")
    md.append("5. **Avoid Admin Avatar:** Keep trace low to prevent spawning\n")
    md.append("6. **Status effects matter:** Carry Antivirus for virus/slow effects\n")
    md.append("7. **Target priority:** Eliminate Scanners first, avoid Firewalls\n")
    md.append("8. **Stealth over combat:** Killing alerts nearby enemies\n")

    return "".join(md)


def generate_exploit_database(content):
    """Generate Exploit-Database.md from game_content.json"""
    exploits = content["exploits"]

    md = ["# Exploit Database\n"]
    md.append("Complete reference for all exploits (abilities) in Rogue Signal Protocol.\n")
    md.append(f"\nThere are **{len(exploits)} exploits** organized into 4 categories.\n")

    # Group by category
    categories = {}
    for exploit_id, exploit in exploits.items():
        category = exploit["category"]
        if category not in categories:
            categories[category] = []
        categories[category].append((exploit_id, exploit))

    # Category order and descriptions
    category_info = {
        "stealth": {
            "title": "Stealth Exploits",
            "description": "Abilities focused on avoiding detection, repositioning, and manipulating enemy awareness.",
        },
        "combat": {
            "title": "Combat Exploits",
            "description": "Offensive abilities for damaging or disabling enemies.",
        },
        "utility": {
            "title": "Utility Exploits",
            "description": "Support abilities for information gathering, resource management, and status effects.",
        },
        "emergency": {
            "title": "Emergency Exploits",
            "description": "High-risk, high-reward last resort abilities.",
        },
    }

    for category in ["stealth", "combat", "utility", "emergency"]:
        if category not in categories:
            continue

        info = category_info[category]
        md.append(f"\n## {info['title']}\n")
        md.append(f"{info['description']}\n")

        for exploit_id, exploit in categories[category]:
            md.append(f"\n### {exploit['name']}\n")

            # Stats table
            md.append(
                f"**Cost:** {exploit['ram']} RAM | **Heat:** {exploit['heat']}° | **Range:** {exploit['range']} tiles\n"
            )

            md.append(f"\n{exploit['description']}\n")

            # Technical details
            md.append("\n**Technical Details:**\n")
            md.append(f"- Targeting: {exploit['targeting']}\n")

            if exploit.get("damage", 0) > 0:
                md.append(f"- Damage: {exploit['damage']}\n")

            if exploit.get("self_damage", 0) > 0:
                md.append(f"- Self Damage: {exploit['self_damage']} ⚠️\n")

            if exploit.get("effect_radius", 0) > 0:
                md.append(f"- Effect Radius: {exploit['effect_radius']} tiles\n")

            if exploit.get("effect_duration", 0) > 0:
                md.append(f"- Duration: {exploit['effect_duration']} turns\n")

            if "trace_reduction_percent" in exploit:
                md.append(f"- Trace Reduction: {exploit['trace_reduction_percent']}%\n")

            if "alert_duration_patrol" in exploit:
                md.append(f"- Alert Duration (Patrol): {exploit['alert_duration_patrol']} turns\n")
                md.append(f"- Alert Duration (Normal): {exploit['alert_duration_normal']} turns\n")

            # Tactical notes
            md.append("\n**Tactical Notes:**\n")

            if exploit_id == "system_hop":
                md.append("- Instant repositioning for escapes or flanking\n")
                md.append("- No line of sight required\n")
                md.append("- Low heat cost for frequent use\n")
            elif exploit_id == "traffic_masquerade":
                md.append("- Complete invisibility for 5 turns\n")
                md.append("- Walk past enemies freely\n")
                md.append("- Attacking breaks invisibility\n")
            elif exploit_id == "decoy_swarm":
                md.append("- Lures enemies away from your position\n")
                md.append("- Long duration (8 turns) for extended distraction\n")
                md.append("- Patrol enemies stay distracted longer\n")
            elif exploit_id == "buffer_overflow":
                md.append("- Highest damage single-target exploit\n")
                md.append("- Melee range only (1 tile)\n")
                md.append("- Combine with blind spot ambush for 50 total damage\n")
            elif exploit_id == "code_injection":
                md.append("- Reliable ranged damage\n")
                md.append("- 5 tile range for safe attacks\n")
                md.append("- Moderate heat cost for repeated use\n")
            elif exploit_id == "system_crash":
                md.append("- **DEALS SELF-DAMAGE!** Use as last resort\n")
                md.append("- Stuns all enemies in radius for 3 turns\n")
                md.append("- Effective when surrounded\n")
            elif exploit_id == "logic_bomb":
                md.append("- Area damage centered on target location\n")
                md.append("- Can damage you if too close!\n")
                md.append("- Good for grouped enemies\n")
            elif exploit_id == "threat_scan":
                md.append("- Reveals enemy vision cones\n")
                md.append("- Shows predicted movement paths\n")
                md.append("- Essential for stealth planning\n")
            elif exploit_id == "network_scan":
                md.append("- Reveals all special nodes instantly\n")
                md.append("- Find cooling/CPU/ghost nodes\n")
                md.append("- One-time use per level recommended\n")
            elif exploit_id == "log_wiper":
                md.append("- Reduces trace by 30%\n")
                md.append("- Prevents Admin Avatar spawn\n")
                md.append("- Use when trace exceeds 70%\n")
            elif exploit_id == "antivirus":
                md.append("- Cures virus and slow effects\n")
                md.append("- Instant cleanse, no duration\n")
                md.append("- Keep equipped when Viruses present\n")
            elif exploit_id == "denial_of_service":
                md.append("- Disables enemies without killing\n")
                md.append("- 5 turn duration for repositioning\n")
                md.append("- Area effect (radius 1)\n")
            elif exploit_id == "memory_leak":
                md.append("- Blinds enemies in 3x3 area\n")
                md.append("- Enemies keep moving while blind\n")
                md.append("- Use to slip past patrols\n")

            md.append("\n")

    # Stats comparison table
    md.append("## Quick Reference Table\n")
    md.append("| Exploit | Category | RAM | Heat | Range | Damage | Duration |\n")
    md.append("|---------|----------|-----|------|-------|--------|----------|\n")

    for exploit_id, exploit in exploits.items():
        damage = str(exploit.get("damage", 0)) if exploit.get("damage", 0) > 0 else "-"
        duration = (
            str(exploit.get("effect_duration", 0)) if exploit.get("effect_duration", 0) > 0 else "-"
        )
        md.append(
            f"| {exploit['name']} | {exploit['category'].title()} | {exploit['ram']} | {exploit['heat']} | {exploit['range']} | {damage} | {duration} |\n"
        )

    md.append("\n## Loadout Strategies\n")
    md.append("### Stealth Build\n")
    md.append("- System Hop (3 RAM)\n")
    md.append("- Traffic Masquerade (2 RAM)\n")
    md.append("- Threat Scan (1 RAM)\n")
    md.append("- Log Wiper (2 RAM)\n")
    md.append("\n**Total:** 8 RAM | **Focus:** Avoiding all combat\n")

    md.append("\n### Balanced Build\n")
    md.append("- Code Injection (2 RAM)\n")
    md.append("- System Hop (3 RAM)\n")
    md.append("- Threat Scan (1 RAM)\n")
    md.append("- Antivirus (2 RAM)\n")
    md.append("\n**Total:** 8 RAM | **Focus:** Versatility\n")

    md.append("\n### Combat Build\n")
    md.append("- Buffer Overflow (2 RAM)\n")
    md.append("- Code Injection (2 RAM)\n")
    md.append("- Logic Bomb (2 RAM)\n")
    md.append("- System Crash (3 RAM)\n")
    md.append("\n**Total:** 9 RAM | **Focus:** Elimination\n")

    md.append("\n### Boss Hunter Build\n")
    md.append("- Buffer Overflow (2 RAM)\n")
    md.append("- Code Injection (2 RAM)\n")
    md.append("- System Hop (3 RAM)\n")
    md.append("- Network Scan (1 RAM)\n")
    md.append("\n**Total:** 8 RAM | **Focus:** Admin Avatar combat\n")

    md.append("\n## Tips & Strategies\n")
    md.append("1. **Balance your loadout:** Mix stealth, combat, and utility\n")
    md.append("2. **RAM management:** Prioritize low-cost exploits early game\n")
    md.append("3. **Heat awareness:** Don't overheat - 2-3 exploits per combat\n")
    md.append("4. **Synergies:** Threat Scan + System Hop = perfect positioning\n")
    md.append(
        "5. **Emergency options:** Always have an escape (System Hop or Traffic Masquerade)\n"
    )
    md.append("6. **Adapt per level:** Corporate needs stealth, Military needs combat\n")
    md.append("7. **Upgrade wisely:** RAM upgrades unlock better loadouts\n")

    return "".join(md)


def generate_network_configuration(content):
    """Generate Network-Configuration.md from game_content.json"""
    networks = content["network_configs"]
    difficulties = content["difficulty_multipliers"]

    md = ["# Network Configuration\n"]
    md.append("Level progression, difficulty settings, and resource distribution.\n")

    md.append("\n## Network Levels\n")
    md.append(
        "Rogue Signal Protocol has **3 progressive network levels** with escalating difficulty.\n"
    )

    for level_id in sorted(networks.keys(), key=int):
        network = networks[level_id]
        md.append(f"\n### Level {level_id}: {network['name']}\n")

        md.append("\n**Threat Level:**\n")
        md.append(f"- Enemies: {network['enemies']}\n")
        md.append(f"- Blind Spot Coverage: {network['blind_spot_coverage']*100:.0f}%\n")
        md.append(f"- Background Trace: {network['background_trace']}/25 turns\n")
        md.append(f"- Trace Alert -> Hostile: {network['trace_alert_to_hostile']}%\n")
        md.append(f"- Trace Continuous Hostile: {network['trace_continuous_hostile']}%/turn\n")

        md.append("\n**Resources:**\n")
        md.append(f"- Cooling Nodes: {network['cooling_nodes']}\n")
        md.append(f"- CPU Recovery Nodes: {network['cpu_nodes']}\n")
        md.append(f"- Ghost Nodes: {network['ghost_nodes']}\n")
        md.append(f"- Data Codes: {network['code_hacks']}\n")
        md.append(f"- Exploit Pickups: {network['exploit_pickups']}\n")
        md.append(f"- Permanent Upgrades: {network['permanent_upgrades']}\n")

        # Strategic notes
        if level_id == "1":
            md.append("\n**Strategic Notes:**\n")
            md.append("- Easiest level with most resources\n")
            md.append("- Use to learn mechanics and collect exploits\n")
            md.append("- Low enemy count allows exploration\n")
            md.append("- Stock up on upgrades before advancing\n")
        elif level_id == "2":
            md.append("\n**Strategic Notes:**\n")
            md.append("- Moderate difficulty spike\n")
            md.append("- Fewer resources require careful management\n")
            md.append("- More enemies increase stealth importance\n")
            md.append("- Critical upgrade opportunities\n")
        elif level_id == "3":
            md.append("\n**Strategic Notes:**\n")
            md.append("- **Hardest level** - minimal resources\n")
            md.append("- Admin Avatar can spawn at high trace\n")
            md.append("- 38 enemies make stealth essential\n")
            md.append("- Final upgrades before victory\n")
            md.append("- Consider going loud if well-equipped\n")

    md.append("\n## Difficulty Multipliers\n")
    md.append("Four difficulty settings affect enemy stats and resource availability.\n")

    md.append("\n| Difficulty | Multiplier | Effect |\n")
    md.append("|------------|------------|--------|\n")

    for difficulty, multiplier in difficulties.items():
        effect = f"{(multiplier - 1.0) * 100:+.0f}%"
        if multiplier == 1.0:
            effect = "Baseline"
        elif multiplier < 1.0:
            effect = f"{(1.0 - multiplier) * 100:.0f}% easier"
        else:
            effect = f"{(multiplier - 1.0) * 100:.0f}% harder"

        md.append(f"| {difficulty.title()} | {multiplier}x | {effect} |\n")

    md.append("\n**What Difficulty Affects:**\n")
    md.append("- Enemy CPU (health)\n")
    md.append("- Enemy damage\n")
    md.append("- Enemy vision range\n")
    md.append("- Trace accumulation rate\n")
    md.append("- Resource spawn rates\n")

    md.append("\n## Progression Strategy\n")

    md.append("\n### Early Game (Corporate Network)\n")
    md.append("**Goals:**\n")
    md.append("- Learn enemy patterns and movement queues\n")
    md.append("- Collect all exploit pickups (4 available)\n")
    md.append("- Find permanent upgrade (prioritize RAM or Heat)\n")
    md.append("- Discover as many story fragments as possible\n")
    md.append("- Practice stealth mechanics in low-pressure environment\n")
    md.append("\n**Resource Management:**\n")
    md.append("- Use cooling nodes liberally (6 available)\n")
    md.append("- Save CPU nodes for emergencies\n")
    md.append("- Use ghost nodes to reduce trace proactively\n")
    md.append("- Collect all 12 data codes for buffs\n")

    md.append("\n### Mid Game (Government System)\n")
    md.append("**Goals:**\n")
    md.append("- Solidify your loadout with 3 more exploits\n")
    md.append("- Obtain 2 permanent upgrades\n")
    md.append("- Master blind spot usage and enemy prediction\n")
    md.append("- Manage limited resources carefully\n")
    md.append("\n**Resource Management:**\n")
    md.append("- Only 4 cooling nodes - conserve heat\n")
    md.append("- 4 CPU nodes - avoid unnecessary damage\n")
    md.append("- 4 ghost nodes - use strategically for trace reduction\n")
    md.append("- 10 data codes - prioritize heat/CPU restoration\n")

    md.append("\n### Late Game (Military Backbone)\n")
    md.append("**Goals:**\n")
    md.append("- Survive to gateway with minimal trace\n")
    md.append("- Avoid Admin Avatar spawn (keep trace below 70%)\n")
    md.append("- Collect final 3 permanent upgrades\n")
    md.append("- Complete the run and exfiltrate\n")
    md.append("\n**Resource Management:**\n")
    md.append("- **Scarce resources!** Only 2 of each node type\n")
    md.append("- Stealth is mandatory - combat too expensive\n")
    md.append("- 5 data codes must be used optimally\n")
    md.append("- 2 exploit pickups - final loadout decisions\n")
    md.append("- Log Wiper essential for trace management\n")

    md.append("\n## Tips for Success\n")
    md.append("1. **Don't rush Level 1:** Collect everything before advancing\n")
    md.append("2. **Upgrade priority:** RAM > Heat > CPU\n")
    md.append("3. **Trace management:** Use ghost nodes and Log Wiper\n")
    md.append("4. **Resource conservation:** Harder levels have fewer nodes\n")
    md.append("5. **Admin Avatar:** If spawned on Level 3, avoid at all costs\n")
    md.append("6. **Difficulty scaling:** Start with Easy, master Normal, attempt Hard\n")
    md.append("7. **Learning curve:** Each network teaches new lessons\n")
    md.append("8. **Permadeath:** Your decisions matter - plan carefully\n")

    return "".join(md)


def main():
    """Generate all wiki pages from game content"""
    print("Generating wiki pages from game content...")

    # Load content
    content = load_game_content()

    # Create output directory
    output_dir = Path("docs/wiki")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Generate pages
    pages = {
        "Enemy-Database.md": generate_enemy_database(content),
        "Exploit-Database.md": generate_exploit_database(content),
        "Network-Configuration.md": generate_network_configuration(content),
    }

    # Write pages
    for filename, content in pages.items():
        filepath = output_dir / filename
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Generated: {filepath}")

    print("\nWiki generation complete!")
    print(f"Generated {len(pages)} pages in {output_dir}/")
    print("\nTo update the GitHub wiki:")
    print("1. cd to parent directory: cd ..")
    print("2. Clone wiki: git clone https://github.com/Dragynrain/RogueSignalProtocol.wiki.git")
    print("3. Copy files: cp -r RogueSignalProtocol/docs/wiki/*.md RogueSignalProtocol.wiki/")
    print("4. cd RogueSignalProtocol.wiki")
    print("5. git add .")
    print('6. git commit -m "Update wiki content"')
    print("7. git push")


if __name__ == "__main__":
    main()
