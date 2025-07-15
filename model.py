from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional
import pandas as pd
import config_import as config_import
from config_import import ConfigKeys, Config
from enum import Enum, IntEnum

from logger import Logger, Log_Actor, Log_Granularity, Log_Action

from dataclasses import dataclass, field
from typing import List, Dict, Optional

class Gear_sets(Enum):
    COLLECTOR = "collector_set"
    DEFENDER = "defender_set"
    ROGUE = "rogue_set"
    TACTICIAN = "tactician_set"
    WARRIOR = "warrior_set"
    DEFAULT = "default_set"

class Gear_pieces(Enum):
    HELMET = "helmet"
    CHEST = "chest"
    RING_ONE = "ring_one"
    RING_TWO = "ring_two"
    BOOTS = "boots"
    WEAPON = "weapon"
    DEFAULT = "default"

class Gear_rarity(IntEnum):
    COMMON = 1
    UNCOMMON = 2
    RARE = 3
    EPIC = 4
    EPIC2 = 5
    LEGENDARY = 6

    def __str__(self):
        return self.name.lower()
    
@dataclass
class MergeRequirement:
    piece_requirement: Gear_pieces           
    rarity_requirement: Gear_rarity      
    set_requirement: Gear_sets      

@dataclass
class Gear:
    level: int
    set: Gear_sets
    piece: Gear_pieces
    max_rarity: Gear_rarity
    rarity_list: Dict[Gear_rarity, int]
    merge_rules: Dict[Gear_rarity, List[MergeRequirement]]
    level_up_rules: pd.DataFrame

    @staticmethod
    def initialize(gear_set: Gear_sets, gear_piece: Gear_pieces, gear_levels_df, gear_merge_df) -> 'Gear':
        
        level = 0
        set = gear_set
        piece = gear_piece
        max_rarity = Gear_rarity.COMMON
        rarity_list = {rarity: 0 for rarity in Gear_rarity}
        merge_rules = {}
        level_up_rules = {}
        level_up_rules = gear_levels_df

        new_gear = Gear(
            level=level,
            set=set,
            piece=piece,
            max_rarity=max_rarity,
            rarity_list=rarity_list,
            merge_rules=merge_rules,
            level_up_rules=level_up_rules
        )
        new_gear.merge_rules = new_gear.set_merge_rules(gear_merge_df)

        return new_gear

    def set_merge_rules(self, gear_merge_df: pd.DataFrame) -> Dict[Gear_rarity, List[MergeRequirement]]:
        rules: Dict[Gear_rarity, List[MergeRequirement]] = {}

        for _, row in gear_merge_df.iterrows():
            target_rarity = Gear_rarity[row[ConfigKeys.TARGET_RARITY.value].upper()]
            requirements: List[MergeRequirement] = []

            for i in range(1, 4):
                rarity_key = f"req{i}_rarity"
                piece_key = f"req{i}_piece"
                set_key = f"req{i}_set"

                if pd.isna(row[rarity_key]) or row[rarity_key] == "":
                    # Skip if rarity is NaN or empty, thus, if the is no requirement
                    continue

                piece_requirement = self.piece if row[piece_key] == "SAME_PIECE" else Gear_pieces.DEFAULT
                set_requirement = self.set if row[set_key] == "SAME_SET" else Gear_sets.DEFAULT

                requirements.append(MergeRequirement(
                    piece_requirement=piece_requirement,
                    rarity_requirement=Gear_rarity[row[rarity_key].upper()],
                    set_requirement=set_requirement
                ))

            rules[target_rarity] = requirements

        return rules

    def merge(self, target_rarity: Gear_rarity, gear_inventory: List['Gear']) -> bool:

        # Keep track of affected rarity requirements to restore if merge fails
        affected_requirements = []

        # Iterate through the merge requirements for the target rarity
        for requirement in self.merge_rules[target_rarity]:
            # Check if the required gear exists in the inventory
            matching_gear = next(
            (gear for gear in gear_inventory
             if gear.piece == requirement.piece_requirement
             and gear.rarity_list.get(requirement.rarity_requirement, 0) > 0
             and gear.set == requirement.set_requirement),
            None
            )

            # If no matching gear is found, restore the affected requirements and return False
            if not matching_gear:
                for gear, rarity in affected_requirements:
                    gear.rarity_list[rarity] += 1
                return False

            # If there is a matching, Decrease the count of the matching gear's rarity, and store it in case we need to restore
            matching_gear.rarity_list[requirement.rarity_requirement] -= 1
            affected_requirements.append((matching_gear, requirement.rarity_requirement))

        # If all requirements are met, add the gear
        # Increase the count of the target rarity in the rarity list
        self.rarity_list[target_rarity] += 1

        # Update the max_rarity based on the highest rarity with a count greater than 0
        self.max_rarity = max(
            (rarity for rarity, count in self.rarity_list.items() if count > 0),
            default=Gear_rarity.COMMON
        )

        return True

    def level_up(self, meta_progression) -> bool:
        expected_level = self.level + 1
        required_gold = self.level_up_rules.loc[expected_level, ConfigKeys.GOLD_COST.value]
        required_designs = self.level_up_rules.loc[expected_level, ConfigKeys.DESIGN_COST.value]
        required_rarity = int(pd.to_numeric(self.level_up_rules.loc[expected_level, ConfigKeys.REQUIRED_RARITY.value], errors='coerce'))

        # Check if the meta progression has enough resources to level up the gear
        # Check if the required rarity is available
        has_required_rarity = any(
            rarity >= required_rarity and count > 0 
            for rarity, count in self.rarity_list.items()
        )

        if (
            meta_progression.gold >= required_gold and
            meta_progression.designs[self.piece] >= required_designs and
            has_required_rarity
        ):
            # Deduct the required resources
            meta_progression.gold -= required_gold
            meta_progression.designs[self.piece] -= required_designs

            # Level up the gear
            self.level = expected_level

            Logger.add_log(
            Log_Actor.SIMULATION, Log_Granularity.META, Log_Action.LEVEL_UP,
            f"Gear leveled up to level {self.level}",
            {"gear": asdict(self), "meta_progression": asdict(meta_progression)}
            )

            return True

        # If requirements are not met, log the failure
        Logger.add_log(
            Log_Actor.SIMULATION, Log_Granularity.META, Log_Action.LEVEL_UP,
            f"Failed to level up gear to level {expected_level}",
            {
            "gear": asdict(self),
            "meta_progression": asdict(meta_progression),
            "required_gold": required_gold,
            "required_designs": required_designs,
            "required_rarity": required_rarity
            }
        )

        return False


