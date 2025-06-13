from dataclasses import dataclass, field
from typing import List, Dict, Any
import pandas as pd
import random
import streamlit as st

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
class Daily_Log:
    
    log: List[Dict[str, Any]] = field(default_factory=list)

    def add_day(self, day: int, event_name: str, player: PlayerCharacter):
        self.log.append({
            "day": day,
            "event_name": event_name,
            "player_atk": player.stat_atk,
            "player_def": player.stat_def,
            "player_hp": player.stat_hp,
            "player_maxhp": player.stat_max_hp,
            "player_delta_atk": self.log[-1]["player_atk"]-player.stat_atk if self.log else 0,
            "player_delta_def": self.log[-1]["player_def"]-player.stat_def if self.log else 0,
            "player_delta_hp": self.log[-1]["player_hp"]-player.stat_hp if self.log else 0,
            "player_delta_maxhp": self.log[-1]["player_maxhp"]-player.stat_max_hp if self.log else 0
        })

    def to_dataframe(self) -> pd.DataFrame:
        return pd.DataFrame(self.log)

@dataclass
class Chapter_Log:
    status: str  # 'win' | 'lose'
    daily_log: Daily_Log



    

def simulate_chapter(player: PlayerCharacter, events: List[Dict]) -> Chapter_Log:

    daily_log = Daily_Log()
    day = 0

    daily_log.add_day(day, "start", player)

    for event in events:
        day += 1

        if "apply" in event:
            event["apply"](player)
            daily_log.add_day(day, event["type"], player)
            st.write(f"Day {day}: {event['type']} applied, player stats: atk={player.stat_atk}, def={player.stat_def}, hp={player.stat_hp}/{player.stat_max_hp}")   

        if player.is_dead():
            return Chapter_Log("lose", daily_log)

    return Chapter_Log("win", daily_log)



def initialize_events(config_df) -> List[Dict]:

    config_events = config_df[["stat", "number"]]

    events = []
    
    for _, row in config_events.iterrows():
        stat = row["stat"]
        number = row["number"]

        if stat == "atk":
            events.append({"type": "atk", "apply": lambda player, n=number: player.modify_atk(n)})
        elif stat == "def":
            events.append({"type": "def", "apply": lambda player, n=number: player.modify_def(n)})
        elif stat == "hp":
            events.append({"type": "hp", "apply": lambda player, n=number: player.modify_hp(n)})

    return events


def model(config_df) -> Chapter_Log:

    stat_atk = int(config_df.loc[config_df["key"] == "atk", "value"].values[0])
    stat_def = int(config_df.loc[config_df["key"] == "def", "value"].values[0])
    stat_hp = int(config_df.loc[config_df["key"] == "hp", "value"].values[0])
    stat_max_hp = int(config_df.loc[config_df["key"] == "max_hp", "value"].values[0])
    days = int(config_df.loc[config_df["key"] == "days", "value"].values[0])

    player = PlayerCharacter(stat_atk=stat_atk, stat_def=stat_def, stat_hp=stat_hp, stat_max_hp=stat_max_hp)

    config_events = initialize_events(config_df)
  
    # Run simulation
    chapter_log = simulate_chapter(player, config_events)
    return chapter_log