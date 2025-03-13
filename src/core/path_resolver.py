from pathlib import Path

class PathResolver:
    PROJECT_ROOT = Path("/project")
    CACHE_DIR = PROJECT_ROOT / "particle_cache"
    EXPORT_DIR = PROJECT_ROOT / "particle-graph"

    @staticmethod
    def resolve_path(path: str, base: Path = PROJECT_ROOT) -> Path:
        """Resolve a path relative to a base, returning a normalized Path object."""
        return (base / path).resolve()

    @staticmethod
    def relative_to_project(path: str) -> str:
        """Return a path relative to PROJECT_ROOT as a string."""
        return str(Path(path).relative_to(PathResolver.PROJECT_ROOT))

    @staticmethod
    def cache_path(filename: str) -> Path:
        """Return a path in the cache directory."""
        return PathResolver.CACHE_DIR / filename

    @staticmethod
    def export_path(filename: str) -> Path:
        """Return a path in the export directory."""
        return PathResolver.EXPORT_DIR / filename