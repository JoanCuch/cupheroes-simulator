from dataclasses import dataclass, field
from typing import List, Dict, Any
import pandas as pd
import random
import streamlit as st
import config_import as config_import
from config_import import ConfigKeys, Config



@dataclass
class Meta_stat:
    name: str = ""
    initial_value: int = 0
    meta_bonus_base: int = 0
    meta_bonus_exp: int = 0
    meta_cost_base: int = 0
    meta_cost_exp: int = 0
    level: int = 0

    def get_bonus(self) -> int:
        return self.meta_bonus_base + self.meta_bonus_exp * self.level
    
    def get_bonus_increment(self) -> int:
        return self.meta_bonus_base + self.meta_bonus_exp * (self.level + 1) - (self.meta_bonus_base + self.meta_bonus_exp * self.level)
    
    def get_cost(self) -> int:
        return self.meta_cost_base + self.meta_cost_exp * self.level
    
    def level_up(self):
        self.level += 1

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
            name=get_config_value(player_config_df, ConfigKeys.STAT_ATK, ConfigKeys.STAT_NAME),
            initial_value=get_config_value(player_config_df, ConfigKeys.STAT_ATK, ConfigKeys.STAT_INITIAL_VALUE),
            meta_bonus_base=get_config_value(player_config_df, ConfigKeys.STAT_ATK, ConfigKeys.STAT_META_BONUS_BASE),
            meta_bonus_exp=get_config_value(player_config_df, ConfigKeys.STAT_ATK, ConfigKeys.STAT_META_BONUS_EXP),
            meta_cost_base=int(get_config_value(player_config_df, ConfigKeys.STAT_ATK, ConfigKeys.STAT_META_COST_BASE)),
            meta_cost_exp=int(get_config_value(player_config_df, ConfigKeys.STAT_ATK, ConfigKeys.STAT_META_COST_EXP)),
            level=0
        )
        stat_def = Meta_stat(
            name=get_config_value(player_config_df, ConfigKeys.STAT_DEF, ConfigKeys.STAT_NAME),
            initial_value=get_config_value(player_config_df, ConfigKeys.STAT_DEF, ConfigKeys.STAT_INITIAL_VALUE),
            meta_bonus_base=get_config_value(player_config_df, ConfigKeys.STAT_DEF, ConfigKeys.STAT_META_BONUS_BASE),
            meta_bonus_exp=get_config_value(player_config_df, ConfigKeys.STAT_DEF, ConfigKeys.STAT_META_BONUS_EXP),
            meta_cost_base=int(get_config_value(player_config_df, ConfigKeys.STAT_DEF, ConfigKeys.STAT_META_COST_BASE)),
            meta_cost_exp=int(get_config_value(player_config_df, ConfigKeys.STAT_DEF, ConfigKeys.STAT_META_COST_EXP)),
            level=0
        )
        stat_max_hp = Meta_stat(
            name="max_hp",
            initial_value=player_config_df.loc[player_config_df[ConfigKeys.STAT_NAME.value] == ConfigKeys.STAT_MAX_HP.value, ConfigKeys.STAT_INITIAL_VALUE.value].iloc[0],
            meta_bonus_base=int(player_config_df.loc[player_config_df[ConfigKeys.STAT_NAME.value] == ConfigKeys.STAT_MAX_HP.value, ConfigKeys.STAT_META_BONUS_BASE.value].iloc[0]),
            meta_bonus_exp=int(player_config_df.loc[player_config_df[ConfigKeys.STAT_NAME.value] == ConfigKeys.STAT_MAX_HP.value, ConfigKeys.STAT_META_BONUS_EXP.value].iloc[0]),
            meta_cost_base=int(player_config_df.loc[player_config_df[ConfigKeys.STAT_NAME.value] == ConfigKeys.STAT_MAX_HP.value, ConfigKeys.STAT_META_COST_BASE.value].iloc[0]),
            meta_cost_exp=int(player_config_df.loc[player_config_df[ConfigKeys.STAT_NAME.value] == ConfigKeys.STAT_MAX_HP.value, ConfigKeys.STAT_META_COST_EXP.value].iloc[0]),
            level=0
        )       
        gold = 0
        chapter = 0

        return Player_meta_progression(
            stat_atk=stat_atk,
            stat_def=stat_def,
            stat_max_hp=stat_max_hp,
            gold=gold,
            chapter_level=chapter
        )
    
    def get_cheapest_stat(self) -> Meta_stat:
        stats = [self.stat_atk, self.stat_def, self.stat_max_hp]
        return min(stats, key=lambda stat: stat.get_cost())
    
    def simulate_meta_progression(self):
    #get cheapest stat to upgrade
        stat = self.get_cheapest_stat()
        st.write(f"Cheapest stat to upgrade: {stat.name} with cost {stat.get_cost()} and bonus {stat.get_bonus_increment()}")

        if self.gold >= stat.get_cost():
            self.gold -= stat.get_cost()
            stat.level += 1
            st.write(f"Upgraded {stat.name} to level {stat.level}")
            
        return

