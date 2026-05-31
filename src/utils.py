import traceback
from random import random, shuffle
from typing import Callable

from gdpc.block import Block
from gdpc.editor import Editor

TREE_KEYWORDS = ["leaves", "log", "wood"]

# =============================================================================
# PALETTES
# =============================================================================

_DEFAULT = {
    "foundation": [Block("stone_bricks"), Block("cracked_stone_bricks")],
    "pillar": [Block("stripped_oak_log"), Block("stripped_oak_log")],
    "wall": [Block("oak_planks"), Block("birch_planks")],
    "roof_stairs": [Block("oak_stairs"), Block("oak_stairs")],
    "roof_block": [Block("oak_planks"), Block("oak_planks")],
    "street": [Block("dirt_path")],
    "pirate_foundation": [Block("stone_bricks"), Block("cracked_stone_bricks")],
    "pirate_pillar": [Block("stripped_mangrove_log"), Block("birch_planks")],
    "pirate_wall": [Block("white_concrete"), Block("mangrove_log")],
    
    "pirate_roof_stairs": [Block("warped_stairs"), Block("warped_stairs")],
    "pirate_roof_slab": [Block("deepslate_brick_slab"), Block("deepslate_brick_slab")],
    "pirate_roof_block": [Block("warped_planks"), Block("deepslate_bricks")],
    "pirate_door": [Block("mangrove_door")],
    "pirate_fence": [Block("mangrove_fence")],
    "pirate_trapdoor": [Block("warped_trapdoor")],
    "pirate_inner_stair": [Block("dark_oak_stairs")],
    "pirate_window": [Block("black_stained_glass_pane")],
    "manor_timber": [Block("mangrove_fence")],
    "manor_roof_stairs": [Block("warped_stairs"), Block("warped_stairs")],
    "manor_roof_slab": [Block("warped_slab"), Block("warped_slab")],
    "manor_roof_block": [Block("warped_planks"), Block("warped_planks")],
    
    "vil_base_stone": [Block("stone_bricks"), Block("cracked_stone_bricks")],
    "vil_base_stone_alt": [Block("cobbled_deepslate"), Block("tuff")],
    "vil_porch_slab": [Block("spruce_slab"), Block("dark_oak_slab")],
    "vil_pillar_wood": [Block("dark_oak_log"), Block("warped_stem")],
    "vil_beam_wood": [Block("stripped_dark_oak_log"), Block("stripped_warped_stem")],
    "vil_wall_wood": [Block("stripped_spruce_log"), Block("stripped_jungle_log")],
    "vil_shoji_block": [Block("bone_block"), Block("brown_mushroom_block")],
    "vil_shoji_trapdoor": [Block("cherry_trapdoor"), Block("warped_trapdoor")],
    "vil_roof_outline_stair": [Block("dark_oak_stairs"), Block("warped_stairs")],
    "vil_roof_outline_slab": [Block("dark_oak_slab"), Block("warped_slab")],
    "vil_roof_outline_block": [Block("dark_oak_planks"), Block("warped_planks")],
    "vil_roof_fill_stair": [Block("cherry_stairs"), Block("jungle_stairs")],
    "vil_roof_fill_slab": [Block("cherry_slab"), Block("jungle_slab")],
    "vil_roof_block": [Block("dark_oak_planks"), Block("warped_planks")],
}

_MEADOW = {
    "foundation": [Block("stone_bricks"), Block("mossy_stone_bricks")],
    "pillar": [Block("stripped_oak_log"), Block("stripped_birch_log")],
    "wall": [Block("oak_planks"), Block("white_wool")],
    "roof_stairs": [Block("birch_stairs"), Block("oak_stairs")],
    "roof_block": [Block("birch_planks"), Block("oak_planks")],
    "street": [Block("dirt_path")],
    "pirate_foundation": [Block("blackstone"), Block("cobbled_deepslate")],
    "pirate_pillar": [Block("stripped_mangrove_log"), Block("stripped_mangrove_log")],
    "pirate_wall":[Block("white_terracotta"), Block("yellow_terracotta")],
    "pirate_roof_stairs": [
        Block("deepslate_brick_stairs"),
        Block("deepslate_brick_stairs"),
    ],
    "pirate_roof_slab": [Block("deepslate_brick_slab"), Block("deepslate_brick_slab")],
    "pirate_roof_block": [Block("deepslate_bricks"), Block("deepslate_bricks")],
    "pirate_door": [Block("dark_oak_door")],
    "pirate_fence": [Block("spruce_fence")],
    "pirate_trapdoor": [Block("spruce_trapdoor")],
    "pirate_inner_stair": [Block("spruce_stairs")],
    "pirate_window": [Block("light_gray_stained_glass_pane")],
    "manor_timber": [Block("spruce_fence")],
    "manor_foundation": [Block("coal_block"), Block("polished_blackstone")],
    "manor_pillar": [Block("gold_block"), Block("stripped_oak_log")],
    "manor_wall": [Block("white_terracotta"), Block("yellow_terracotta")],
    "manor_roof_stairs": [
        Block("deepslate_tile_stairs"),
        Block("deepslate_tile_stairs"),
    ],
    "manor_roof_slab": [Block("deepslate_tile_slab"), Block("deepslate_tile_slab")],
    "manor_roof_block": [Block("deepslate_tiles"), Block("deepslate_tiles")],
    "manor_floor": [Block("oak_planks"), Block("dark_oak_planks")],
    # --- VILLAGER HOUSE (JAPANESE) ---
    "vil_base_stone": [Block("mossy_stone_bricks"), Block("stone_bricks")],
    "vil_base_stone_alt": [Block("cobblestone"), Block("mossy_cobblestone")],
    "vil_porch_slab": [Block("birch_slab"), Block("oak_slab")],
    "vil_pillar_wood": [Block("stripped_oak_log"), Block("mangrove_log")],
    "vil_beam_wood": [Block("stripped_birch_log"), Block("stripped_mangrove_log")],
    "vil_wall_wood": [Block("stripped_oak_log"), Block("stripped_jungle_log")],
    "vil_shoji_block": [Block("white_wool"), Block("green_wool")],
    "vil_shoji_trapdoor": [Block("birch_trapdoor"), Block("mangrove_trapdoor")],
    "vil_roof_outline_stair": [Block("oak_stairs"), Block("mangrove_stairs")],
    "vil_roof_outline_slab": [Block("oak_slab"), Block("mangrove_slab")],
    "vil_roof_outline_block": [Block("oak_planks"), Block("mangrove_planks")],
    "vil_roof_fill_stair": [Block("birch_stairs"), Block("jungle_stairs")],
    "vil_roof_fill_slab": [Block("birch_slab"), Block("jungle_slab")],
    "vil_roof_block": [Block("oak_planks"), Block("mangrove_planks")],
}

_CHERRY = {
    "foundation": [Block("stone_bricks"), Block("mossy_stone_bricks")],
    "pillar": [Block("stripped_cherry_log"), Block("cherry_log")],
    "wall": [Block("cherry_planks"), Block("white_terracotta")],
    "roof_stairs": [Block("cherry_stairs"), Block("cherry_stairs")],
    "roof_block": [Block("cherry_planks"), Block("cherry_planks")],
    "street": [Block("dirt_path")],
    "pirate_foundation": [Block("blackstone"), Block("cobbled_deepslate")],
    "pirate_pillar": [Block("dark_oak_log"), Block("stripped_cherry_log")],
    "pirate_wall": [Block("cherry_planks"), Block("dark_oak_planks")],
    "pirate_roof_stairs": [
        Block("deepslate_brick_stairs"),
        Block("deepslate_brick_stairs"),
    ],
    "pirate_roof_slab": [Block("deepslate_brick_slab"), Block("deepslate_brick_slab")],
    "pirate_roof_block": [Block("deepslate_bricks"), Block("deepslate_bricks")],
    "pirate_door": [Block("cherry_door")],
    "pirate_fence": [Block("cherry_fence")],
    "pirate_trapdoor": [Block("cherry_trapdoor")],
    "pirate_inner_stair": [Block("cherry_stairs")],
    "pirate_window": [Block("pink_stained_glass_pane")],
    "manor_timber": [Block("cherry_fence")],
    "manor_foundation": [Block("coal_block"), Block("obsidian")],
    "manor_pillar": [Block("gold_block"), Block("cherry_log")],
    "manor_wall": [Block("pink_terracotta"), Block("white_concrete")],
    "manor_roof_stairs": [
        Block("deepslate_tile_stairs"),
        Block("deepslate_tile_stairs"),
    ],
    "manor_roof_slab": [Block("deepslate_tile_slab"), Block("deepslate_tile_slab")],
    "manor_roof_block": [Block("deepslate_tiles"), Block("deepslate_tiles")],
    "manor_floor": [Block("cherry_planks"), Block("dark_oak_planks")],
    # --- VILLAGER HOUSE (JAPANESE) ---
    "vil_base_stone": [Block("calcite"), Block("tuff")],
    "vil_base_stone_alt": [Block("diorite"), Block("polished_diorite")],
    "vil_porch_slab": [Block("cherry_slab"), Block("crimson_slab")],
    "vil_pillar_wood": [Block("cherry_log"), Block("crimson_stem")],
    "vil_beam_wood": [Block("stripped_cherry_log"), Block("stripped_crimson_stem")],
    "vil_wall_wood": [Block("stripped_cherry_log"), Block("stripped_crimson_stem")],
    "vil_shoji_block": [Block("pink_wool"), Block("red_nether_bricks")],
    "vil_shoji_trapdoor": [Block("cherry_trapdoor"), Block("crimson_trapdoor")],
    "vil_roof_outline_stair": [Block("dark_oak_stairs"), Block("nether_brick_stairs")],
    "vil_roof_outline_slab": [Block("dark_oak_slab"), Block("nether_brick_slab")],
    "vil_roof_outline_block": [Block("dark_oak_planks"), Block("nether_bricks")],
    "vil_roof_fill_stair": [Block("cherry_stairs"), Block("crimson_stairs")],
    "vil_roof_fill_slab": [Block("cherry_slab"), Block("crimson_slab")],
    "vil_roof_block": [Block("cherry_planks"), Block("crimson_planks")],
}

