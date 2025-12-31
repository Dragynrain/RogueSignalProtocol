"""
Particle system for visual effects in graphics mode.

Handles explosive particle effects when enemies die, with physics simulation
and multi-color sprite-based particles.
"""

import logging
import math
import random
import time
from dataclasses import dataclass

from rsp.core.config import GameConfig
from rsp.entities.base import Colors

# Fallback color when no colors are provided
FALLBACK_WHITE = Colors.PURE_WHITE


@dataclass
class Particle:
    """Individual particle with physics properties."""

    # Position in world coordinates (float for smooth sub-pixel movement)
    x: float
    y: float

    # Velocity in pixels per second
    velocity_x: float
    velocity_y: float

    # Visual properties
    color: tuple[int, int, int]  # RGB
    size: int  # Pixel size (3-5 pixels)

    # Lifetime tracking
    birth_time: float
    lifetime: float  # Total lifetime in seconds

    def is_alive(self, current_time: float) -> bool:
        """Check if particle is still alive."""
        age = current_time - self.birth_time
        return age < self.lifetime

    def get_alpha(self, current_time: float) -> int:
        """Calculate current alpha value based on age (fade out over lifetime)."""
        age = current_time - self.birth_time
        if age >= self.lifetime:
            return 0

        # Linear fade: 255 at birth -> 0 at death
        alpha_ratio = 1.0 - (age / self.lifetime)
        return int(255 * alpha_ratio)


