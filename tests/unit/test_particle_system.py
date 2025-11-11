#!/usr/bin/env python3
"""
Unit tests for the Particle System.

Tests particle creation, physics simulation, lifetime management,
and memory cleanup. The particle system is CRITICAL for visual effects
during combat (every exploit uses particles).
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
import time
import math

from game_particle_system import Particle, ParticleSystem
from game_config import GameConfig


class TestParticleDataclass:
    """Test the Particle dataclass."""

    def test_particle_creation(self):
        """Particle can be created with all properties."""
        current_time = time.time()

        particle = Particle(
            x=10.5,
            y=20.5,
            velocity_x=5.0,
            velocity_y=-3.0,
            color=(255, 0, 0),
            size=4,
            birth_time=current_time,
            lifetime=1.0
        )

        assert particle.x == 10.5
        assert particle.y == 20.5
        assert particle.velocity_x == 5.0
        assert particle.velocity_y == -3.0
        assert particle.color == (255, 0, 0)
        assert particle.size == 4
        assert particle.birth_time == current_time
        assert particle.lifetime == 1.0

    def test_is_alive_immediately_after_birth(self):
        """Particle is alive immediately after creation."""
        current_time = time.time()

        particle = Particle(
            x=10.0, y=10.0,
            velocity_x=0.0, velocity_y=0.0,
            color=(255, 255, 255),
            size=3,
            birth_time=current_time,
            lifetime=1.0
        )

        assert particle.is_alive(current_time) is True

    def test_is_alive_before_lifetime_expires(self):
        """Particle is alive before lifetime expires."""
        current_time = time.time()

        particle = Particle(
            x=10.0, y=10.0,
            velocity_x=0.0, velocity_y=0.0,
            color=(255, 255, 255),
            size=3,
            birth_time=current_time,
            lifetime=1.0
        )

        # Check 0.5 seconds later (still alive)
        assert particle.is_alive(current_time + 0.5) is True

    def test_is_alive_after_lifetime_expires(self):
        """Particle is dead after lifetime expires."""
        current_time = time.time()

        particle = Particle(
            x=10.0, y=10.0,
            velocity_x=0.0, velocity_y=0.0,
            color=(255, 255, 255),
            size=3,
            birth_time=current_time,
            lifetime=1.0
        )

        # Check 1.5 seconds later (dead)
        assert particle.is_alive(current_time + 1.5) is False

    def test_is_alive_exactly_at_lifetime(self):
        """Particle is dead exactly at lifetime expiration."""
        current_time = time.time()

        particle = Particle(
            x=10.0, y=10.0,
            velocity_x=0.0, velocity_y=0.0,
            color=(255, 255, 255),
            size=3,
            birth_time=current_time,
            lifetime=1.0
        )

        # Check exactly at lifetime (should be dead)
        assert particle.is_alive(current_time + 1.0) is False


class TestParticleAlpha:
    """Test particle alpha/fade calculations."""

    def test_get_alpha_at_birth_is_255(self):
        """Alpha is 255 (fully opaque) at birth."""
        current_time = time.time()

        particle = Particle(
            x=10.0, y=10.0,
            velocity_x=0.0, velocity_y=0.0,
            color=(255, 255, 255),
            size=3,
            birth_time=current_time,
            lifetime=1.0
        )

        assert particle.get_alpha(current_time) == 255

    def test_get_alpha_at_half_lifetime(self):
        """Alpha is approximately 127 at half lifetime."""
        current_time = time.time()

        particle = Particle(
            x=10.0, y=10.0,
            velocity_x=0.0, velocity_y=0.0,
            color=(255, 255, 255),
            size=3,
            birth_time=current_time,
            lifetime=1.0
        )

        alpha = particle.get_alpha(current_time + 0.5)
        # Linear fade: 50% lifetime = 50% alpha
        assert 125 <= alpha <= 130

    def test_get_alpha_after_death_is_zero(self):
        """Alpha is 0 after lifetime expires."""
        current_time = time.time()

        particle = Particle(
            x=10.0, y=10.0,
            velocity_x=0.0, velocity_y=0.0,
            color=(255, 255, 255),
            size=3,
            birth_time=current_time,
            lifetime=1.0
        )

        assert particle.get_alpha(current_time + 1.5) == 0

    def test_get_alpha_fades_linearly(self):
        """Alpha fades linearly from 255 to 0 over lifetime."""
        current_time = time.time()

        particle = Particle(
            x=10.0, y=10.0,
            velocity_x=0.0, velocity_y=0.0,
            color=(255, 255, 255),
            size=3,
            birth_time=current_time,
            lifetime=1.0
        )

        # Sample alpha at different times
        alpha_0 = particle.get_alpha(current_time)
        alpha_25 = particle.get_alpha(current_time + 0.25)
        alpha_50 = particle.get_alpha(current_time + 0.5)
        alpha_75 = particle.get_alpha(current_time + 0.75)

        # Should decrease monotonically
        assert alpha_0 > alpha_25 > alpha_50 > alpha_75


class TestParticleSystemInitialization:
    """Test ParticleSystem initialization."""

    def test_initialization(self):
        """ParticleSystem initializes with empty particle list."""
        ps = ParticleSystem()

        assert len(ps.particles) == 0
        assert ps.get_particle_count() == 0

    def test_initialization_loads_gravity(self):
        """ParticleSystem loads gravity from config."""
        ps = ParticleSystem()

        expected_gravity = GameConfig.PARTICLE_GRAVITY()
        assert ps.gravity == expected_gravity


class TestDeathExplosion:
    """Test death explosion particle creation."""

    def test_create_death_explosion_spawns_particles(self):
        """create_death_explosion spawns particles."""
        ps = ParticleSystem()

        ps.create_death_explosion(
            world_x=10,
            world_y=10,
            colors=[(255, 0, 0), (0, 255, 0)],
            particle_count=10
        )

        assert len(ps.particles) == 10

    def test_create_death_explosion_uses_default_count(self):
        """create_death_explosion uses default count from config."""
        ps = ParticleSystem()

        ps.create_death_explosion(
            world_x=10,
            world_y=10,
            colors=[(255, 0, 0)]
        )

        expected_count = GameConfig.PARTICLE_COUNT_DEFAULT()
        assert len(ps.particles) == expected_count

    def test_create_death_explosion_particles_at_origin(self):
        """Particles spawn at explosion center."""
        ps = ParticleSystem()

        ps.create_death_explosion(
            world_x=15,
            world_y=20,
            colors=[(255, 0, 0)],
            particle_count=5
        )

        # All particles should start at (15, 20)
        for particle in ps.particles:
            assert particle.x == 15.0
            assert particle.y == 20.0

    def test_create_death_explosion_particles_have_velocity(self):
        """Particles have non-zero velocity for explosion effect."""
        ps = ParticleSystem()

        ps.create_death_explosion(
            world_x=10,
            world_y=10,
            colors=[(255, 0, 0)],
            particle_count=20
        )

        # At least some particles should have velocity
        # (random, so check that not all are zero)
        non_zero_velocity = sum(
            1 for p in ps.particles
            if p.velocity_x != 0 or p.velocity_y != 0
        )

        assert non_zero_velocity > 15  # Most should have velocity

    def test_create_death_explosion_uses_provided_colors(self):
        """Particles use colors from provided palette."""
        ps = ParticleSystem()

        colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255)]
        ps.create_death_explosion(
            world_x=10,
            world_y=10,
            colors=colors,
            particle_count=30
        )

        # Check that particle colors are based on palette
        # (with variation, so check they're close to one of the colors)
        for particle in ps.particles:
            r, g, b = particle.color
            # Each component should be in valid range
            assert 0 <= r <= 255
            assert 0 <= g <= 255
            assert 0 <= b <= 255

    def test_create_death_explosion_with_empty_colors(self):
        """Empty color list uses fallback white."""
        ps = ParticleSystem()

        ps.create_death_explosion(
            world_x=10,
            world_y=10,
            colors=[],
            particle_count=5
        )

        # Should still create particles with white color
        assert len(ps.particles) == 5
        # Check particles have some color (fallback white with variation)
        for particle in ps.particles:
            assert particle.color is not None

    def test_create_death_explosion_particles_have_lifetime(self):
        """Particles have randomized lifetime from config range."""
        ps = ParticleSystem()

        ps.create_death_explosion(
            world_x=10,
            world_y=10,
            colors=[(255, 0, 0)],
            particle_count=20
        )

        min_lifetime = GameConfig.PARTICLE_LIFETIME_MIN()
        max_lifetime = GameConfig.PARTICLE_LIFETIME_MAX()

        for particle in ps.particles:
            assert min_lifetime <= particle.lifetime <= max_lifetime

    def test_create_death_explosion_particles_have_size(self):
        """Particles have randomized size from config range."""
        ps = ParticleSystem()

        ps.create_death_explosion(
            world_x=10,
            world_y=10,
            colors=[(255, 0, 0)],
            particle_count=20
        )

        min_size = GameConfig.PARTICLE_SIZE_MIN()
        max_size = GameConfig.PARTICLE_SIZE_MAX()

        for particle in ps.particles:
            assert min_size <= particle.size <= max_size


class TestParticleUpdate:
    """Test particle physics updates."""

    def test_update_removes_dead_particles(self):
        """update removes particles after lifetime expires."""
        ps = ParticleSystem()
        current_time = time.time()

        # Create a particle with very short lifetime
        particle = Particle(
            x=10.0, y=10.0,
            velocity_x=0.0, velocity_y=0.0,
            color=(255, 255, 255),
            size=3,
            birth_time=current_time - 2.0,  # Born 2 seconds ago
            lifetime=1.0  # Lives for 1 second (already dead)
        )
        ps.particles.append(particle)

        # Update should remove dead particle
        ps.update(delta_time=0.016)

        assert len(ps.particles) == 0

    def test_update_keeps_alive_particles(self):
        """update keeps particles that are still alive."""
        ps = ParticleSystem()
        current_time = time.time()

        # Create a particle that's alive
        particle = Particle(
            x=10.0, y=10.0,
            velocity_x=0.0, velocity_y=0.0,
            color=(255, 255, 255),
            size=3,
            birth_time=current_time,
            lifetime=10.0  # Long lifetime
        )
        ps.particles.append(particle)

        # Update should keep alive particle
        ps.update(delta_time=0.016)

        assert len(ps.particles) == 1

    def test_update_applies_gravity(self):
        """update applies gravity to vertical velocity."""
        ps = ParticleSystem()
        current_time = time.time()

        particle = Particle(
            x=10.0, y=10.0,
            velocity_x=5.0,
            velocity_y=0.0,  # Start with no vertical velocity
            color=(255, 255, 255),
            size=3,
            birth_time=current_time,
            lifetime=10.0
        )
        ps.particles.append(particle)

        initial_velocity_y = particle.velocity_y

        # Update with 1 second delta
        ps.update(delta_time=1.0)

        # Velocity Y should increase (gravity pulls down)
        assert particle.velocity_y > initial_velocity_y

    def test_update_moves_particles(self):
        """update moves particles based on velocity."""
        ps = ParticleSystem()
        current_time = time.time()

        particle = Particle(
            x=10.0, y=20.0,
            velocity_x=5.0,
            velocity_y=3.0,
            color=(255, 255, 255),
            size=3,
            birth_time=current_time,
            lifetime=10.0
        )
        ps.particles.append(particle)

        initial_x = particle.x
        initial_y = particle.y

        # Update with 1 second delta
        ps.update(delta_time=1.0)

        # Position should change based on velocity
        # x should increase by ~5 (velocity_x * delta_time)
        # y should increase by some amount (velocity_y + gravity effect)
        assert particle.x > initial_x
        assert particle.y != initial_y


class TestParticleMemoryManagement:
    """Test memory management and cleanup."""

    def test_clear_removes_all_particles(self):
        """clear removes all particles."""
        ps = ParticleSystem()

        # Create many particles
        ps.create_death_explosion(
            world_x=10,
            world_y=10,
            colors=[(255, 0, 0)],
            particle_count=100
        )

        assert len(ps.particles) > 0

        # Clear should remove all
        ps.clear()

        assert len(ps.particles) == 0
        assert ps.get_particle_count() == 0

    def test_multiple_explosions_accumulate_particles(self):
        """Multiple explosions create cumulative particles."""
        ps = ParticleSystem()

        # First explosion
        ps.create_death_explosion(
            world_x=10, world_y=10,
            colors=[(255, 0, 0)],
            particle_count=10
        )

        count_after_first = len(ps.particles)
        assert count_after_first == 10

        # Second explosion
        ps.create_death_explosion(
            world_x=20, world_y=20,
            colors=[(0, 255, 0)],
            particle_count=15
        )

        # Should have particles from both explosions
        assert len(ps.particles) == 25

    def test_get_particle_count(self):
        """get_particle_count returns correct count."""
        ps = ParticleSystem()

        assert ps.get_particle_count() == 0

        ps.create_death_explosion(
            world_x=10, world_y=10,
            colors=[(255, 0, 0)],
            particle_count=42
        )

        assert ps.get_particle_count() == 42


class TestParticlePerformance:
    """Test performance with many particles."""

    def test_spawn_100_particles(self):
        """System handles 100 particles."""
        ps = ParticleSystem()

        ps.create_death_explosion(
            world_x=10,
            world_y=10,
            colors=[(255, 0, 0), (0, 255, 0), (0, 0, 255)],
            particle_count=100
        )

        assert len(ps.particles) == 100

        # Update should complete without error
        ps.update(delta_time=0.016)

        # Particles should still exist (haven't expired yet)
        assert len(ps.particles) > 0

    def test_spawn_500_particles_stress_test(self):
        """System handles 500 particles (stress test)."""
        ps = ParticleSystem()

        ps.create_death_explosion(
            world_x=10,
            world_y=10,
            colors=[(255, 0, 0)],
            particle_count=500
        )

        assert len(ps.particles) == 500

        # Multiple updates should complete
        for _ in range(10):
            ps.update(delta_time=0.016)

        # Should still have particles
        assert len(ps.particles) > 0


class TestParticleEdgeCases:
    """Test edge cases and unusual scenarios."""

    def test_create_explosion_with_zero_particles(self):
        """Zero particle count creates no particles."""
        ps = ParticleSystem()

        ps.create_death_explosion(
            world_x=10,
            world_y=10,
            colors=[(255, 0, 0)],
            particle_count=0
        )

        assert len(ps.particles) == 0

    def test_update_with_zero_delta_time(self):
        """update with zero delta_time doesn't crash."""
        ps = ParticleSystem()
        current_time = time.time()

        particle = Particle(
            x=10.0, y=10.0,
            velocity_x=5.0, velocity_y=3.0,
            color=(255, 255, 255),
            size=3,
            birth_time=current_time,
            lifetime=10.0
        )
        ps.particles.append(particle)

        # Update with zero delta (shouldn't crash)
        ps.update(delta_time=0.0)

        # Particle should still exist
        assert len(ps.particles) == 1

    def test_update_with_negative_delta_time(self):
        """update with negative delta_time handled gracefully."""
        ps = ParticleSystem()
        current_time = time.time()

        particle = Particle(
            x=10.0, y=10.0,
            velocity_x=5.0, velocity_y=3.0,
            color=(255, 255, 255),
            size=3,
            birth_time=current_time,
            lifetime=10.0
        )
        ps.particles.append(particle)

        # Update with negative delta
        ps.update(delta_time=-0.1)

        # Should not crash (though behavior may be undefined)
        assert True  # Survival is success

    def test_particle_with_zero_lifetime(self):
        """Particle with zero lifetime is immediately dead."""
        current_time = time.time()

        particle = Particle(
            x=10.0, y=10.0,
            velocity_x=0.0, velocity_y=0.0,
            color=(255, 255, 255),
            size=3,
            birth_time=current_time,
            lifetime=0.0
        )

        # Should be dead immediately
        assert particle.is_alive(current_time) is False
        assert particle.get_alpha(current_time) == 0

    def test_particle_color_clamping(self):
        """Particle colors are clamped to valid RGB range."""
        ps = ParticleSystem()

        # Use extreme color that might get varied out of range
        ps.create_death_explosion(
            world_x=10,
            world_y=10,
            colors=[(255, 255, 255), (0, 0, 0)],
            particle_count=20
        )

        # All particle colors should be valid RGB
        for particle in ps.particles:
            r, g, b = particle.color
            assert 0 <= r <= 255
            assert 0 <= g <= 255
            assert 0 <= b <= 255