_SAVANNA = {
    "foundation": [Block("cobblestone"), Block("mossy_cobblestone")],
    "pillar": [Block("stripped_acacia_log"), Block("acacia_log")],
    "wall": [Block("acacia_planks"), Block("terracotta")],
    "roof_stairs": [Block("acacia_stairs"), Block("acacia_stairs")],
    "roof_block": [Block("acacia_planks"), Block("acacia_planks")],
    "street": [Block("coarse_dirt")],
    "pirate_foundation": [Block("cobbled_deepslate"), Block("blackstone")],
    "pirate_pillar": [Block("dark_oak_log"), Block("acacia_log")],
    "pirate_wall": [Block("acacia_planks"), Block("dark_oak_planks")],
    "pirate_roof_stairs": [
        Block("deepslate_brick_stairs"),
        Block("deepslate_brick_stairs"),
    ],
    "pirate_roof_slab": [Block("deepslate_brick_slab"), Block("deepslate_brick_slab")],
    "pirate_roof_block": [Block("deepslate_bricks"), Block("deepslate_bricks")],
    "pirate_door": [Block("acacia_door")],
    "pirate_fence": [Block("acacia_fence")],
    "pirate_trapdoor": [Block("acacia_trapdoor")],
    "pirate_inner_stair": [Block("acacia_stairs")],
    "pirate_window": [Block("orange_stained_glass_pane")],
    "manor_timber": [Block("acacia_fence")],
    "manor_foundation": [Block("coal_block"), Block("polished_blackstone")],
    "manor_pillar": [Block("gold_block"), Block("orange_terracotta")],
    "manor_wall": [Block("terracotta"), Block("acacia_planks")],
    "manor_roof_stairs": [
        Block("deepslate_tile_stairs"),
        Block("deepslate_tile_stairs"),
    ],
    "manor_roof_slab": [Block("deepslate_tile_slab"), Block("deepslate_tile_slab")],
    "manor_roof_block": [Block("deepslate_tiles"), Block("deepslate_tiles")],
    "manor_floor": [Block("acacia_planks"), Block("dark_oak_planks")],
    # --- VILLAGER HOUSE (JAPANESE) ---
    "vil_base_stone": [Block("terracotta"), Block("brown_terracotta")],
    "vil_base_stone_alt": [Block("coarse_dirt"), Block("dirt")],
    "vil_porch_slab": [Block("acacia_slab"), Block("jungle_slab")],
    "vil_pillar_wood": [Block("acacia_log"), Block("jungle_log")],
    "vil_beam_wood": [Block("stripped_acacia_log"), Block("stripped_jungle_log")],
    "vil_wall_wood": [Block("stripped_acacia_log"), Block("stripped_jungle_log")],
    "vil_shoji_block": [Block("orange_terracotta"), Block("red_terracotta")],
    "vil_shoji_trapdoor": [Block("acacia_trapdoor"), Block("jungle_trapdoor")],
    "vil_roof_outline_stair": [Block("dark_oak_stairs"), Block("jungle_stairs")],
    "vil_roof_outline_slab": [Block("dark_oak_slab"), Block("jungle_slab")],
    "vil_roof_outline_block": [Block("dark_oak_planks"), Block("jungle_planks")],
    "vil_roof_fill_stair": [Block("acacia_stairs"), Block("jungle_stairs")],
    "vil_roof_fill_slab": [Block("acacia_slab"), Block("jungle_slab")],
    "vil_roof_block": [Block("acacia_planks"), Block("jungle_planks")],
}

_JUNGLE = {
    "foundation": [Block("mossy_cobblestone"), Block("mossy_stone_bricks")],
    "pillar": [Block("stripped_jungle_log"), Block("jungle_log")],
    "wall": [Block("jungle_planks"), Block("bamboo_planks")],
    "roof_stairs": [Block("jungle_stairs"), Block("jungle_stairs")],
    "roof_block": [Block("jungle_planks"), Block("jungle_planks")],
    "street": [Block("podzol")],
    "pirate_foundation": [Block("mossy_stone_bricks"), Block("blackstone")],
    "pirate_pillar": [Block("dark_oak_log"), Block("jungle_log")],
    "pirate_wall": [Block("jungle_planks"), Block("dark_oak_planks")],
    "pirate_roof_stairs": [
        Block("deepslate_brick_stairs"),
        Block("deepslate_brick_stairs"),
    ],
    "pirate_roof_slab": [Block("deepslate_brick_slab"), Block("deepslate_brick_slab")],
    "pirate_roof_block": [Block("deepslate_bricks"), Block("deepslate_bricks")],
    "pirate_door": [Block("bamboo_door")],
    "pirate_fence": [Block("bamboo_fence")],
    "pirate_trapdoor": [Block("bamboo_trapdoor")],
    "pirate_inner_stair": [Block("jungle_stairs")],
    "pirate_window": [Block("green_stained_glass_pane")],
    "manor_timber": [Block("bamboo_fence")],
    "manor_foundation": [Block("coal_block"), Block("obsidian")],
    "manor_pillar": [Block("gold_block"), Block("mossy_stone_bricks")],
    "manor_wall": [Block("green_terracotta"), Block("jungle_planks")],
    "manor_roof_stairs": [
        Block("deepslate_tile_stairs"),
        Block("deepslate_tile_stairs"),
    ],
    "manor_roof_slab": [Block("deepslate_tile_slab"), Block("deepslate_tile_slab")],
    "manor_roof_block": [Block("deepslate_tiles"), Block("deepslate_tiles")],
    "manor_floor": [Block("jungle_planks"), Block("dark_oak_planks")],
    # --- VILLAGER HOUSE (JAPANESE) ---
    "vil_base_stone": [Block("mossy_cobblestone"), Block("cobblestone")],
    "vil_base_stone_alt": [Block("mossy_stone_bricks"), Block("cracked_stone_bricks")],
    "vil_porch_slab": [Block("jungle_slab"), Block("bamboo_slab")],
    "vil_pillar_wood": [Block("jungle_log"), Block("warped_stem")],
    "vil_beam_wood": [Block("stripped_jungle_log"), Block("stripped_warped_stem")],
    "vil_wall_wood": [Block("stripped_jungle_log"), Block("stripped_warped_stem")],
    "vil_shoji_block": [Block("green_terracotta"), Block("brown_mushroom_block")],
    "vil_shoji_trapdoor": [Block("bamboo_trapdoor"), Block("warped_trapdoor")],
    "vil_roof_outline_stair": [Block("dark_oak_stairs"), Block("warped_stairs")],
    "vil_roof_outline_slab": [Block("dark_oak_slab"), Block("warped_slab")],
    "vil_roof_outline_block": [Block("dark_oak_planks"), Block("warped_planks")],
    "vil_roof_fill_stair": [Block("jungle_stairs"), Block("warped_stairs")],
    "vil_roof_fill_slab": [Block("jungle_slab"), Block("warped_slab")],
    "vil_roof_block": [Block("jungle_planks"), Block("warped_planks")],
}