class ParticleSystem:
    """
    Manages particle effects for the game.

    Handles creation, updating, and rendering of particle effects like
    enemy death explosions.
    """

    def __init__(self):
        """Initialize the particle system."""
        self.particles: list[Particle] = []

        # Physics constants from config
        self.gravity = GameConfig.PARTICLE_GRAVITY()
        self.update_count = 0
        self.last_update_time = 0

    def create_death_explosion(
        self,
        world_x: int,
        world_y: int,
        colors: list[tuple[int, int, int]],
        particle_count: int = None,
    ) -> None:
        """
        Create an explosive particle effect at the given world position.

        Args:
            world_x: World X coordinate of explosion center
            world_y: World Y coordinate of explosion center
            colors: List of RGB colors sampled from sprite
            particle_count: Number of particles to spawn (default from config)
        """
        if particle_count is None:
            particle_count = GameConfig.PARTICLE_COUNT_DEFAULT()
        current_time = time.time()

        # Ensure we have colors to work with
        if not colors:
            # Caller should always provide colors - this indicates a bug
            logging.error("create_death_explosion called with empty colors list")
            colors = [FALLBACK_WHITE]

        for _ in range(particle_count):
            # Random angle for radial burst
            angle = random.uniform(0, 2 * math.pi)

            # Random speed with variation from config
            speed = random.uniform(
                GameConfig.PARTICLE_VELOCITY_MIN(), GameConfig.PARTICLE_VELOCITY_MAX()
            )

            # Calculate velocity components - add upward bias for explosion
            velocity_x = math.cos(angle) * speed
            velocity_y = math.sin(angle) * speed - GameConfig.PARTICLE_UPWARD_BIAS()

            # Choose random color from palette
            color = random.choice(colors)

            # Add color variation from config
            color_var = GameConfig.PARTICLE_COLOR_VARIATION()
            varied_color = tuple(
                max(0, min(255, c + random.randint(-color_var, color_var))) for c in color
            )

            # Random particle size from config
            size = random.randint(GameConfig.PARTICLE_SIZE_MIN(), GameConfig.PARTICLE_SIZE_MAX())

            # Random lifetime from config
            lifetime = random.uniform(
                GameConfig.PARTICLE_LIFETIME_MIN(), GameConfig.PARTICLE_LIFETIME_MAX()
            )

            # Create particle at explosion center
            particle = Particle(
                x=float(world_x),
                y=float(world_y),
                velocity_x=velocity_x,
                velocity_y=velocity_y,
                color=varied_color,
                size=size,
                birth_time=current_time,
                lifetime=lifetime,
            )

            self.particles.append(particle)

        # Log only in debug mode
        if logging.getLogger().isEnabledFor(logging.DEBUG):
            if len(self.particles) > 0:
                logging.debug(
                    f"Created {particle_count} particles at ({world_x}, {world_y}) with colors: {colors[:3]}"
                )
                self.explosion_start_time = current_time
                self.explosion_expected_duration = max(p.lifetime for p in self.particles)

    def update(self, delta_time: float) -> None:
        """
        Update all particles with physics simulation.

        Args:
            delta_time: Time elapsed since last update (seconds)
        """
        current_time = time.time()

        # Log update frequency only in debug mode
        if logging.getLogger().isEnabledFor(logging.DEBUG):
            self.update_count += 1
            if current_time - self.last_update_time > 1.0:
                if len(self.particles) > 0:
                    logging.debug(
                        f"Update rate: {self.update_count} updates/sec, {len(self.particles)} active particles"
                    )
                self.update_count = 0
                self.last_update_time = current_time

        # Remove dead particles
        self.particles = [p for p in self.particles if p.is_alive(current_time)]

        # Update living particles
        for particle in self.particles:
            # Apply gravity to vertical velocity
            particle.velocity_y += self.gravity * delta_time

            # Update position based on velocity
            particle.x += particle.velocity_x * delta_time
            particle.y += particle.velocity_y * delta_time

    def render(
        self,
        sdl_renderer,
        camera_offset_x: int,
        camera_offset_y: int,
        tile_width: int,
        tile_height: int,
        viewport_width: int,
        viewport_height: int,
        viewport_pixel_width: int,
        viewport_pixel_height: int,
    ) -> None:
        """
        Render all particles using SDL primitives.

        Args:
            sdl_renderer: SDL renderer object
            camera_offset_x: Camera X offset in world tiles
            camera_offset_y: Camera Y offset in world tiles
            tile_width: Width of one tile in pixels
            tile_height: Height of one tile in pixels
            viewport_width: Viewport width in tiles
            viewport_height: Viewport height in tiles
            viewport_pixel_width: Viewport width in pixels
            viewport_pixel_height: Viewport height in pixels
        """
        current_time = time.time()

        # Calculate viewport boundaries in world coordinates
        viewport_left = camera_offset_x
        viewport_top = camera_offset_y
        viewport_right = camera_offset_x + viewport_width
        viewport_bottom = camera_offset_y + viewport_height

        particles_rendered = 0
        particles_culled = 0
        for particle in self.particles:
            # Skip if particle is outside viewport
            if (
                particle.x < viewport_left
                or particle.x >= viewport_right
                or particle.y < viewport_top
                or particle.y >= viewport_bottom
            ):
                particles_culled += 1
                continue

            # Convert world coordinates to screen pixels
            screen_x = int((particle.x - camera_offset_x) * tile_width)
            screen_y = int((particle.y - camera_offset_y) * tile_height)

            # Clamp to viewport boundaries (particles stop at edges)
            screen_x = max(0, min(viewport_pixel_width - particle.size, screen_x))
            screen_y = max(0, min(viewport_pixel_height - particle.size, screen_y))

            # Get current alpha for fade-out effect
            alpha = particle.get_alpha(current_time)
            if alpha <= 0:
                continue

            # Set draw color with alpha
            r, g, b = particle.color
            sdl_renderer.draw_color = (r, g, b, alpha)

            # Set blend mode for alpha blending
            from tcod.sdl.render import BlendMode

            original_blend = sdl_renderer.draw_blend_mode
            sdl_renderer.draw_blend_mode = BlendMode.BLEND

            # Draw particle as filled rectangle
            # SDL fill_rect takes a tuple: (x, y, width, height)
            particle_rect = (screen_x, screen_y, particle.size, particle.size)
            sdl_renderer.fill_rect(particle_rect)

            # Restore original blend mode
            sdl_renderer.draw_blend_mode = original_blend
            particles_rendered += 1

        # Only log if we have a lot of particles for performance monitoring
        if len(self.particles) > 200:
            logging.debug(
                f"Particle render: {particles_rendered} rendered, {particles_culled} culled"
            )

    def clear(self) -> None:
        """Clear all particles (useful for game state transitions)."""
        self.particles.clear()

    def get_particle_count(self) -> int:
        """Get the current number of active particles."""
        return len(self.particles)
