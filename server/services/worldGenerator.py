"""
World Generator Service
Generates procedural worlds with configurable parameters for the Roam server.
"""
import random
import json
from typing import Dict, List, Tuple, Optional


class BiomeType:
    """Biome types available in the world"""
    GRASSLAND = "grassland"
    FOREST = "forest"
    JUNGLE = "jungle"
    MOUNTAIN = "mountain"


class WorldGenerator:
    """Generates procedural worlds with biomes, terrain, and resources"""
    
    def __init__(self, seed: Optional[int] = None, grid_size: int = 17):
        """
        Initialize the world generator.
        
        Args:
            seed: Random seed for reproducible world generation
            grid_size: Size of the grid for each room
        """
        self.seed = seed if seed is not None else random.randint(0, 999999)
        self.grid_size = grid_size
        self.random = random.Random(self.seed)
        
    def generate_world_config(self) -> Dict:
        """
        Generate world configuration.
        
        Returns:
            Dictionary containing world configuration
        """
        return {
            "seed": self.seed,
            "grid_size": self.grid_size,
            "biomes": [
                BiomeType.GRASSLAND,
                BiomeType.FOREST,
                BiomeType.JUNGLE,
                BiomeType.MOUNTAIN
            ]
        }
    
    def generate_room_data(self, x: int, y: int) -> Dict:
        """
        Generate room data for a specific coordinate.
        
        Args:
            x: X coordinate of the room
            y: Y coordinate of the room
            
        Returns:
            Dictionary containing room data
        """
        # Use coordinate-based seed for deterministic generation
        coord_seed = self.seed + x * 1000 + y
        coord_random = random.Random(coord_seed)
        
        # Select biome based on coordinates and world seed
        biome = self._select_biome(x, y, coord_random)
        
        # Generate terrain features
        terrain_features = self._generate_terrain_features(biome, coord_random)
        
        # Generate resources
        resources = self._generate_resources(biome, coord_random)
        
        # Generate environmental objects
        environmental_objects = self._generate_environmental_objects(biome, coord_random)
        
        # Get background color for biome
        background_color = self._get_biome_background_color(biome, coord_random)
        
        return {
            "x": x,
            "y": y,
            "biome": biome,
            "background_color": background_color,
            "terrain_features": terrain_features,
            "resources": resources,
            "environmental_objects": environmental_objects,
            "grid_size": self.grid_size
        }
    
    def _select_biome(self, x: int, y: int, rng: random.Random) -> str:
        """
        Select biome based on coordinates using perlin-like noise simulation.
        
        Args:
            x: X coordinate
            y: Y coordinate
            rng: Random number generator
            
        Returns:
            Biome type string
        """
        # Simple noise-like function using coordinates
        distance_from_origin = (x * x + y * y) ** 0.5
        noise_value = (rng.random() + (x % 3) * 0.3 + (y % 3) * 0.3) % 1.0
        
        # Biome distribution based on distance and noise
        if distance_from_origin < 5:
            # Near origin: more grasslands
            if noise_value < 0.6:
                return BiomeType.GRASSLAND
            elif noise_value < 0.8:
                return BiomeType.FOREST
            elif noise_value < 0.95:
                return BiomeType.JUNGLE
            else:
                return BiomeType.MOUNTAIN
        elif distance_from_origin < 15:
            # Medium distance: balanced
            if noise_value < 0.35:
                return BiomeType.GRASSLAND
            elif noise_value < 0.6:
                return BiomeType.FOREST
            elif noise_value < 0.85:
                return BiomeType.JUNGLE
            else:
                return BiomeType.MOUNTAIN
        else:
            # Far from origin: more mountains
            if noise_value < 0.2:
                return BiomeType.GRASSLAND
            elif noise_value < 0.4:
                return BiomeType.FOREST
            elif noise_value < 0.6:
                return BiomeType.JUNGLE
            else:
                return BiomeType.MOUNTAIN
    
    def _get_biome_background_color(self, biome: str, rng: random.Random) -> Tuple[int, int, int]:
        """Get background color for a biome with some variation."""
        if biome == BiomeType.GRASSLAND:
            return (
                rng.randint(200, 210),
                rng.randint(130, 140),
                rng.randint(60, 70)
            )
        elif biome == BiomeType.FOREST:
            return (
                rng.randint(200, 210),
                rng.randint(130, 140),
                rng.randint(60, 70)
            )
        elif biome == BiomeType.JUNGLE:
            return (
                rng.randint(200, 210),
                rng.randint(130, 140),
                rng.randint(60, 70)
            )
        elif biome == BiomeType.MOUNTAIN:
            return (
                rng.randint(100, 110),
                rng.randint(100, 110),
                rng.randint(100, 110)
            )
        else:
            return (0, 0, 0)
    
    def _generate_terrain_features(self, biome: str, rng: random.Random) -> List[Dict]:
        """Generate terrain features based on biome."""
        features = []
        
        if biome == BiomeType.GRASSLAND:
            # Grass coverage
            grass_density = rng.uniform(0.85, 0.95)
            features.append({
                "type": "grass",
                "density": grass_density
            })
            # Occasional rocks
            rock_density = rng.uniform(0.01, 0.05)
            features.append({
                "type": "stone",
                "density": rock_density
            })
            
        elif biome == BiomeType.FOREST:
            # Grass and trees
            features.append({
                "type": "grass",
                "density": rng.uniform(0.85, 0.95)
            })
            tree_count = rng.randint(3, 6)
            features.append({
                "type": "oak_tree",
                "count": tree_count
            })
            
        elif biome == BiomeType.JUNGLE:
            # Dense vegetation
            features.append({
                "type": "leaves",
                "density": rng.uniform(0.85, 0.95)
            })
            tree_count = rng.randint(8, 15)
            features.append({
                "type": "jungle_tree",
                "count": tree_count
            })
            
        elif biome == BiomeType.MOUNTAIN:
            # Rocks everywhere
            features.append({
                "type": "stone",
                "density": 1.0
            })
        
        return features
    
    def _generate_resources(self, biome: str, rng: random.Random) -> List[Dict]:
        """Generate resource distribution based on biome."""
        resources = []
        
        if biome == BiomeType.GRASSLAND:
            # Occasional food
            if rng.random() < 0.1:
                resources.append({
                    "type": "apple",
                    "count": rng.randint(1, 3)
                })
                
        elif biome == BiomeType.FOREST:
            # Apples near trees
            apple_count = rng.randint(2, 5)
            resources.append({
                "type": "apple",
                "count": apple_count
            })
            
        elif biome == BiomeType.JUNGLE:
            # Bananas
            banana_count = rng.randint(4, 8)
            resources.append({
                "type": "banana",
                "count": banana_count
            })
            
        elif biome == BiomeType.MOUNTAIN:
            # Ore deposits
            if rng.random() < 0.3:
                ore_type = "coal_ore" if rng.random() < 0.5 else "iron_ore"
                resources.append({
                    "type": ore_type,
                    "count": rng.randint(1, 3)
                })
        
        return resources
    
    def _generate_environmental_objects(self, biome: str, rng: random.Random) -> List[Dict]:
        """Generate environmental objects and hazards."""
        objects = []
        
        # Add animals based on biome
        if biome == BiomeType.GRASSLAND:
            # Chickens
            if rng.random() < 0.25:
                chicken_count = rng.randint(1, 3)
                objects.append({
                    "type": "chicken",
                    "count": chicken_count
                })
                
        elif biome == BiomeType.FOREST:
            # Chickens and bears
            if rng.random() < 0.25:
                chicken_count = rng.randint(1, 3)
                objects.append({
                    "type": "chicken",
                    "count": chicken_count
                })
            if rng.random() < 0.1:
                objects.append({
                    "type": "bear",
                    "count": 1
                })
                
        elif biome == BiomeType.JUNGLE:
            # More wildlife
            if rng.random() < 0.3:
                chicken_count = rng.randint(2, 4)
                objects.append({
                    "type": "chicken",
                    "count": chicken_count
                })
        
        return objects
    
    def generate_world_overview(self, radius: int = 10) -> Dict:
        """
        Generate an overview of the world in a radius around the origin.
        
        Args:
            radius: Radius around origin to generate overview for
            
        Returns:
            Dictionary with world overview data
        """
        rooms = []
        biome_distribution = {
            BiomeType.GRASSLAND: 0,
            BiomeType.FOREST: 0,
            BiomeType.JUNGLE: 0,
            BiomeType.MOUNTAIN: 0
        }
        
        for x in range(-radius, radius + 1):
            for y in range(-radius, radius + 1):
                room_data = self.generate_room_data(x, y)
                rooms.append({
                    "x": x,
                    "y": y,
                    "biome": room_data["biome"]
                })
                biome_distribution[room_data["biome"]] += 1
        
        return {
            "seed": self.seed,
            "grid_size": self.grid_size,
            "radius": radius,
            "total_rooms": len(rooms),
            "biome_distribution": biome_distribution,
            "rooms": rooms
        }