_MANGROVE = {
    "foundation": [Block("mud_bricks"), Block("packed_mud")],
    "pillar": [Block("stripped_mangrove_log"), Block("mangrove_log")],
    "wall": [Block("mangrove_planks"), Block("mud_bricks")],
    "roof_stairs": [Block("mangrove_stairs"), Block("mangrove_stairs")],
    "roof_block": [Block("mangrove_planks"), Block("mangrove_planks")],
    "street": [Block("packed_mud")],
    "pirate_foundation": [Block("mud_bricks"), Block("blackstone")],
    "pirate_pillar": [Block("mangrove_log"), Block("dark_oak_log")],
    "pirate_wall": [Block("mangrove_planks"), Block("dark_oak_planks")],
    "pirate_roof_stairs": [
        Block("polished_deepslate_stairs"),
        Block("polished_deepslate_stairs"),
    ],
    "pirate_roof_slab": [
        Block("polished_deepslate_slab"),
        Block("polished_deepslate_slab"),
    ],
    "pirate_roof_block": [Block("polished_deepslate"), Block("polished_deepslate")],
    "pirate_door": [Block("mangrove_door")],
    "pirate_fence": [Block("mangrove_fence")],
    "pirate_trapdoor": [Block("mangrove_trapdoor")],
    "pirate_inner_stair": [Block("mangrove_stairs")],
    "pirate_window": [Block("cyan_stained_glass_pane")],
    "manor_timber": [Block("mangrove_fence")],
    "manor_foundation": [Block("coal_block"), Block("polished_blackstone")],
    "manor_pillar": [Block("gold_block"), Block("emerald_block")],
    "manor_wall": [Block("mud_bricks"), Block("green_terracotta")],
    "manor_roof_stairs": [
        Block("deepslate_tile_stairs"),
        Block("deepslate_tile_stairs"),
    ],
    "manor_roof_slab": [Block("deepslate_tile_slab"), Block("deepslate_tile_slab")],
    "manor_roof_block": [Block("deepslate_tiles"), Block("deepslate_tiles")],
    "manor_floor": [Block("mangrove_planks"), Block("dark_oak_planks")],
    # --- VILLAGER HOUSE (JAPANESE) ---
    "vil_base_stone": [Block("mud_bricks"), Block("packed_mud")],
    "vil_base_stone_alt": [Block("packed_mud"), Block("dirt")],
    "vil_porch_slab": [Block("mangrove_slab"), Block("crimson_slab")],
    "vil_pillar_wood": [Block("mangrove_log"), Block("crimson_stem")],
    "vil_beam_wood": [Block("stripped_mangrove_log"), Block("stripped_crimson_stem")],
    "vil_wall_wood": [Block("stripped_mangrove_log"), Block("stripped_crimson_stem")],
    "vil_shoji_block": [Block("red_terracotta"), Block("nether_wart_block")],
    "vil_shoji_trapdoor": [Block("mangrove_trapdoor"), Block("crimson_trapdoor")],
    "vil_roof_outline_stair": [Block("dark_oak_stairs"), Block("nether_brick_stairs")],
    "vil_roof_outline_slab": [Block("dark_oak_slab"), Block("nether_brick_slab")],
    "vil_roof_outline_block": [Block("dark_oak_planks"), Block("nether_bricks")],
    "vil_roof_fill_stair": [Block("mangrove_stairs"), Block("crimson_stairs")],
    "vil_roof_fill_slab": [Block("mangrove_slab"), Block("crimson_slab")],
    "vil_roof_block": [Block("mangrove_planks"), Block("crimson_planks")],
}

_MUSHROOM = {
    "foundation": [Block("polished_diorite"), Block("calcite")],
    "pillar": [Block("mushroom_stem"), Block("mushroom_stem")],
    "wall": [Block("red_mushroom_block"), Block("brown_mushroom_block")],
    "roof_stairs": [Block("oak_stairs"), Block("purpur_stairs")],
    "roof_block": [Block("oak_planks"), Block("purpur_block")],
    "street": [Block("mycelium")],
    "pirate_foundation": [Block("blackstone"), Block("obsidian")],
    "pirate_pillar": [Block("dark_oak_log"), Block("mushroom_stem")],
    "pirate_wall": [Block("red_mushroom_block"), Block("dark_oak_planks")],
    "pirate_roof_stairs": [
        Block("deepslate_brick_stairs"),
        Block("deepslate_brick_stairs"),
    ],
    "pirate_roof_slab": [Block("deepslate_brick_slab"), Block("deepslate_brick_slab")],
    "pirate_roof_block": [Block("deepslate_bricks"), Block("deepslate_bricks")],
    "pirate_door": [Block("dark_oak_door")],
    "pirate_fence": [Block("dark_oak_fence")],
    "pirate_trapdoor": [Block("dark_oak_trapdoor")],
    "pirate_inner_stair": [Block("dark_oak_stairs")],
    "pirate_window": [Block("purple_stained_glass_pane")],
    "manor_timber": [Block("dark_oak_fence")],
    "manor_foundation": [Block("coal_block"), Block("obsidian")],
    "manor_pillar": [Block("gold_block"), Block("purpur_pillar")],
    "manor_wall": [Block("magenta_terracotta"), Block("purpur_block")],
    "manor_roof_stairs": [
        Block("deepslate_tile_stairs"),
        Block("deepslate_tile_stairs"),
    ],
    "manor_roof_slab": [Block("deepslate_tile_slab"), Block("deepslate_tile_slab")],
    "manor_roof_block": [Block("deepslate_tiles"), Block("deepslate_tiles")],
    "manor_floor": [Block("dark_oak_planks"), Block("purpur_block")],
    # --- VILLAGER HOUSE (JAPANESE) ---
    "vil_base_stone": [Block("polished_diorite"), Block("diorite")],
    "vil_base_stone_alt": [Block("calcite"), Block("tuff")],
    "vil_porch_slab": [Block("purpur_slab"), Block("crimson_slab")],
    "vil_pillar_wood": [Block("mushroom_stem"), Block("stripped_crimson_stem")],
    "vil_beam_wood": [Block("mushroom_stem"), Block("stripped_crimson_stem")],
    "vil_wall_wood": [Block("mushroom_stem"), Block("stripped_crimson_stem")],
    "vil_shoji_block": [Block("red_mushroom_block"), Block("brown_mushroom_block")],
    "vil_shoji_trapdoor": [Block("dark_oak_trapdoor"), Block("crimson_trapdoor")],
    "vil_roof_outline_stair": [Block("dark_oak_stairs"), Block("nether_brick_stairs")],
    "vil_roof_outline_slab": [Block("dark_oak_slab"), Block("nether_brick_slab")],
    "vil_roof_outline_block": [Block("dark_oak_planks"), Block("nether_bricks")],
    "vil_roof_fill_stair": [Block("purpur_stairs"), Block("crimson_stairs")],
    "vil_roof_fill_slab": [Block("purpur_slab"), Block("crimson_slab")],
    "vil_roof_block": [Block("purpur_block"), Block("crimson_planks")],
}

_ICE = {
    "foundation": [Block("snow_block"), Block("packed_ice")],
    "pillar": [Block("packed_ice"), Block("blue_ice")],
    "wall": [Block("snow_block"), Block("light_blue_concrete_powder")],
    "roof_stairs": [Block("quartz_stairs"), Block("quartz_stairs")],
    "roof_block": [Block("quartz_block"), Block("quartz_block")],
    "street": [Block("packed_ice")],
    "pirate_foundation": [Block("basalt"), Block("packed_ice")],
    "pirate_pillar": [Block("dark_oak_log"), Block("blue_ice")],
    "pirate_wall": [Block("packed_ice"), Block("dark_oak_planks")],
    "pirate_roof_stairs": [
        Block("deepslate_brick_stairs"),
        Block("deepslate_brick_stairs"),
    ],
    "pirate_roof_slab": [Block("deepslate_brick_slab"), Block("deepslate_brick_slab")],
    "pirate_roof_block": [Block("deepslate_bricks"), Block("deepslate_bricks")],
    "pirate_door": [Block("spruce_door")],
    "pirate_fence": [Block("spruce_fence")],
    "pirate_trapdoor": [Block("iron_trapdoor")],
    "pirate_inner_stair": [Block("spruce_stairs")],
    "pirate_window": [Block("light_blue_stained_glass_pane")],
    "manor_timber": [Block("spruce_fence")],
    "manor_foundation": [Block("coal_block"), Block("blue_ice")],
    "manor_pillar": [Block("gold_block"), Block("packed_ice")],
    "manor_wall": [Block("cyan_terracotta"), Block("blue_ice")],
    "manor_roof_stairs": [
        Block("deepslate_tile_stairs"),
        Block("deepslate_tile_stairs"),
    ],
    "manor_roof_slab": [Block("deepslate_tile_slab"), Block("deepslate_tile_slab")],
    "manor_roof_block": [Block("deepslate_tiles"), Block("deepslate_tiles")],
    "manor_floor": [Block("spruce_planks"), Block("dark_oak_planks")],
    # --- VILLAGER HOUSE (JAPANESE) ---
    "vil_base_stone": [Block("packed_ice"), Block("blue_ice")],
    "vil_base_stone_alt": [Block("snow_block"), Block("ice")],
    "vil_porch_slab": [Block("quartz_slab"), Block("stone_slab")],
    "vil_pillar_wood": [Block("stripped_spruce_log"), Block("stripped_dark_oak_log")],
    "vil_beam_wood": [Block("stripped_spruce_log"), Block("stripped_dark_oak_log")],
    "vil_wall_wood": [Block("stripped_spruce_log"), Block("stripped_dark_oak_log")],
    "vil_shoji_block": [Block("light_blue_wool"), Block("cyan_wool")],
    "vil_shoji_trapdoor": [Block("iron_trapdoor"), Block("spruce_trapdoor")],
    "vil_roof_outline_stair": [Block("quartz_stairs"), Block("stone_brick_stairs")],
    "vil_roof_outline_slab": [Block("quartz_slab"), Block("stone_brick_slab")],
    "vil_roof_outline_block": [Block("quartz_block"), Block("stone_bricks")],
    "vil_roof_fill_stair": [Block("spruce_stairs"), Block("dark_oak_stairs")],
    "vil_roof_fill_slab": [Block("spruce_slab"), Block("dark_oak_slab")],
    "vil_roof_block": [Block("spruce_planks"), Block("dark_oak_planks")],
}