@dataclass
class Player_meta_progression:
    
    gold: int
    chapter_level: int
    gear_inventory: List[Gear]
    designs: Dict[Gear_pieces, int]
    equipped_gear: Dict[Gear_pieces, Gear]
    merge_rules: Dict[Gear_rarity, List[MergeRequirement]] = field(default_factory=dict)

    @staticmethod
    def initialize(gear_levels_config: pd.DataFrame, gear_merge_config: pd.DataFrame) -> 'Player_meta_progression':

        gold = 0
        chapter_level = 1
        designs = {s: 0 for s in Gear_pieces}
        equipped_gear = {}
        merge_rules = {}
        gear_inventory = [
                Gear.initialize(gear_set, gear_piece, gear_levels_config, gear_merge_config)
                for gear_set in Gear_sets
                for gear_piece in Gear_pieces
                if gear_set != Gear_sets.DEFAULT and gear_piece != Gear_pieces.DEFAULT
            ]

        new_meta = Player_meta_progression(
            gold=gold,
            chapter_level=chapter_level,
            gear_inventory=gear_inventory,
            designs=designs,
            equipped_gear=equipped_gear,
            merge_rules=merge_rules
        )

        Logger.add_log(
            Log_Actor.SIMULATION, Log_Granularity.SIMULATION, Log_Action.INITIALIZE,
            "Meta progression initialized",
            {"meta_progression": asdict(new_meta) }
            )       

        return new_meta

    
    def simulate(self):
        
        # Obtain free chests

        # Open Chests

        # Get new gear

        # Merge Gear

        for gear in self.gear_inventory:
            for rarity in Gear_rarity:
                if rarity != Gear_rarity.COMMON:
                    success = gear.merge(rarity, self.gear_inventory)
                    if success:
                        Logger.add_log(
                            Log_Actor.SIMULATION, Log_Granularity.META, Log_Action.MERGE,
                            f"Successfully merged gear to rarity {rarity}",
                            {"gear": asdict(gear), "rarity": str(rarity)}
                        )


        # Sort gear inventory by highest level and try to level up
        sorted_gear_inventory = sorted(self.gear_inventory, key=lambda g: g.level, reverse=True)
        for gear in sorted_gear_inventory:
            gear.level_up(self)

        # Equip Gear

        # Purchase

        Logger.add_log(
            Log_Actor.SIMULATION, Log_Granularity.META, Log_Action.SIMULATE,
            "Meta progression simulation completed",
            {"gold": self.gold, "chapter_level": self.chapter_level}
        )
        return
    
    def chapter_level_up(self):
        self.chapter_level += 1
        Logger.add_log(
            Log_Actor.SIMULATION, Log_Granularity.META, Log_Action.SIMULATE,
            f"Chapter level up: new chapter level is {self.chapter_level}",
            {"chapter_level": self.chapter_level}
        )
        return

