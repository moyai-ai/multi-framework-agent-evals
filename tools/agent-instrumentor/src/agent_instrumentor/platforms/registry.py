"""Dynamic platform registry for auto-discovering observability platforms."""

import importlib
import inspect
import pkgutil
from pathlib import Path
from typing import Dict, List, Optional
from .base import ObservabilityPlatform, PlatformInfo


class PlatformRegistry:
    """Registry for observability platforms with auto-discovery."""

    def __init__(self):
        self._platforms: Dict[str, ObservabilityPlatform] = {}
        self._auto_discovered = False

    def register(self, platform: ObservabilityPlatform) -> None:
        """Manually register a platform."""
        self._platforms[platform.name] = platform

    def get(self, name: str) -> Optional[ObservabilityPlatform]:
        """Get a platform by name."""
        if not self._auto_discovered:
            self.auto_discover()

        return self._platforms.get(name)

    def list_platforms(self) -> List[PlatformInfo]:
        """List all registered platforms."""
        if not self._auto_discovered:
            self.auto_discover()

        return [platform.get_info() for platform in self._platforms.values()]

    def auto_discover(self) -> None:
        """Auto-discover platforms from the platforms directory."""
        if self._auto_discovered:
            return

        # Get the platforms package directory
        platforms_dir = Path(__file__).parent

        # Iterate through all Python files in the directory
        for file_path in platforms_dir.glob("*.py"):
            # Skip special files
            if file_path.name.startswith('_') or file_path.name in ['base.py', 'registry.py']:
                continue

            try:
                # Import the module
                module_name = f"agent_instrumentor.platforms.{file_path.stem}"
                module = importlib.import_module(module_name)

                # Find classes that implement ObservabilityPlatform protocol
                for name, obj in inspect.getmembers(module, inspect.isclass):
                    # Skip imported classes
                    if obj.__module__ != module.__name__:
                        continue

                    # Check if it has all required methods (duck typing)
                    required_attrs = ['name', 'display_name', 'get_dependencies',
                                      'get_env_vars', 'generate_instrumentation']

                    if all(hasattr(obj, attr) for attr in required_attrs):
                        try:
                            # Instantiate the platform
                            platform_instance = obj()

                            # Register it
                            self._platforms[platform_instance.name] = platform_instance
                            print(f"[Platform Registry] Discovered: {platform_instance.display_name}")

                        except Exception as e:
                            print(f"[Platform Registry] Failed to instantiate {name}: {e}")

            except Exception as e:
                print(f"[Platform Registry] Failed to import {file_path.name}: {e}")

        self._auto_discovered = True

    def has_platform(self, name: str) -> bool:
        """Check if a platform is registered."""
        if not self._auto_discovered:
            self.auto_discover()

        return name in self._platforms


# Global registry instance
platform_registry = PlatformRegistry()


# Convenience functions
def get_platform(name: str) -> Optional[ObservabilityPlatform]:
    """Get a platform by name."""
    return platform_registry.get(name)


def list_platforms() -> List[PlatformInfo]:
    """List all available platforms."""
    return platform_registry.list_platforms()


def register_platform(platform: ObservabilityPlatform) -> None:
    """Register a platform."""
    platform_registry.register(platform)