_MOUNTAIN = {
    "foundation": [Block("cobbled_deepslate"), Block("tuff")],
    "pillar": [Block("stone"), Block("andesite")],
    "wall": [Block("calcite"), Block("diorite")],
    "roof_stairs": [Block("stone_brick_stairs"), Block("stone_brick_stairs")],
    "roof_block": [Block("stone_bricks"), Block("stone_bricks")],
    "street": [Block("gravel")],
    "pirate_foundation": [Block("tuff"), Block("cobbled_deepslate")],
    "pirate_pillar": [Block("dark_oak_log"), Block("andesite")],
    "pirate_wall": [Block("calcite"), Block("dark_oak_planks")],
    "pirate_roof_stairs": [
        Block("polished_deepslate_stairs"),
        Block("polished_deepslate_stairs"),
    ],
    "pirate_roof_slab": [
        Block("polished_deepslate_slab"),
        Block("polished_deepslate_slab"),
    ],
    "pirate_roof_block": [Block("polished_deepslate"), Block("polished_deepslate")],
    "pirate_door": [Block("spruce_door")],
    "pirate_fence": [Block("spruce_fence")],
    "pirate_trapdoor": [Block("spruce_trapdoor")],
    "pirate_inner_stair": [Block("cobblestone_stairs")],
    "pirate_window": [Block("gray_stained_glass_pane")],
    "manor_timber": [Block("spruce_fence")],
    "manor_foundation": [Block("coal_block"), Block("polished_deepslate")],
    "manor_pillar": [Block("gold_block"), Block("chiseled_stone_bricks")],
    "manor_wall": [Block("calcite"), Block("tuff_bricks")],
    "manor_roof_stairs": [
        Block("deepslate_tile_stairs"),
        Block("deepslate_tile_stairs"),
    ],
    "manor_roof_slab": [Block("deepslate_tile_slab"), Block("deepslate_tile_slab")],
    "manor_roof_block": [Block("deepslate_tiles"), Block("deepslate_tiles")],
    "manor_floor": [Block("spruce_planks"), Block("dark_oak_planks")],
    # --- VILLAGER HOUSE (JAPANESE) ---
    "vil_base_stone": [Block("tuff"), Block("cobbled_deepslate")],
    "vil_base_stone_alt": [Block("calcite"), Block("andesite")],
    "vil_porch_slab": [Block("spruce_slab"), Block("dark_oak_slab")],
    "vil_pillar_wood": [Block("spruce_log"), Block("dark_oak_log")],
    "vil_beam_wood": [Block("stripped_spruce_log"), Block("stripped_dark_oak_log")],
    "vil_wall_wood": [Block("stripped_spruce_log"), Block("stripped_dark_oak_log")],
    "vil_shoji_block": [Block("light_gray_wool"), Block("gray_wool")],
    "vil_shoji_trapdoor": [Block("spruce_trapdoor"), Block("dark_oak_trapdoor")],
    "vil_roof_outline_stair": [
        Block("stone_brick_stairs"),
        Block("deepslate_brick_stairs"),
    ],
    "vil_roof_outline_slab": [Block("stone_brick_slab"), Block("deepslate_brick_slab")],
    "vil_roof_outline_block": [Block("stone_bricks"), Block("deepslate_bricks")],
    "vil_roof_fill_stair": [Block("spruce_stairs"), Block("dark_oak_stairs")],
    "vil_roof_fill_slab": [Block("spruce_slab"), Block("dark_oak_slab")],
    "vil_roof_block": [Block("spruce_planks"), Block("dark_oak_planks")],
}

_WARM_OCEAN = {
    "foundation": [Block("smooth_sandstone"), Block("sandstone")],
    "pillar": [Block("stripped_jungle_log"), Block("jungle_log")],
    "wall": [Block("sandstone"), Block("cyan_terracotta")],
    "roof_stairs": [Block("sandstone_stairs"), Block("sandstone_stairs")],
    "roof_block": [Block("sandstone"), Block("sandstone")],
    "street": [Block("sandstone")],
    "pirate_foundation": [Block("dark_prismarine"), Block("blackstone")],
    "pirate_pillar": [Block("dark_oak_log"), Block("stripped_jungle_log")],
    "pirate_wall": [Block("prismarine_bricks"), Block("dark_oak_planks")],
    "pirate_roof_stairs": [
        Block("deepslate_brick_stairs"),
        Block("deepslate_brick_stairs"),
    ],
    "pirate_roof_slab": [Block("deepslate_brick_slab"), Block("deepslate_brick_slab")],
    "pirate_roof_block": [Block("deepslate_bricks"), Block("deepslate_bricks")],
    "pirate_door": [Block("jungle_door")],
    "pirate_fence": [Block("jungle_fence")],
    "pirate_trapdoor": [Block("jungle_trapdoor")],
    "pirate_inner_stair": [Block("jungle_stairs")],
    "pirate_window": [Block("cyan_stained_glass_pane")],
    "manor_timber": [Block("jungle_fence")],
    "manor_foundation": [Block("coal_block"), Block("dark_prismarine")],
    "manor_pillar": [Block("gold_block"), Block("prismarine")],
    "manor_wall": [Block("cyan_terracotta"), Block("prismarine_bricks")],
    "manor_roof_stairs": [
        Block("deepslate_tile_stairs"),
        Block("deepslate_tile_stairs"),
    ],
    "manor_roof_slab": [Block("deepslate_tile_slab"), Block("deepslate_tile_slab")],
    "manor_roof_block": [Block("deepslate_tiles"), Block("deepslate_tiles")],
    "manor_floor": [Block("jungle_planks"), Block("dark_oak_planks")],
    # --- VILLAGER HOUSE (JAPANESE) ---
    "vil_base_stone": [Block("smooth_sandstone"), Block("sandstone")],
    "vil_base_stone_alt": [Block("cut_sandstone"), Block("chiseled_sandstone")],
    "vil_porch_slab": [Block("jungle_slab"), Block("acacia_slab")],
    "vil_pillar_wood": [Block("jungle_log"), Block("stripped_acacia_log")],
    "vil_beam_wood": [Block("stripped_jungle_log"), Block("stripped_acacia_log")],
    "vil_wall_wood": [Block("stripped_jungle_log"), Block("stripped_acacia_log")],
    "vil_shoji_block": [Block("cyan_terracotta"), Block("light_blue_terracotta")],
    "vil_shoji_trapdoor": [Block("jungle_trapdoor"), Block("acacia_trapdoor")],
    "vil_roof_outline_stair": [
        Block("sandstone_stairs"),
        Block("red_sandstone_stairs"),
    ],
    "vil_roof_outline_slab": [Block("sandstone_slab"), Block("red_sandstone_slab")],
    "vil_roof_outline_block": [
        Block("smooth_sandstone"),
        Block("smooth_red_sandstone"),
    ],
    "vil_roof_fill_stair": [Block("jungle_stairs"), Block("acacia_stairs")],
    "vil_roof_fill_slab": [Block("jungle_slab"), Block("acacia_slab")],
    "vil_roof_block": [Block("jungle_planks"), Block("acacia_planks")],
}

