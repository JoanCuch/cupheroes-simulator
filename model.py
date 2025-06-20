from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
import pandas as pd
import config_import as config_import
from config_import import ConfigKeys, Config
from enum import Enum
import copy

@dataclass
class Meta_stat:
    _name: str = ""
    _initial_value: int = 0
    _meta_bonus_base: int = 0
    _meta_bonus_exp: int = 0
    _meta_cost_base: int = 0
    _meta_cost_exp: int = 0
    _level: int = 0

    def get_value(self) -> int:
        return self._initial_value + self._meta_bonus_exp * self._level
    
    def get_bonus_increment(self) -> int:
        return self._initial_value + self._meta_bonus_exp * (self._level + 1) - (self._initial_value + self._meta_bonus_exp * self._level)

    def get_cost(self) -> int:
        return self._meta_cost_base + self._meta_cost_exp * self._level

    def level_up(self):
        self._level += 1

    def get_level(self) -> int:
        return self._level

@dataclass
class Player_meta_progression:
    stat_atk: Meta_stat
    stat_def: Meta_stat
    stat_max_hp: Meta_stat
    
    gold: int = 0
    chapter_level: int = 0

    @staticmethod
    def initialize(player_config_df) -> 'Player_meta_progression':
        stat_atk = Meta_stat(
            _name=get_config_value(player_config_df, ConfigKeys.STAT_NAME, ConfigKeys.STAT_ATK, ConfigKeys.STAT_NAME),
            _initial_value=get_config_value(player_config_df, ConfigKeys.STAT_NAME,ConfigKeys.STAT_ATK, ConfigKeys.STAT_INITIAL_VALUE),
            _meta_bonus_base=get_config_value(player_config_df, ConfigKeys.STAT_NAME,ConfigKeys.STAT_ATK, ConfigKeys.STAT_META_BONUS_BASE),
            _meta_bonus_exp=get_config_value(player_config_df,ConfigKeys.STAT_NAME, ConfigKeys.STAT_ATK, ConfigKeys.STAT_META_BONUS_EXP),
            _meta_cost_base=int(get_config_value(player_config_df, ConfigKeys.STAT_NAME,ConfigKeys.STAT_ATK, ConfigKeys.STAT_META_COST_BASE)),
            _meta_cost_exp=int(get_config_value(player_config_df, ConfigKeys.STAT_NAME,ConfigKeys.STAT_ATK, ConfigKeys.STAT_META_COST_EXP)),
            _level=0
        )
        stat_def = Meta_stat(
            _name=get_config_value(player_config_df, ConfigKeys.STAT_NAME,ConfigKeys.STAT_DEF, ConfigKeys.STAT_NAME),
            _initial_value=get_config_value(player_config_df, ConfigKeys.STAT_NAME,ConfigKeys.STAT_DEF, ConfigKeys.STAT_INITIAL_VALUE),
            _meta_bonus_base=get_config_value(player_config_df,ConfigKeys.STAT_NAME, ConfigKeys.STAT_DEF, ConfigKeys.STAT_META_BONUS_BASE),
            _meta_bonus_exp=get_config_value(player_config_df, ConfigKeys.STAT_NAME,ConfigKeys.STAT_DEF, ConfigKeys.STAT_META_BONUS_EXP),
            _meta_cost_base=int(get_config_value(player_config_df, ConfigKeys.STAT_NAME,ConfigKeys.STAT_DEF, ConfigKeys.STAT_META_COST_BASE)),
            _meta_cost_exp=int(get_config_value(player_config_df,ConfigKeys.STAT_NAME, ConfigKeys.STAT_DEF, ConfigKeys.STAT_META_COST_EXP)),
            _level=0
        )
        stat_max_hp = Meta_stat(
            _name=get_config_value(player_config_df, ConfigKeys.STAT_NAME,ConfigKeys.STAT_MAX_HP, ConfigKeys.STAT_NAME),
            _initial_value=get_config_value(player_config_df, ConfigKeys.STAT_NAME,ConfigKeys.STAT_MAX_HP, ConfigKeys.STAT_INITIAL_VALUE),
            _meta_bonus_base=get_config_value(player_config_df, ConfigKeys.STAT_NAME,ConfigKeys.STAT_MAX_HP, ConfigKeys.STAT_META_BONUS_BASE),
            _meta_bonus_exp=int(get_config_value(player_config_df, ConfigKeys.STAT_NAME,ConfigKeys.STAT_MAX_HP, ConfigKeys.STAT_META_BONUS_EXP)),
            _meta_cost_base=int(get_config_value(player_config_df, ConfigKeys.STAT_NAME,ConfigKeys.STAT_MAX_HP, ConfigKeys.STAT_META_COST_BASE)),
            _meta_cost_exp=int(get_config_value(player_config_df, ConfigKeys.STAT_NAME,ConfigKeys.STAT_MAX_HP, ConfigKeys.STAT_META_COST_EXP)),
            _level=0
        )       
        gold = 0
        chapter = 1

        new_meta = Player_meta_progression(
            stat_atk=stat_atk,
            stat_def=stat_def,
            stat_max_hp=stat_max_hp,
            gold=gold,
            chapter_level=chapter
        )
        Logger.add_log(AT.META, AS.INIT, {
            "str": "Meta progression initialized",
            "copy": new_meta
        })
        return new_meta

    def add_gold(self, value:int):
        self.gold+= value
        return
    
    def get_cheapest_stat(self) -> Meta_stat:
        stats = [self.stat_atk, self.stat_def, self.stat_max_hp]
        return min(stats, key=lambda stat: stat.get_cost())
    
    def simulate_meta_progression(self):
    #get cheapest stat to upgrade
        stat = self.get_cheapest_stat()
        Logger.add_log(AT.META, AS.SIMULATE, {
            "str": f"Cheapest stat to upgrade: {stat._name} with cost {stat.get_cost()} and bonus {stat.get_bonus_increment()}",
            "copy": {
                "stat_name": stat._name,
                "cost": stat.get_cost(),
                "bonus_increment": stat.get_bonus_increment(),
                "gold_available": self.gold
            }
        })

        if self.gold >= stat.get_cost():
            self.gold -= stat.get_cost()
            stat.level_up()
            Logger.add_log(AT.META, AS.SIMULATE, {
                "str": f"Upgraded {stat._name} to level {stat.get_level()}",
                "copy": {
                    "stat_name": stat._name,
                    "new_level": stat.get_level(),
                    "new_value": stat.get_value(),
                    "new_cost": stat.get_cost()
                }
            })

        return

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
        Logger.add_log(AT.CHAPTER, AS.INIT_PLAYER_CHARACTER, {
            "str": "Player character initialized",
            "copy": new_character
        })

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

        Logger.add_log(AT.CHAPTER, AS.INIT_ENEMY, {
            "str": f"Enemy character initialized: {new_enemy.type.value}",
            "copy": new_enemy
        })

        return new_enemy