@dataclass
class PlayerCharacter:
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

    def is_dead(self) -> bool:
        return self.stat_hp <= 0
    
@dataclass
class EnemyCharacter:
    type: str
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

@dataclass
class Simulation_Log:
    chapters_log : List[Dict['str','Chapter_Log']] = field(default_factory=list)
    #TODO

@dataclass
class Chapter_Log:
    status: str  # 'win' | 'lose' | 'ongoing'
    daily_log: List[Dict[str, Any]] = field(default_factory=list)

    def add_day(self, day: int, event_name: str, player: PlayerCharacter):
        self.daily_log.append({
            "day": day,
            "event_name": event_name,
            "player_atk": player.stat_atk,
            "player_def": player.stat_def,
            "player_hp": player.stat_hp,
            "player_maxhp": player.stat_max_hp,
            "player_delta_atk": self.daily_log[-1]["player_atk"]-player.stat_atk if self.daily_log else 0,
            "player_delta_def": self.daily_log[-1]["player_def"]-player.stat_def if self.daily_log else 0,
            "player_delta_hp": self.daily_log[-1]["player_hp"]-player.stat_hp if self.daily_log else 0,
            "player_delta_maxhp": self.daily_log[-1]["player_maxhp"]-player.stat_max_hp if self.daily_log else 0
        })

def get_config_value(config_df, row_key: ConfigKeys, column_key: ConfigKeys) -> Any:
    return config_df.loc[config_df[ConfigKeys.STAT_NAME.value] == row_key.value, column_key.value].iloc[0]

def initialize_chapter_config(chapter_config_df, enemies_df) -> List[Dict]:

    events = []
    st.dataframe(chapter_config_df)


    for index, row in chapter_config_df.iterrows():

        daily_event = row[ConfigKeys.CHAPTER_DAILY_EVENT.value]
        daily_event_param = row[ConfigKeys.CHAPTER_DAILY_EVENT_PARAM.value]
        reward = int(row[ConfigKeys.CHAPTER_DAILY_GOLD_REWARD.value])

        if daily_event == "atk":
            events.append({"type": "atk", "apply": lambda player, n=daily_event_param: player.modify_atk(int(n)), "reward": reward})
        elif daily_event == "def":
            events.append({"type": "def", "apply": lambda player, n=daily_event_param: player.modify_def(int(n)), "reward": reward})
        elif daily_event == "hp":
            events.append({"type": "hp", "apply": lambda player, n=daily_event_param: player.modify_hp(int(n)), "reward": reward})
        elif daily_event == "battle":
            enemy_row = enemies_df[enemies_df["enemy_type"] == daily_event_param].iloc[0]
            events.append({
                "type": "battle",
                "apply": EnemyCharacter(
                    type=enemy_row["enemy_type"],
                    stat_atk=int(enemy_row["enemy_atk"]),
                    stat_def=int(enemy_row["enemy_def"]),
                    stat_max_hp=int(enemy_row["enemy_max_hp"]),
                    stat_hp=int(enemy_row["enemy_max_hp"])
                ),
                "reward": reward
            })

    return events