_OCEAN = {
    "foundation": [Block("prismarine_bricks"), Block("dark_prismarine")],
    "pillar": [Block("stripped_oak_log"), Block("stripped_oak_log")],
    "wall": [Block("mossy_stone_bricks"), Block("stone_bricks")],
    "roof_stairs": [Block("prismarine_stairs"), Block("prismarine_stairs")],
    "roof_block": [Block("prismarine_slab"), Block("prismarine_slab")],
    "street": [Block("stripped_oak_wood", {"axis": "y"})],
    "pirate_foundation": [Block("dark_prismarine"), Block("blackstone")],
    "pirate_pillar": [Block("dark_oak_log"), Block("dark_oak_log")],
    "pirate_wall": [Block("prismarine_bricks"), Block("dark_oak_planks")],
    "pirate_roof_stairs": [
        Block("deepslate_brick_stairs"),
        Block("deepslate_brick_stairs"),
    ],
    "pirate_roof_slab": [Block("deepslate_brick_slab"), Block("deepslate_brick_slab")],
    "pirate_roof_block": [Block("deepslate_bricks"), Block("deepslate_bricks")],
    "pirate_door": [Block("dark_oak_door")],
    "pirate_fence": [Block("dark_oak_fence")],
    "pirate_trapdoor": [Block("dark_oak_trapdoor")],
    "pirate_inner_stair": [Block("dark_oak_stairs")],
    "pirate_window": [Block("blue_stained_glass_pane")],
    "manor_timber": [Block("dark_oak_fence")],
    "manor_foundation": [Block("coal_block"), Block("dark_prismarine")],
    "manor_pillar": [Block("gold_block"), Block("prismarine")],
    "manor_wall": [Block("cyan_terracotta"), Block("prismarine_bricks")],
    "manor_roof_stairs": [
        Block("deepslate_tile_stairs"),
        Block("deepslate_tile_stairs"),
    ],
    "manor_roof_slab": [Block("deepslate_tile_slab"), Block("deepslate_tile_slab")],
    "manor_roof_block": [Block("deepslate_tiles"), Block("deepslate_tiles")],
    "manor_floor": [Block("dark_oak_planks"), Block("dark_oak_planks")],
    # --- VILLAGER HOUSE (JAPANESE) ---
    "vil_base_stone": [Block("prismarine_bricks"), Block("dark_prismarine")],
    "vil_base_stone_alt": [Block("prismarine"), Block("mossy_stone_bricks")],
    "vil_porch_slab": [Block("dark_oak_slab"), Block("spruce_slab")],
    "vil_pillar_wood": [Block("stripped_dark_oak_log"), Block("stripped_spruce_log")],
    "vil_beam_wood": [Block("stripped_dark_oak_log"), Block("stripped_spruce_log")],
    "vil_wall_wood": [Block("stripped_dark_oak_log"), Block("stripped_spruce_log")],
    "vil_shoji_block": [Block("cyan_wool"), Block("blue_wool")],
    "vil_shoji_trapdoor": [Block("dark_oak_trapdoor"), Block("spruce_trapdoor")],
    "vil_roof_outline_stair": [
        Block("prismarine_stairs"),
        Block("prismarine_brick_stairs"),
    ],
    "vil_roof_outline_slab": [Block("prismarine_slab"), Block("prismarine_brick_slab")],
    "vil_roof_outline_block": [Block("prismarine"), Block("prismarine_bricks")],
    "vil_roof_fill_stair": [Block("dark_oak_stairs"), Block("spruce_stairs")],
    "vil_roof_fill_slab": [Block("dark_oak_slab"), Block("spruce_slab")],
    "vil_roof_block": [Block("dark_oak_planks"), Block("spruce_planks")],
}

_DESERT = {
    "foundation": [Block("smooth_sandstone"), Block("sandstone")],
    "pillar": [Block("cut_sandstone"), Block("chiseled_sandstone")],
    "wall": [Block("sandstone"), Block("smooth_sandstone")],
    "roof_stairs": [Block("sandstone_stairs"), Block("sandstone_stairs")],
    "roof_block": [Block("cut_sandstone"), Block("cut_sandstone")],
    "street": [Block("smooth_sandstone")],
    "pirate_foundation": [Block("blackstone"), Block("cobbled_deepslate")],
    "pirate_pillar": [Block("dark_oak_log"), Block("stripped_dark_oak_log")],
    "pirate_wall": [Block("red_sandstone"), Block("dark_oak_planks")],
    "pirate_roof_stairs": [
        Block("deepslate_brick_stairs"),
        Block("deepslate_brick_stairs"),
    ],
    "pirate_roof_slab": [Block("deepslate_brick_slab"), Block("deepslate_brick_slab")],
    "pirate_roof_block": [Block("deepslate_bricks"), Block("deepslate_bricks")],
    "pirate_door": [Block("jungle_door")],
    "pirate_fence": [Block("jungle_fence")],
    "pirate_trapdoor": [Block("jungle_trapdoor")],
    "pirate_inner_stair": [Block("sandstone_stairs")],
    "pirate_window": [Block("yellow_stained_glass_pane")],
    "manor_timber": [Block("jungle_fence")],
    "manor_foundation": [Block("coal_block"), Block("polished_blackstone")],
    "manor_pillar": [Block("gold_block"), Block("cut_red_sandstone")],
    "manor_wall": [Block("smooth_red_sandstone"), Block("terracotta")],
    "manor_roof_stairs": [
        Block("deepslate_tile_stairs"),
        Block("deepslate_tile_stairs"),
    ],
    "manor_roof_slab": [Block("deepslate_tile_slab"), Block("deepslate_tile_slab")],
    "manor_roof_block": [Block("deepslate_tiles"), Block("deepslate_tiles")],
    "manor_floor": [Block("dark_oak_planks"), Block("jungle_planks")],
    # --- VILLAGER HOUSE (JAPANESE) ---
    "vil_base_stone": [Block("smooth_sandstone"), Block("cut_sandstone")],
    "vil_base_stone_alt": [Block("sandstone"), Block("chiseled_sandstone")],
    "vil_porch_slab": [Block("birch_slab"), Block("jungle_slab")],
    "vil_pillar_wood": [Block("stripped_birch_log"), Block("stripped_jungle_log")],
    "vil_beam_wood": [Block("stripped_birch_log"), Block("stripped_jungle_log")],
    "vil_wall_wood": [Block("stripped_birch_log"), Block("stripped_jungle_log")],
    "vil_shoji_block": [Block("white_terracotta"), Block("yellow_terracotta")],
    "vil_shoji_trapdoor": [Block("birch_trapdoor"), Block("jungle_trapdoor")],
    "vil_roof_outline_stair": [
        Block("sandstone_stairs"),
        Block("red_sandstone_stairs"),
    ],
    "vil_roof_outline_slab": [Block("sandstone_slab"), Block("red_sandstone_slab")],
    "vil_roof_outline_block": [
        Block("smooth_sandstone"),
        Block("smooth_red_sandstone"),
    ],
    "vil_roof_fill_stair": [Block("birch_stairs"), Block("jungle_stairs")],
    "vil_roof_fill_slab": [Block("birch_slab"), Block("jungle_slab")],
    "vil_roof_block": [Block("birch_planks"), Block("jungle_planks")],
}

_BADLANDS = {
    "foundation": [Block("red_sandstone"), Block("chiseled_red_sandstone")],
    "pillar": [Block("terracotta"), Block("brown_terracotta")],
    "wall": [Block("orange_terracotta"), Block("yellow_terracotta")],
    "roof_stairs": [Block("red_sandstone_stairs"), Block("red_sandstone_stairs")],
    "roof_block": [Block("smooth_red_sandstone"), Block("smooth_red_sandstone")],
    "street": [Block("smooth_red_sandstone")],
    "pirate_foundation": [Block("blackstone"), Block("cobbled_deepslate")],
    "pirate_pillar": [Block("dark_oak_log"), Block("stripped_dark_oak_log")],
    "pirate_wall": [Block("terracotta"), Block("red_sandstone")],
    "pirate_roof_stairs": [
        Block("deepslate_brick_stairs"),
        Block("deepslate_brick_stairs"),
    ],
    "pirate_roof_slab": [Block("deepslate_brick_slab"), Block("deepslate_brick_slab")],
    "pirate_roof_block": [Block("deepslate_bricks"), Block("deepslate_bricks")],
    "pirate_door": [Block("acacia_door")],
    "pirate_fence": [Block("acacia_fence")],
    "pirate_trapdoor": [Block("acacia_trapdoor")],
    "pirate_inner_stair": [Block("red_sandstone_stairs")],
    "pirate_window": [Block("orange_stained_glass_pane")],
    "manor_timber": [Block("acacia_fence")],
    "manor_foundation": [Block("coal_block"), Block("polished_blackstone")],
    "manor_pillar": [Block("gold_block"), Block("red_terracotta")],
    "manor_wall": [Block("red_terracotta"), Block("yellow_terracotta")],
    "manor_roof_stairs": [
        Block("deepslate_tile_stairs"),
        Block("deepslate_tile_stairs"),
    ],
    "manor_roof_slab": [Block("deepslate_tile_slab"), Block("deepslate_tile_slab")],
    "manor_roof_block": [Block("deepslate_tiles"), Block("deepslate_tiles")],
    "manor_floor": [Block("dark_oak_planks"), Block("jungle_planks")],
    # --- VILLAGER HOUSE (JAPANESE) ---
    "vil_base_stone": [Block("red_sandstone"), Block("cut_red_sandstone")],
    "vil_base_stone_alt": [Block("terracotta"), Block("brown_terracotta")],
    "vil_porch_slab": [Block("acacia_slab"), Block("dark_oak_slab")],
    "vil_pillar_wood": [Block("stripped_acacia_log"), Block("stripped_dark_oak_log")],
    "vil_beam_wood": [Block("stripped_acacia_log"), Block("stripped_dark_oak_log")],
    "vil_wall_wood": [Block("stripped_acacia_log"), Block("stripped_dark_oak_log")],
    "vil_shoji_block": [Block("orange_terracotta"), Block("red_terracotta")],
    "vil_shoji_trapdoor": [Block("acacia_trapdoor"), Block("dark_oak_trapdoor")],
    "vil_roof_outline_stair": [
        Block("red_sandstone_stairs"),
        Block("sandstone_stairs"),
    ],
    "vil_roof_outline_slab": [Block("red_sandstone_slab"), Block("sandstone_slab")],
    "vil_roof_outline_block": [
        Block("smooth_red_sandstone"),
        Block("smooth_sandstone"),
    ],
    "vil_roof_fill_stair": [Block("acacia_stairs"), Block("dark_oak_stairs")],
    "vil_roof_fill_slab": [Block("acacia_slab"), Block("dark_oak_slab")],
    "vil_roof_block": [Block("acacia_planks"), Block("dark_oak_planks")],
}