@dataclass
class Day:

    class EventType(Enum):
        INCREASE_ATK = "increase_atk"
        INCREASE_DEF = "increase_def"
        INCREASE_MAX_HP = "increase_max_hp"
        RESTORE_HP = "restore_hp"
        BATTLE = "battle"    

    _event_param: Any
    _gold_reward: int
    _event_type: EventType
    _event_enemy: Optional[EnemyCharacter]

    @staticmethod
    def initialize(day_config, enemies_config) -> 'Day':
        event_name = day_config[ConfigKeys.CHAPTER_DAILY_EVENT.value]
        event_type = Day.EventType(event_name)
        event_param = day_config[ConfigKeys.CHAPTER_DAILY_EVENT_PARAM.value]
        gold_reward = int(day_config[ConfigKeys.CHAPTER_DAILY_GOLD_REWARD.value]) 

        # Convert event_param to int for numeric operations
        if event_type in [Day.EventType.INCREASE_ATK, Day.EventType.INCREASE_DEF, 
                      Day.EventType.INCREASE_MAX_HP, Day.EventType.RESTORE_HP]:
            event_param = int(event_param)

        enemy_type = None
        if event_type == Day.EventType.BATTLE:
            enemy_type = EnemyCharacter.Enemy_Types(event_param) 

        new_day =  Day(
            _event_type=event_type,
            _event_param=event_param,
            _gold_reward=gold_reward,
            _event_enemy=EnemyCharacter.initialize(
                enemies_config,
                enemy_type
            ) if enemy_type else None
        )   

        Logger.add_log(AT.DAY, AS.INIT, {
            "str": f"Day initialized with event {event_name}",
            "copy": new_day
        })

        return new_day

    def simulate(self, player_character: Player_Character, meta_progression: Player_meta_progression):

        match self._event_type:
            case Day.EventType.INCREASE_ATK:
                player_character.modify_atk(self._event_param)
                meta_progression.add_gold(self._gold_reward)
            case Day.EventType.INCREASE_DEF:
                player_character.modify_def(self._event_param)
                meta_progression.add_gold(self._gold_reward)
            case Day.EventType.INCREASE_MAX_HP:
                player_character.modify_max_hp(self._event_param)
                meta_progression.add_gold(self._gold_reward)
            case Day.EventType.RESTORE_HP:
                player_character.modify_hp(self._event_param)
                meta_progression.add_gold(self._gold_reward)
            case Day.EventType.BATTLE:
                if self._event_enemy is None:
                    raise ValueError("Battle event requires an enemy character.")
                simulate_battle(player_character, self._event_enemy)
                if(not player_character.is_dead()):
                    meta_progression.add_gold(self._gold_reward)
            case _:
                raise ValueError(f"Unknown event type: {self._event_type}")
            
        Logger.add_log(AT.DAY, AS.DAY_EVENT, {
            "str": f"Day event {self._event_type.value} simulated",
            "copy": {
                "event_type": self._event_type.value,
                "event_param": self._event_param,
                "gold_reward": self._gold_reward,
                "player_character": {
                    "atk": player_character.stat_atk,
                    "def": player_character.stat_def,
                    "hp": player_character.stat_hp,
                    "max_hp": player_character.stat_max_hp
                }
            }
        })

        return


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
        
        Logger.add_log(AT.CHAPTER, AS.INIT, {
            "str": f"Chapter initialized with {len(days)} days",
            "copy": chapter         
        })    
        return chapter


    def simulate(self) -> bool:

        victory = True

        for day in self.days:
            day.simulate(self.player_character, self.meta_progression)
            if(self.player_character.is_dead()):
                victory = False
                break

        Logger.add_log(AT.CHAPTER, AS.SIMULATE, {
            "str": f"Chapter simulation completed with status: {'Victory' if victory else 'Defeat'}",
            "copy": {
                "player_character": {
                    "atk": self.player_character.stat_atk,
                    "def": self.player_character.stat_def,
                    "hp": self.player_character.stat_hp,
                    "max_hp": self.player_character.stat_max_hp
                },
                "meta_progression": {
                    "gold": self.meta_progression.gold,
                    "chapter_level": self.meta_progression.chapter_level
                },
                "victory": victory
            }
        })

        return victory