"""
@dataclass
class Player_Character:
    stat_atk: int
    stat_def: int
    stat_hp: int
    stat_max_hp: int

    def modify_atk(self, value: int):
        self.stat_atk += value

    def modify_def(self, value: int):
        self.stat_def += value

    def modify_hp(self, value: int):
        self.stat_hp = min(self.stat_hp + value, self.stat_max_hp)

    def modify_max_hp(self, value: int):
         self.stat_max_hp+=value

    def is_dead(self) -> bool:
        return self.stat_hp <= 0
    
    @staticmethod
    def initialize(stat_atk: int, stat_def:int, stat_max_hp:int) -> 'Player_Character':
        new_character =Player_Character(
            stat_atk=stat_atk,
            stat_def=stat_def,
            stat_hp = stat_max_hp,
            stat_max_hp=stat_max_hp
        )
        Logger.add_log(Log_Actor.SIMULATION, Log_Granularity.SIMULATION, Log_Action.INITIALIZE,
            "Player character initialized",
            {
                "player_character": asdict(new_character),
            }
        )

        return new_character

@dataclass
class EnemyCharacter:

    class Enemy_Types (Enum):
        SLIME = "slime"
        SKELETON = "skeleton"
        BOSS = "boss"
   
    type: Enemy_Types
    stat_atk: int
    stat_def: int
    stat_max_hp: int
    stat_hp: int

    def modify_atk(self, value: int):
        self.stat_atk += value

    def modify_def(self, value: int):
        self.stat_def += value

    def modify_hp(self, value: int):
        self.stat_hp = min(self.stat_hp + value, self.stat_max_hp)

    def is_dead(self) -> bool:
        return self.stat_hp <= 0
    
    @staticmethod
    def initialize(enemies_config, enemy_type: Enemy_Types)-> 'EnemyCharacter':

        new_enemy = EnemyCharacter(
            type = enemy_type,
            stat_atk= get_config_value_str_row(enemies_config, ConfigKeys.ENEMY_TYPE, enemy_type.value, ConfigKeys.ENEMY_ATK),
            stat_def= get_config_value_str_row(enemies_config, ConfigKeys.ENEMY_TYPE, enemy_type.value, ConfigKeys.ENEMY_DEF),
            stat_max_hp= get_config_value_str_row(enemies_config, ConfigKeys.ENEMY_TYPE, enemy_type.value, ConfigKeys.ENEMY_MAX_HP),
            stat_hp= get_config_value_str_row(enemies_config, ConfigKeys.ENEMY_TYPE, enemy_type.value, ConfigKeys.ENEMY_MAX_HP)
        )

        Logger.add_log(Log_Actor.SIMULATION, Log_Granularity.SIMULATION, Log_Action.INITIALIZE,
            "Enemy character initialized",
            {
                "enemy_character": asdict(new_enemy),
            }
        )

        return new_enemy

@dataclass
class Day:

    class EventType(Enum):
        INCREASE_ATK = "increase_atk"
        INCREASE_DEF = "increase_def"
        INCREASE_MAX_HP = "increase_max_hp"
        RESTORE_HP = "restore_hp"
        BATTLE = "battle"    
    chapter_num: int
    day_num: int
    event_type: EventType
    event_param: Any
    gold_reward: int
    event_enemy: Optional[EnemyCharacter]

    @staticmethod
    def initialize(day_config, enemies_config) -> 'Day':
        event_name = day_config[ConfigKeys.CHAPTER_DAILY_EVENT.value]
        event_type = Day.EventType(event_name)
        event_param = day_config[ConfigKeys.CHAPTER_DAILY_EVENT_PARAM.value]
        gold_reward = int(day_config[ConfigKeys.CHAPTER_DAILY_GOLD_REWARD.value]) 
        chapter_num = int(day_config[ConfigKeys.CHAPTER_NUM.value])
        day_num = int(day_config[ConfigKeys.CHAPTER_DAY_NUM.value])

        # Convert event_param to int for numeric operations
        if event_type in [Day.EventType.INCREASE_ATK, Day.EventType.INCREASE_DEF, 
                      Day.EventType.INCREASE_MAX_HP, Day.EventType.RESTORE_HP]:
            event_param = int(event_param)

        enemy_type = None
        if event_type == Day.EventType.BATTLE:
            enemy_type = EnemyCharacter.Enemy_Types(event_param) 

        new_day =  Day(
            chapter_num=chapter_num,
            day_num=day_num,
            event_type=event_type,
            event_param=event_param,
            gold_reward=gold_reward,
            event_enemy=EnemyCharacter.initialize(
                enemies_config,
                enemy_type
            ) if enemy_type else None
        )   

        Logger.add_log(Log_Actor.SIMULATION, Log_Granularity.SIMULATION, Log_Action.INITIALIZE,
            "Day initialized",
            {
                "day": asdict(new_day)  
            }
        )

        return new_day

    def simulate(self, player_character: Player_Character, meta_progression: Player_meta_progression):

        match self.event_type:
            case Day.EventType.INCREASE_ATK:
                player_character.modify_atk(self.event_param)
                meta_progression.add_gold(self.gold_reward)
            case Day.EventType.INCREASE_DEF:
                player_character.modify_def(self.event_param)
                meta_progression.add_gold(self.gold_reward)
            case Day.EventType.INCREASE_MAX_HP:
                player_character.modify_max_hp(self.event_param)
                meta_progression.add_gold(self.gold_reward)
            case Day.EventType.RESTORE_HP:
                player_character.modify_hp(self.event_param)
                meta_progression.add_gold(self.gold_reward)
            case Day.EventType.BATTLE:
                if self.event_enemy is None:
                    raise ValueError("Battle event requires an enemy character.")
                simulate_battle(player_character, self.event_enemy)
                if(not player_character.is_dead()):
                    meta_progression.add_gold(self.gold_reward)
            case _:
                raise ValueError(f"Unknown event type: {self._event_type}")
            
        Logger.add_log(
            Log_Actor.SIMULATION, Log_Granularity.DAY, Log_Action.SIMULATE,
            f"Day simulated with event {self.event_type.value} and param {self.event_param}",
            {
                "day": asdict(self),
                "player_character": asdict(player_character),
                "meta_progression": asdict(meta_progression),
            }
        )

        return
"""