_BIRCH = {
    "foundation": [Block("stone_bricks"), Block("cracked_stone_bricks")],
    "pillar": [Block("stripped_birch_log"), Block("stripped_birch_log")],
    "wall": [Block("white_terracotta"), Block("bone_block")],
    "roof_stairs": [Block("birch_stairs"), Block("birch_stairs")],
    "roof_block": [Block("birch_planks"), Block("birch_planks")],
    "street": [Block("dirt_path")],
    "pirate_foundation": [Block("cobbled_deepslate"), Block("polished_deepslate")],
    "pirate_pillar": [Block("dark_oak_log"), Block("dark_oak_log")],
    "pirate_wall": [Block("stripped_spruce_log"), Block("dark_oak_planks")],
    "pirate_roof_stairs": [
        Block("polished_deepslate_stairs"),
        Block("polished_deepslate_stairs"),
    ],
    "pirate_roof_slab": [
        Block("polished_deepslate_slab"),
        Block("polished_deepslate_slab"),
    ],
    "pirate_roof_block": [Block("polished_deepslate"), Block("polished_deepslate")],
    "pirate_door": [Block("birch_door")],
    "pirate_fence": [Block("birch_fence")],
    "pirate_trapdoor": [Block("birch_trapdoor")],
    "pirate_inner_stair": [Block("birch_stairs")],
    "pirate_window": [Block("white_stained_glass_pane")],
    "manor_timber": [Block("birch_fence")],
    "manor_foundation": [Block("coal_block"), Block("polished_blackstone")],
    "manor_pillar": [Block("gold_block"), Block("chiseled_stone_bricks")],
    "manor_wall": [Block("calcite"), Block("polished_diorite")],
    "manor_roof_stairs": [
        Block("deepslate_tile_stairs"),
        Block("deepslate_tile_stairs"),
    ],
    "manor_roof_slab": [Block("deepslate_tile_slab"), Block("deepslate_tile_slab")],
    "manor_roof_block": [Block("deepslate_tiles"), Block("deepslate_tiles")],
    "manor_floor": [Block("spruce_planks"), Block("spruce_planks")],
    # --- VILLAGER HOUSE (JAPANESE) ---
    "vil_base_stone": [Block("stone_bricks"), Block("mossy_stone_bricks")],
    "vil_base_stone_alt": [Block("cobblestone"), Block("mossy_cobblestone")],
    "vil_porch_slab": [Block("birch_slab"), Block("oak_slab")],
    "vil_pillar_wood": [Block("stripped_birch_log"), Block("stripped_oak_log")],
    "vil_beam_wood": [Block("stripped_birch_log"), Block("stripped_oak_log")],
    "vil_wall_wood": [Block("stripped_birch_log"), Block("stripped_oak_log")],
    "vil_shoji_block": [Block("white_wool"), Block("light_gray_wool")],
    "vil_shoji_trapdoor": [Block("birch_trapdoor"), Block("oak_trapdoor")],
    "vil_roof_outline_stair": [Block("oak_stairs"), Block("spruce_stairs")],
    "vil_roof_outline_slab": [Block("oak_slab"), Block("spruce_slab")],
    "vil_roof_outline_block": [Block("oak_planks"), Block("spruce_planks")],
    "vil_roof_fill_stair": [Block("birch_stairs"), Block("oak_stairs")],
    "vil_roof_fill_slab": [Block("birch_slab"), Block("oak_slab")],
    "vil_roof_block": [Block("birch_planks"), Block("oak_planks")],
}

_DARK_FOREST = {
    "foundation": [Block("cobblestone"), Block("mossy_cobblestone")],
    "pillar": [Block("stripped_dark_oak_log"), Block("stripped_dark_oak_log")],
    "wall": [Block("dark_oak_planks"), Block("spruce_planks")],
    "roof_stairs": [Block("dark_oak_stairs"), Block("dark_oak_stairs")],
    "roof_block": [Block("dark_oak_planks"), Block("dark_oak_planks")],
    "street": [Block("dirt_path")],
    "pirate_foundation": [Block("obsidian"), Block("blackstone")],
    "pirate_pillar": [Block("dark_oak_log"), Block("dark_oak_log")],
    "pirate_wall": [Block("dark_oak_planks"), Block("polished_blackstone_bricks")],
    "pirate_roof_stairs": [
        Block("deepslate_brick_stairs"),
        Block("deepslate_brick_stairs"),
    ],
    "pirate_roof_slab": [Block("deepslate_brick_slab"), Block("deepslate_brick_slab")],
    "pirate_roof_block": [Block("deepslate_bricks"), Block("deepslate_bricks")],
    "pirate_door": [Block("dark_oak_door")],
    "pirate_fence": [Block("dark_oak_fence")],
    "pirate_trapdoor": [Block("dark_oak_trapdoor")],
    "pirate_inner_stair": [Block("dark_oak_stairs")],
    "pirate_window": [Block("brown_stained_glass_pane")],
    "manor_timber": [Block("dark_oak_fence")],
    "manor_foundation": [Block("coal_block"), Block("obsidian")],
    "manor_pillar": [Block("gold_block"), Block("gilded_blackstone")],
    "manor_wall": [Block("obsidian"), Block("cracked_polished_blackstone_bricks")],
    "manor_roof_stairs": [
        Block("deepslate_tile_stairs"),
        Block("deepslate_tile_stairs"),
    ],
    "manor_roof_slab": [Block("deepslate_tile_slab"), Block("deepslate_tile_slab")],
    "manor_roof_block": [Block("deepslate_tiles"), Block("deepslate_tiles")],
    "manor_floor": [Block("spruce_planks"), Block("spruce_planks")],
    # --- VILLAGER HOUSE (JAPANESE) ---
    "vil_base_stone": [Block("cobblestone"), Block("mossy_cobblestone")],
    "vil_base_stone_alt": [Block("obsidian"), Block("crying_obsidian")],
    "vil_porch_slab": [Block("dark_oak_slab"), Block("warped_slab")],
    "vil_pillar_wood": [Block("stripped_dark_oak_log"), Block("stripped_warped_stem")],
    "vil_beam_wood": [Block("stripped_dark_oak_log"), Block("stripped_warped_stem")],
    "vil_wall_wood": [Block("stripped_dark_oak_log"), Block("stripped_warped_stem")],
    "vil_shoji_block": [Block("brown_wool"), Block("black_wool")],
    "vil_shoji_trapdoor": [Block("dark_oak_trapdoor"), Block("warped_trapdoor")],
    "vil_roof_outline_stair": [Block("spruce_stairs"), Block("warped_stairs")],
    "vil_roof_outline_slab": [Block("spruce_slab"), Block("warped_slab")],
    "vil_roof_outline_block": [Block("spruce_planks"), Block("warped_planks")],
    "vil_roof_fill_stair": [Block("dark_oak_stairs"), Block("warped_stairs")],
    "vil_roof_fill_slab": [Block("dark_oak_slab"), Block("warped_slab")],
    "vil_roof_block": [Block("dark_oak_planks"), Block("warped_planks")],
}