class AT(Enum):
    MODEL = "model"
    META = "meta"
    CHAPTER = "chapter"
    DAY = "day"
    BATTLE = "battle"
    PLAYER = "player"

class AS(Enum):
    INIT = "init"
    SIMULATE = "simulate"
    INIT_ENEMY = "init_enemy"
    INIT_PLAYER_CHARACTER = "init_player_character"
    UPGRADE_STAT = "upgrade_stat"
    START_CHAPTER = "start_chapter"
    DAY_EVENT = "day_event"
    ENEMY_ATTACK = "enemy_attack"
    PLAYER_ATTACK = "player_attack"
    END_BATTLE = "end_battle"
    GAIN_GOLD = "gain_gold"
    END = "end"

class Logger:
    _logs = []

    @classmethod
    def add_log(cls, action_type: AT, action_subtype: AS, payload: dict):
        log_entry = {
            "type": action_type.value,
            "subtype": action_subtype.value,
            "payload": copy.deepcopy(payload) if payload else {},
        }
        cls._logs.append(log_entry)

    @classmethod
    def get_logs(cls):
        return cls._logs

    @classmethod
    def clear_logs(cls):
        cls._logs = []

def get_config_value(config_df, row: ConfigKeys, row_key: ConfigKeys, column_key: ConfigKeys) -> Any:
    return config_df.loc[config_df[row.value] == row_key.value, column_key.value].iloc[0]