@dataclass
class Chapter:

    days: List[Day]
    player_character: Player_Character
    meta_progression: Player_meta_progression

    @staticmethod
    def initialize(chapter_config_df, meta_progression: Player_meta_progression, enemies_config_df) -> 'Chapter':

        #Instantiate the player characteer
        player_character = Player_Character.initialize(
            meta_progression.stat_atk.get_value(),
            meta_progression.stat_def.get_value(),
            meta_progression.stat_max_hp.get_value()
            )    
        
        #Instantiate the day list with all the events
        days: List[Day] = []
        for index,day_config in chapter_config_df.iterrows():
            new_day = Day.initialize(day_config, enemies_config_df)
            days.append(new_day)
    
        #Create the new chapter
        chapter = Chapter(
            days,
            player_character,
            meta_progression)
        
        Logger.add_log(Log_Actor.SIMULATION, Log_Granularity.CHAPTER, Log_Action.INITIALIZE,
            f"Chapter initialized with {len(days)} days",
            {
                "chapter_level": meta_progression.chapter_level,
                "player_character": asdict(player_character),
                "days_count": len(days),
                "days": [asdict(day) for day in days]
            }
        )
        return chapter


    def simulate(self) -> bool:

        victory = True

        for day in self.days:
            day.simulate(self.player_character, self.meta_progression)
            if(self.player_character.is_dead()):
                victory = False
                break

        Logger.add_log(
            Log_Actor.SIMULATION, Log_Granularity.CHAPTER, Log_Action.SIMULATE,
            f"Chapter {self.meta_progression.chapter_level} simulation completed with status: {'Victory' if victory else 'Defeat'}",
            {
                "chapter_level": self.meta_progression.chapter_level,
                "player_character": asdict(self.player_character),
                "victory": victory
            }
        )

        return victory

def get_config_value(config_df, row: ConfigKeys, row_key: ConfigKeys, column_key: ConfigKeys) -> Any:
    return config_df.loc[config_df[row.value] == row_key.value, column_key.value].iloc[0]

def get_config_value_str_row(config_df, row: ConfigKeys, row_key: str, column_key: ConfigKeys) -> Any:
    return config_df.loc[config_df[row.value] == row_key, column_key.value].iloc[0]

