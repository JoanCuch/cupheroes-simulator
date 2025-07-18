from enum import Enum
import copy

class Log_Action(Enum) :
    INITIALIZE = "initialize"
    SIMULATE = "simulate"
    END = "end"
    PLAYER_ATTACK = "player_attack"
    ENEMY_ATTACK = "enemy_attack"
    PLAYER_DEFEATED = "player_defeated"
    ENEMY_DEFEATED = "enemy_defeated"
    MERGE = "merge"
    LEVEL_UP = "level_up"
    OPEN_GACHA = "open_gacha"
    ADD_GEAR = "add_gear"
    WIN_CHAPTER = "win_chapter"
    LOSE_CHAPTER = "lose_chapter"
    ADD_DESIGNS = "add_designs" 
    EQUIP_GEAR = "equip_gear"
    DAILY_FREE_GACHA = "daily_free_gacha"
    PURCHASE_OFFER = "purchase_offer"

class Logger:
    _logs = []

    @classmethod
    def add_log(cls, action: Log_Action, time, message: str, payload: dict):
        log_entry = {
            "action": action.value,
            "time": time,
            "message": message,
            "payload": copy.deepcopy(payload) if payload else {},
        }
        cls._logs.append(log_entry)

    @classmethod
    def get_logs(cls):
        return cls._logs

    @classmethod
    def clear_logs(cls):
        cls._logs = []

    @classmethod
    def get_logs_as_dataframe(cls):
        import pandas as pd
        return pd.DataFrame(cls._logs)

    @classmethod
    def has_logs(cls):
        return len(cls._logs) > 0
    
    @classmethod
    def get_flattened_logs_df(cls):
        import pandas as pd
        raw_logs = cls.get_logs_as_dataframe().to_dict(orient="records")

        flattened_df = pd.json_normalize(
            raw_logs,
            sep="."  # aplanar tots els nivells amb noms com 'payload.player_character.hp'
        )

        if "payload" in flattened_df.columns:
            flattened_df = flattened_df.drop(columns=["payload"])

        return flattened_df