def initialize_player_character(config_df, meta_progression: Player_meta_progression) -> PlayerCharacter:
    stat_atk = get_config_value(config_df, ConfigKeys.STAT_ATK, ConfigKeys.STAT_INITIAL_VALUE) + meta_progression.stat_atk.get_bonus()
    stat_def = get_config_value(config_df, ConfigKeys.STAT_DEF, ConfigKeys.STAT_INITIAL_VALUE) + meta_progression.stat_def.get_bonus()
    stat_max_hp = get_config_value(config_df, ConfigKeys.STAT_MAX_HP, ConfigKeys.STAT_INITIAL_VALUE) + meta_progression.stat_max_hp.get_bonus()
    stat_hp = stat_max_hp

    player = PlayerCharacter(stat_atk=stat_atk, stat_def=stat_def, stat_hp=stat_hp, stat_max_hp=stat_max_hp)
    return player

def simulate_battle(player: PlayerCharacter, enemy: EnemyCharacter) ->  List[str]:
    
    battle_log = []

    while not player.is_dead() and not enemy.is_dead():
        # Player attacks enemy
        damage_to_enemy = max(0, player.stat_atk - enemy.stat_def)
        enemy.modify_hp(-damage_to_enemy)
        battle_log.append(f"Player attacks {enemy.type} for {damage_to_enemy} damage. Enemy HP: {enemy.stat_hp}/{enemy.stat_max_hp}")

        if enemy.is_dead():
            battle_log.append(f"{enemy.type} defeated!")
            break

        # Enemy attacks player
        damage_to_player = max(0, enemy.stat_atk - player.stat_def)
        player.modify_hp(-damage_to_player)
        battle_log.append(f"{enemy.type} attacks player for {damage_to_player} damage. Player HP: {player.stat_hp}/{player.stat_max_hp}")

        if player.is_dead():
            battle_log.append("Battle ended: Player defeated!")
            break

    st.dataframe(battle_log)
    battle_log.append("Battle ended")
    return battle_log

def simulate_chapter(player: PlayerCharacter, meta_progression: Player_meta_progression, events: List[Dict]) -> Chapter_Log:

    chapter_log = Chapter_Log(status="ongoing")
    day = 0

    chapter_log.add_day(day, "start", player)

    for event in events:
        day += 1

        if event["type"] == "battle":
            simulate_battle(player, event["apply"])
            chapter_log.add_day(day, event["type"], player)
            st.write(f"Day {day}: Battle with {event['apply'].type} completed, player stats: atk={player.stat_atk}, def={player.stat_def}, hp={player.stat_hp}/{player.stat_max_hp}")               
        else:
            event["apply"](player)
            chapter_log.add_day(day, event["type"], player)
            st.write(f"Day {day}: {event['type']} applied, player stats: atk={player.stat_atk}, def={player.stat_def}, hp={player.stat_hp}/{player.stat_max_hp}")   

        if player.is_dead():
            chapter_log.status = "lose"
            return chapter_log
        else:
            meta_progression.gold += event["reward"]

    chapter_log.status = "win"
    return chapter_log



def model(config: Config) -> List[Chapter_Log]:
    chapter_logs = []
    player_config = config.get_player_config()
    enemies_config = config.get_enemies_config()

    meta_progression = Player_meta_progression.initialize(player_config)
    total_chapters = config.get_total_chapters()
    total_rounds = 0
    meta_progression.chapter_level += 1 


    # Chapters Sequence Loop
    while(total_rounds<=5 and meta_progression.chapter_level<=total_chapters):
    #for totalrounds in range(1, total_chapters+1): 
        total_rounds+=1
        chapter_number = meta_progression.chapter_level
        st.write(f"Simulating Chapter {chapter_number}")

        # Chapter initialization
        chapter_config = config.get_chapter_config(chapter_number)
        chapter = initialize_chapter_config(chapter_config, enemies_config)
        player_character = initialize_player_character(player_config, meta_progression)

        # Chapter Simulation
        chapter_log = simulate_chapter(player_character,meta_progression, chapter)
        chapter_logs.append(chapter_log)

        # Meta Progression Simulation
        meta_progression.simulate_meta_progression()

        st.write(f"Chapter {chapter_number} completed with status: {chapter_log.status}")

        if chapter_log.status == "win":
            st.write(f"Chapter {chapter_number} won! Player stats: atk={player_character.stat_atk}, def={player_character.stat_def}, hp={player_character.stat_hp}/{player_character.stat_max_hp}")
            meta_progression.chapter_level += 1 

    return chapter_logs
