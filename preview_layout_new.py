# New layout code to replace in _render_preview_map

        # Shadows (if available) - put a couple in shadow area
        if "shadow" in self.selected_variants:
            shadow_positions = [(2, 2), (3, 2)]
            for sx, sy in shadow_positions:
                render_queue.append((sx, sy, "shadow", 1))

        # Ghost node ON TOP of shadow (like in-game)
        if "ghostnode" in self.selected_variants:
            render_queue.append((2, 2, "ghostnode", 3))

        # Player (center-left area)
        if "player" in self.selected_variants:
            render_queue.append((10, 8, "player", 2))

        # Enemies (2 rows of 4, compact spacing)
        enemy_positions = [
            (2, 5), (5, 5), (8, 5), (11, 5),
            (2, 8), (5, 8), (8, 8), (11, 8)
        ]
        enemy_types = ["scanner", "patrol", "bot", "hunter", "virus", "inhibitor", "firewall", "avatar"]
        for i, enemy_type in enumerate(enemy_types):
            if enemy_type in self.selected_variants and i < len(enemy_positions):
                ex, ey = enemy_positions[i]
                render_queue.append((ex, ey, enemy_type, 2))

        # CodeHacks and Exploits - FULL SIZE, side by side horizontally at top
        # Position them above the enemies
        if "codehack" in self.selected_variants:
            for i in range(6):  # 6 color variants
                render_queue.append((2 + i, 2, "codehack", 2, i))  # Add variant index as 5th element

        if "exploit" in self.selected_variants:
            for i in range(4):  # 4 color variants
                render_queue.append((9 + i, 2, "exploit", 2, i))

        # Other items - regular positions
        item_positions = [
            (14, 5), (17, 5),  # cooling node/upgrade
            (14, 8), (17, 8),  # cpu node/upgrade
            (14, 11), (17, 11),  # ram upgrade, ghost node (moved)
        ]
        item_types = ["coolingnode", "coolingupgrade", "cpunode", "cpuupgrade", "ramupgrade"]
        for i, item_type in enumerate(item_types):
            if item_type in self.selected_variants and i < len(item_positions):
                ix, iy = item_positions[i]
                render_queue.append((ix, iy, item_type, 2))

        # Special entities
        if "portal" in self.selected_variants:
            render_queue.append((14, 14, "portal", 2))
        if "storyfragment" in self.selected_variants:
            render_queue.append((17, 14, "storyfragment", 2))

        # BOTTOM RIGHT CORNER - Combat preview scene
        # Enemy with alert ring, movement predictions, and vision brackets
        if "hunter" in self.selected_variants:
            # Hunter enemy at position 17, 14
            combat_enemy_x, combat_enemy_y = 17, 12
            render_queue.append((combat_enemy_x, combat_enemy_y, "hunter", 2))

            # Mark this enemy for alert ring and vision rendering
            alert_enemy_pos = (combat_enemy_x, combat_enemy_y)

        # Player target for movement predictions
        if "player" in self.selected_variants:
            combat_player_x, combat_player_y = 14, 14
            render_queue.append((combat_player_x, combat_player_y, "player", 2))

            # Movement predictions from enemy toward player
            if "movementprediction" in self.selected_variants:
                # Path from hunter to player
                pred_positions = [(16, 13), (15, 13), (15, 14)]
                for px, py in pred_positions:
                    render_queue.append((px, py, "movementprediction", 1))