def get_config_value_str_row(config_df, row: ConfigKeys, row_key: str, column_key: ConfigKeys) -> Any:
    return config_df.loc[config_df[row.value] == row_key, column_key.value].iloc[0]

def simulate_battle(player_character: Player_Character, enemy: EnemyCharacter):

    while not player_character.is_dead() and not enemy.is_dead():
        # Player attacks enemy
        damage_to_enemy = max(0, player_character.stat_atk - enemy.stat_def)
        enemy.modify_hp(-damage_to_enemy)
        Logger.add_log(AT.BATTLE, AS.PLAYER_ATTACK, {
            "str": f"Player attacks {enemy.type} for {damage_to_enemy} damage. Enemy HP: {enemy.stat_hp}/{enemy.stat_max_hp}",
            "copy": {
                "enemy_type": enemy.type.value,
                "damage": damage_to_enemy,
                "enemy_hp": enemy.stat_hp,
                "enemy_max_hp": enemy.stat_max_hp
            }
        })

        if enemy.is_dead():
            Logger.add_log(AT.BATTLE, AS.END_BATTLE, {
                "str": f"{enemy.type} defeated!",
                "copy": {
                    "enemy_type": enemy.type.value,
                    "enemy_hp": enemy.stat_hp,
                    "enemy_max_hp": enemy.stat_max_hp
                }
            })
            break

        # Enemy attacks player
        damage_to_player = max(0, enemy.stat_atk - player_character.stat_def)
        player_character.modify_hp(-damage_to_player)
        Logger.add_log(AT.BATTLE, AS.ENEMY_ATTACK, {
            "str": f"{enemy.type} attacks player for {damage_to_player} damage. Player HP: {player_character.stat_hp}/{player_character.stat_max_hp}",
            "copy": {
                "enemy_type": enemy.type.value,
                "damage": damage_to_player,
                "player_hp": player_character.stat_hp,
                "player_max_hp": player_character.stat_max_hp
            }
        })
        if player_character.is_dead():
            Logger.add_log(AT.BATTLE, AS.END_BATTLE, {
                "str": "Battle ended: Player defeated!",
                "copy": {
                    "player_hp": player_character.stat_hp,
                    "player_max_hp": player_character.stat_max_hp
                }
            })
            break

    return

def model(main_config: Config) -> List[dict]:

    player_config = main_config.get_player_config()
    enemies_config = main_config.get_enemies_config()
    total_chapters = main_config.get_total_chapters()
    Logger.add_log(AT.MODEL, AS.INIT, {"str": "Model initialized with main config", "copy": {"player_config": player_config, "enemies_config": enemies_config, "total_chapters": total_chapters}})

    meta_progression = Player_meta_progression.initialize(player_config)


    rounds_done = 0
    max_allowed_rounds = 5 #TODO: Turn into config value

    # Chapters Sequence Loop
    while(rounds_done<=max_allowed_rounds and meta_progression.chapter_level<=total_chapters):
        rounds_done+=1
        
        # Chapter Simulation
        chapter_level = meta_progression.chapter_level
        chapter_config = main_config.get_chapter_config(chapter_level)
        chapter = Chapter.initialize(chapter_config, meta_progression, enemies_config)
        victory_bool = chapter.simulate()

        # Chapter Simulation
        #chapter_log = simulate_chapter(player_character,meta_progression, chapter)
        #chapter_logs.append(chapter_log)
        #TODO Log

        # Meta Progression Simulation
        meta_progression.simulate_meta_progression()

        #st.write(f"Chapter {chapter_number} completed with status: {chapter_log.status}")

        if victory_bool:
            meta_progression.chapter_level += 1 

    Logger.add_log(AT.MODEL, AS.END, {
        "str": "Model simulation ended at chapter level " + str(meta_progression.chapter_level),
        "copy": {
            "player_meta_progression": meta_progression,
            "chapter_level": meta_progression.chapter_level
        }
    })
    return Logger.get_logs()