def simulate_battle(player_character: Player_Character, enemy: EnemyCharacter):

    Logger.add_log(
        Log_Actor.GAME,
        Log_Granularity.BATTLE,
        Log_Action.INITIALIZE, 
        f"Battle initialized between player and {enemy.type.value}",
        {
            "player_character": asdict(player_character),
            "enemy": asdict(enemy)
        }
    )

    while not player_character.is_dead() and not enemy.is_dead():
        # Player attacks enemy
        damage_to_enemy = max(0, player_character.stat_atk - enemy.stat_def)
        enemy.modify_hp(-damage_to_enemy)

        Logger.add_log(
            Log_Actor.GAME, Log_Granularity.TURN, Log_Action.PLAYER_ATTACK,
            f"Player attacks {enemy.type.value} for {damage_to_enemy} damage. Enemy HP: {enemy.stat_hp}/{enemy.stat_max_hp}",
            {"player_character": asdict(player_character),
             "enemy": asdict(enemy), 
             "damage": damage_to_enemy})

        if enemy.is_dead():
            Logger.add_log(
                Log_Actor.GAME, Log_Granularity.BATTLE, Log_Action.ENEMY_DEFEATED,
                f"Enemy {enemy.type.value} defeated!",
                {
                    "player_character": asdict(player_character),
                    "enemy": asdict(enemy),
                }
            )
            break

        # Enemy attacks player
        damage_to_player = max(0, enemy.stat_atk - player_character.stat_def)
        player_character.modify_hp(-damage_to_player)

        Logger.add_log(
            Log_Actor.GAME, Log_Granularity.TURN, Log_Action.ENEMY_ATTACK,
            f"{enemy.type.value} attacks player for {damage_to_player} damage. Player HP: {player_character.stat_hp}/{player_character.stat_max_hp}",
            {"player_character": asdict(player_character),
             "enemy": asdict(enemy), 
             "damage": damage_to_player})

        if player_character.is_dead():

            Logger.add_log(
                Log_Actor.GAME, Log_Granularity.BATTLE, Log_Action.PLAYER_DEFEATED,
                "Player defeated!",
                {
                    "player_character": asdict(player_character),
                    "enemy": asdict(enemy)
                }
            )
            break

    return

def model(main_config: Config):

    Logger.add_log(
        Log_Actor.SIMULATION, Log_Granularity.SIMULATION, Log_Action.INITIALIZE,
        "Model initialized",{})

    
    Logger.clear_logs()

    gear_levels_config = main_config.gear_levels_df
    gear_merge_config = main_config.gear_merge_df
    chapters_config = main_config.chapters_df
    
    Logger.add_log(
        Log_Actor.SIMULATION, Log_Granularity.SIMULATION, Log_Action.INITIALIZE,
        "Model initialized configs: player and enemies",
        {"gear_levels_config": gear_levels_config,
         "gear_merge_config": gear_merge_config,
         "chapters_config": chapters_config})

    meta_progression = Player_meta_progression.initialize(gear_levels_config, gear_merge_config)

    rounds_done = 0
    max_allowed_rounds = 5 #TODO: Turn into config value

    # Chapters Sequence Loop
    while(rounds_done<=max_allowed_rounds and meta_progression.chapter_level<=total_chapters):
        rounds_done+=1

        Logger.add_log(
            Log_Actor.SIMULATION, Log_Granularity.CHAPTER, Log_Action.SIMULATE,
            f"Starting simulation for chapter {meta_progression.chapter_level} in round {rounds_done}",
            {"chapter_level": meta_progression.chapter_level,
             "rounds_done": rounds_done,
             "meta_progression": asdict(meta_progression)})
        
        # Chapter Simulation
        chapter_level = meta_progression.chapter_level
        chapter_config = main_config.get_chapter_config(chapter_level)
        chapter = Chapter.initialize(chapter_config, meta_progression, enemies_config)
        victory_bool = chapter.simulate()

        # Chapter Simulation
        Logger.add_log(
            Log_Actor.SIMULATION, Log_Granularity.CHAPTER, Log_Action.SIMULATE,
            f"Chapter {chapter_level} simulation in round {rounds_done} completed with status: {'Victory' if victory_bool else 'Defeat'}",
            {"chapter_level": chapter_level,
             "victory": victory_bool,
             "meta_progression": asdict(meta_progression)}
        )

        # Meta Progression Simulation
        meta_progression.simulate()

        if victory_bool:
            meta_progression.chapter_level += 1 
            

    return