_SPRUCE = {
    "foundation": [Block("cobblestone"), Block("mossy_cobblestone")],
    "pillar": [Block("stripped_spruce_log"), Block("stripped_spruce_log")],
    "wall": [Block("spruce_planks"), Block("mud_bricks")],
    "roof_stairs": [Block("spruce_stairs"), Block("spruce_stairs")],
    "roof_block": [Block("spruce_planks"), Block("spruce_planks")],
    "street": [Block("dirt_path")],
    "pirate_foundation": [Block("cobbled_deepslate"), Block("cobbled_deepslate")],
    "pirate_pillar": [Block("dark_oak_log"), Block("dark_oak_log")],
    "pirate_wall": [Block("spruce_planks"), Block("tuff")],
    "pirate_roof_stairs": [
        Block("polished_deepslate_stairs"),
        Block("polished_deepslate_stairs"),
    ],
    "pirate_roof_slab": [
        Block("polished_deepslate_slab"),
        Block("polished_deepslate_slab"),
    ],
    "pirate_roof_block": [Block("polished_deepslate"), Block("polished_deepslate")],
    "pirate_door": [Block("spruce_door")],
    "pirate_fence": [Block("spruce_fence")],
    "pirate_trapdoor": [Block("spruce_trapdoor")],
    "pirate_inner_stair": [Block("spruce_stairs")],
    "pirate_window": [Block("gray_stained_glass_pane")],
    "manor_timber": [Block("spruce_fence")],
    "manor_foundation": [Block("coal_block"), Block("polished_blackstone")],
    "manor_pillar": [Block("gold_block"), Block("tuff_bricks")],
    "manor_wall": [Block("tuff_bricks"), Block("calcite")],
    "manor_roof_stairs": [
        Block("deepslate_tile_stairs"),
        Block("deepslate_tile_stairs"),
    ],
    "manor_roof_slab": [Block("deepslate_tile_slab"), Block("deepslate_tile_slab")],
    "manor_roof_block": [Block("deepslate_tiles"), Block("deepslate_tiles")],
    "manor_floor": [Block("dark_oak_planks"), Block("dark_oak_planks")],
    # --- VILLAGER HOUSE (JAPANESE) ---
    "vil_base_stone": [Block("cobblestone"), Block("mossy_cobblestone")],
    "vil_base_stone_alt": [Block("stone_bricks"), Block("cracked_stone_bricks")],
    "vil_porch_slab": [Block("spruce_slab"), Block("dark_oak_slab")],
    "vil_pillar_wood": [Block("stripped_spruce_log"), Block("stripped_dark_oak_log")],
    "vil_beam_wood": [Block("stripped_spruce_log"), Block("stripped_dark_oak_log")],
    "vil_wall_wood": [Block("stripped_spruce_log"), Block("stripped_dark_oak_log")],
    "vil_shoji_block": [Block("light_gray_wool"), Block("gray_wool")],
    "vil_shoji_trapdoor": [Block("spruce_trapdoor"), Block("dark_oak_trapdoor")],
    "vil_roof_outline_stair": [Block("dark_oak_stairs"), Block("mangrove_stairs")],
    "vil_roof_outline_slab": [Block("dark_oak_slab"), Block("mangrove_slab")],
    "vil_roof_outline_block": [Block("dark_oak_planks"), Block("mangrove_planks")],
    "vil_roof_fill_stair": [Block("spruce_stairs"), Block("dark_oak_stairs")],
    "vil_roof_fill_slab": [Block("spruce_slab"), Block("dark_oak_slab")],
    "vil_roof_block": [Block("spruce_planks"), Block("dark_oak_planks")],
}

_SNOWY = {
    "foundation": [Block("stone_bricks"), Block("cobblestone")],
    "pillar": [Block("stripped_spruce_log"), Block("stripped_spruce_log")],
    "wall": [Block("snow_block"), Block("white_wool")],
    "roof_stairs": [Block("spruce_stairs"), Block("spruce_stairs")],
    "roof_block": [Block("spruce_planks"), Block("spruce_planks")],
    "street": [Block("stone_bricks")],
    "pirate_foundation": [Block("basalt"), Block("polished_basalt")],
    "pirate_pillar": [Block("dark_oak_log"), Block("dark_oak_log")],
    "pirate_wall": [Block("spruce_planks"), Block("snow_block")],
    "pirate_roof_stairs": [
        Block("deepslate_brick_stairs"),
        Block("deepslate_brick_stairs"),
    ],
    "pirate_roof_slab": [Block("deepslate_brick_slab"), Block("deepslate_brick_slab")],
    "pirate_roof_block": [Block("deepslate_bricks"), Block("deepslate_bricks")],
    "pirate_door": [Block("spruce_door")],
    "pirate_fence": [Block("spruce_fence")],
    "pirate_trapdoor": [Block("iron_trapdoor")],
    "pirate_inner_stair": [Block("spruce_stairs")],
    "pirate_window": [Block("white_stained_glass_pane")],
    "manor_timber": [Block("spruce_fence")],
    "manor_foundation": [Block("coal_block"), Block("polished_blackstone")],
    "manor_pillar": [Block("gold_block"), Block("packed_ice")],
    "manor_wall": [Block("packed_ice"), Block("calcite")],
    "manor_roof_stairs": [
        Block("deepslate_tile_stairs"),
        Block("deepslate_tile_stairs"),
    ],
    "manor_roof_slab": [Block("deepslate_tile_slab"), Block("deepslate_tile_slab")],
    "manor_roof_block": [Block("deepslate_tiles"), Block("deepslate_tiles")],
    "manor_floor": [Block("spruce_planks"), Block("spruce_planks")],
    # --- VILLAGER HOUSE (JAPANESE) ---
    "vil_base_stone": [Block("stone_bricks"), Block("cracked_stone_bricks")],
    "vil_base_stone_alt": [Block("snow_block"), Block("powder_snow")],
    "vil_porch_slab": [Block("spruce_slab"), Block("oak_slab")],
    "vil_pillar_wood": [Block("stripped_spruce_log"), Block("stripped_oak_log")],
    "vil_beam_wood": [Block("stripped_spruce_log"), Block("stripped_oak_log")],
    "vil_wall_wood": [Block("stripped_spruce_log"), Block("stripped_oak_log")],
    "vil_shoji_block": [Block("white_wool"), Block("light_blue_wool")],
    "vil_shoji_trapdoor": [Block("spruce_trapdoor"), Block("oak_trapdoor")],
    "vil_roof_outline_stair": [
        Block("stone_brick_stairs"),
        Block("cobblestone_stairs"),
    ],
    "vil_roof_outline_slab": [Block("stone_brick_slab"), Block("cobblestone_slab")],
    "vil_roof_outline_block": [Block("stone_bricks"), Block("cobblestone")],
    "vil_roof_fill_stair": [Block("spruce_stairs"), Block("oak_stairs")],
    "vil_roof_fill_slab": [Block("spruce_slab"), Block("oak_slab")],
    "vil_roof_block": [Block("spruce_planks"), Block("oak_planks")],
}

_SWAMP = {
    "foundation": [Block("mossy_cobblestone"), Block("mud_bricks")],
    "pillar": [Block("stripped_mangrove_log"), Block("stripped_mangrove_log")],
    "wall": [Block("mud_bricks"), Block("packed_mud")],
    "roof_stairs": [Block("mangrove_stairs"), Block("mangrove_stairs")],
    "roof_block": [Block("mangrove_planks"), Block("mangrove_planks")],
    "street": [Block("dirt_path")],
    "pirate_foundation": [Block("mud_bricks"), Block("blackstone")],
    "pirate_pillar": [Block("mangrove_log"), Block("mangrove_log")],
    "pirate_wall": [Block("mangrove_planks"), Block("dark_oak_planks")],
    "pirate_roof_stairs": [
        Block("polished_deepslate_stairs"),
        Block("polished_deepslate_stairs"),
    ],
    "pirate_roof_slab": [
        Block("polished_deepslate_slab"),
        Block("polished_deepslate_slab"),
    ],
    "pirate_roof_block": [Block("polished_deepslate"), Block("polished_deepslate")],
    "pirate_door": [Block("mangrove_door")],
    "pirate_fence": [Block("mangrove_fence")],
    "pirate_trapdoor": [Block("mangrove_trapdoor")],
    "pirate_inner_stair": [Block("mangrove_stairs")],
    "pirate_window": [Block("green_stained_glass_pane")],
    "manor_timber": [Block("mangrove_fence")],
    "manor_foundation": [Block("coal_block"), Block("polished_blackstone")],
    "manor_pillar": [Block("gold_block"), Block("emerald_block")],
    "manor_wall": [Block("mud_bricks"), Block("green_terracotta")],
    "manor_roof_stairs": [
        Block("deepslate_tile_stairs"),
        Block("deepslate_tile_stairs"),
    ],
    "manor_roof_slab": [Block("deepslate_tile_slab"), Block("deepslate_tile_slab")],
    "manor_roof_block": [Block("deepslate_tiles"), Block("deepslate_tiles")],
    "manor_floor": [Block("mangrove_planks"), Block("mangrove_planks")],
    # --- VILLAGER HOUSE (JAPANESE) ---
    "vil_base_stone": [Block("mossy_cobblestone"), Block("cobblestone")],
    "vil_base_stone_alt": [Block("mud_bricks"), Block("packed_mud")],
    "vil_porch_slab": [Block("mangrove_slab"), Block("jungle_slab")],
    "vil_pillar_wood": [Block("stripped_mangrove_log"), Block("stripped_jungle_log")],
    "vil_beam_wood": [Block("stripped_mangrove_log"), Block("stripped_jungle_log")],
    "vil_wall_wood": [Block("stripped_mangrove_log"), Block("stripped_jungle_log")],
    "vil_shoji_block": [Block("green_wool"), Block("brown_wool")],
    "vil_shoji_trapdoor": [Block("mangrove_trapdoor"), Block("jungle_trapdoor")],
    "vil_roof_outline_stair": [Block("dark_oak_stairs"), Block("jungle_stairs")],
    "vil_roof_outline_slab": [Block("dark_oak_slab"), Block("jungle_slab")],
    "vil_roof_outline_block": [Block("dark_oak_planks"), Block("jungle_planks")],
    "vil_roof_fill_stair": [Block("mangrove_stairs"), Block("jungle_stairs")],
    "vil_roof_fill_slab": [Block("mangrove_slab"), Block("jungle_slab")],
    "vil_roof_block": [Block("mangrove_planks"), Block("jungle_planks")],
}

# =============================================================================
# MAPPING
# =============================================================================

BIOME_PALETTES: dict[str, dict[str, list[Block]]] = {
    # --- TEMPERATE / PLAINS ---
    "plains": _DEFAULT,
    "sunflower_plains": _DEFAULT,
    "meadow": _MEADOW,
    "cherry_grove": _CHERRY,
    "forest": _DEFAULT,
    "flower_forest": _DEFAULT,
    "birch_forest": _BIRCH,
    "old_growth_birch_forest": _BIRCH,
    "dark_forest": _DARK_FOREST,
    "swamp": _SWAMP,
    "mangrove_swamp": _MANGROVE,
    # --- COLD / TAIGA ---
    "taiga": _SPRUCE,
    "old_growth_pine_taiga": _SPRUCE,
    "old_growth_spruce_taiga": _SPRUCE,
    "windswept_forest": _SPRUCE,
    # --- SNOWY / ICE ---
    "snowy_plains": _SNOWY,
    "ice_spikes": _ICE,
    "snowy_taiga": _SNOWY,
    "snowy_beach": _SNOWY,
    "grove": _SNOWY,
    "snowy_slopes": _SNOWY,
    "jagged_peaks": _MOUNTAIN,
    "frozen_peaks": _ICE,
    "frozen_river": _ICE,
    "frozen_ocean": _ICE,
    "deep_frozen_ocean": _ICE,
    # --- MOUNTAINS / HILLS ---
    "windswept_hills": _MOUNTAIN,
    "windswept_gravelly_hills": _MOUNTAIN,
    "stony_peaks": _MOUNTAIN,
    # --- WARM / HOT ---
    "desert": _DESERT,
    "beach": _DESERT,
    "badlands": _BADLANDS,
    "eroded_badlands": _BADLANDS,
    "wooded_badlands": _BADLANDS,
    "savanna": _SAVANNA,
    "savanna_plateau": _SAVANNA,
    "windswept_savanna": _SAVANNA,
    "jungle": _JUNGLE,
    "sparse_jungle": _JUNGLE,
    "bamboo_jungle": _JUNGLE,
    "stony_shore": _MOUNTAIN,
    # --- OCEANS / RIVERS ---
    "river": _OCEAN,
    "ocean": _OCEAN,
    "deep_ocean": _OCEAN,
    "warm_ocean": _WARM_OCEAN,
    "lukewarm_ocean": _WARM_OCEAN,
    "deep_lukewarm_ocean": _WARM_OCEAN,
    "cold_ocean": _OCEAN,
    "deep_cold_ocean": _OCEAN,
    # --- CAVES ---
    "dripstone_caves": _MOUNTAIN,
    "lush_caves": _JUNGLE,
    "deep_dark": _MOUNTAIN,
    # --- OTHER OVERWORLD ---
    "mushroom_fields": _MUSHROOM,
    # --- THE NETHER ---
    "nether_wastes": _BADLANDS,
    "soul_sand_valley": _BADLANDS,
    "crimson_forest": _BADLANDS,
    "warped_forest": _DARK_FOREST,
    "basalt_deltas": _BADLANDS,
    # --- THE END ---
    "the_end": _DEFAULT,
    "small_end_islands": _DEFAULT,
    "end_midlands": _DEFAULT,
    "end_highlands": _DEFAULT,
    "end_barrens": _DEFAULT,
    # --- FALLBACK ---
    "the_void": _DEFAULT,
}

for biome_name, palette in BIOME_PALETTES.items():
    if "pirate_foundation" in palette:
        
        palette["manor_foundation"] = [palette["pirate_foundation"][0], palette["pirate_foundation"][0]]
        palette["manor_pillar"] = [palette["pirate_pillar"][0], palette["pirate_pillar"][0]]
        palette["manor_wall"] = [palette["pirate_wall"][0], palette["pirate_wall"][0]]
        
        
        palette["manor_roof_stairs"] = [palette["pirate_roof_stairs"][0], palette["pirate_roof_stairs"][0]]
        palette["manor_roof_slab"] = [palette["pirate_roof_slab"][0], palette["pirate_roof_slab"][0]]
        palette["manor_roof_block"] = [palette["pirate_roof_block"][0], palette["pirate_roof_block"][0]]
        
    if "manor_floor" in palette:
        palette["manor_floor"] = [palette["manor_floor"][0], palette["manor_floor"][0]]
    if "manor_timber" in palette:
        palette["manor_timber"] = [palette["manor_timber"][0], palette["manor_timber"][0]]

def get_palette_for_biome(biome_id: str) -> dict:
    """Returns the matching block configuration based on exact biome ID."""
    clean_id = biome_id.replace("minecraft:", "").lower()
    return BIOME_PALETTES.get(clean_id, _DEFAULT)


class CustomEditor(Editor):
    def ingame_print(self, text: str) -> None:
        """
        Prints a message in Minecraft
        :param editor: The editor that interacts with Minecraft
        :param text: The message to print
        :return: None
        """
        self.runCommand(f'tellraw @a {{ "text": "{text}", "color": "white" }}')

    def ingame_exception(self, e: Exception) -> None:
        """
        Prints an exception message in Minecraft
        :param editor: The editor that interacts with Minecraft
        :param e: The exception that occurred
        :return: None
        """
        traceback.print_exc()
        self.runCommand('tellraw @a {"text": "Error: ' + str(e) + '", "color": "red"}')

    def is_tree_block(self, block_id: str) -> bool:
        """Check if a given block ID matches tree component keywords."""
        return any(key in block_id for key in TREE_KEYWORDS)

    def destroy_tree_flood_fill(self, start_pos: tuple[int, int, int]) -> None:
        """Vaporize an entire connected tree structure using a 3D Flood Fill."""
        queue = [start_pos]
        visited = {start_pos}
        neighbors = [
            (1, 0, 0),
            (-1, 0, 0),
            (0, 1, 0),
            (0, -1, 0),
            (0, 0, 1),
            (0, 0, -1),
        ]

        while queue:
            cx, cy, cz = queue.pop(0)
            block = self.getBlock((cx, cy, cz))
            assert block.id is not None

            if not self.is_tree_block(block.id):
                continue

            # Clear the tree block components
            self.placeBlock((cx, cy, cz), Block("air"))

            for dx, dy, dz in neighbors:
                neighbor_pos = (cx + dx, cy + dy, cz + dz)
                if neighbor_pos not in visited:
                    visited.add(neighbor_pos)
                    queue.append(neighbor_pos)

    def clean_vegetation_area(
        self,
        min_x: int,
        max_x: int,
        min_z: int,
        max_z: int,
        min_y: int,
        max_y: int,
    ) -> None:
        """Scan a specific 3D volume bounding box and vaporize trees."""
        for y in range(min_y, max_y + 1):
            for x in range(min_x, max_x):
                for z in range(min_z, max_z):
                    block = self.getBlock((x, y, z))
                    assert block.id is not None
                    if self.is_tree_block(block.id):
                        self.destroy_tree_flood_fill((x, y, z))


def probability(p: float) -> bool:
    return random() < p


def do_with_probability[T](
    p: float, function: Callable[..., T]
) -> tuple[T | None, bool]:
    if probability(p):
        return function(), True
    return None, False


def mix(specs: list[tuple[Block, int]]) -> list[Block]:
    """
    Creates a list of blocks respecting the proportions given.
    """
    mixed_list = [block for block, proportion in specs for _ in range(proportion)]
    shuffle(mixed_list)

    return mixed_list


class AllowedTimeExceededError(Exception):
    """
    Raised when the allowed time is exceeded.
    """