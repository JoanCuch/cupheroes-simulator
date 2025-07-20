from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional
import random
import pandas as pd
import config_import as config_import
from config_import import ConfigKeys, Config
from enum import Enum, IntEnum

from logger import Logger, Log_Action

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
    WEAPON = "weapon    "
    RING = "ring"
    GLOVES = "gloves"
    HELMET = "helmet"
    ARMOR = "armor"
    BOOTS = "boots"
    DEFAULT = "default"

class Gear_rarity(IntEnum):
    COMMON = 1
    UNCOMMON = 2
    RARE = 3
    EPIC = 4
    MYTHICAL = 5
    LEGENDARY = 6

    def __str__(self):
        return self.name.lower()
    
    @staticmethod
    def parse(value: "Gear_rarity | str | int") -> "Gear_rarity":
        """Accepta enum, string ('common') o int (1-6) i retorna Gear_rarity."""
        if isinstance(value, Gear_rarity):
            return value
        if isinstance(value, (int, float)):
            return Gear_rarity(int(value))
        if isinstance(value, str):
            return Gear_rarity[value.strip().upper()]
        raise ValueError(f"Unknown rarity value: {value}")
    
@dataclass
class MergeRequirement:
    piece_requirement: Gear_pieces           
    rarity_requirement: Gear_rarity      
    set_requirement: Gear_sets 

@dataclass
class Timer:
    total_time: int
    session_time: int

    play_chapter_time: int
    meta_progression_time: int

    @staticmethod
    def initialize(player_behavior: dict[str, int]) -> 'Timer':
        current_total_time = 0
        current_session_time = 0
        play_chapter_time = player_behavior[ConfigKeys.PLAYER_PLAY_CHAPTER.value]
        meta_progression_time = player_behavior[ConfigKeys.PLAYER_META_PROGRESSION.value]
        return Timer(total_time=current_total_time, session_time=current_session_time, play_chapter_time=play_chapter_time, meta_progression_time=meta_progression_time)

    def increment(self, minutes: int):
        self.total_time += minutes
        self.session_time += minutes
        return
    
    def get_timer_info(self) -> 'Dict[str, int]':
        return {
            "total_time": int(self.total_time),
            "current_day": int(self.current_day()),
            "session_time": int(self.session_time),
        }

    def increment_play_chapter(self):
        self.total_time += self.play_chapter_time
        self.session_time += self.play_chapter_time
        return
    
    def increment_meta_progression(self):
        self.total_time += self.meta_progression_time
        self.session_time += self.meta_progression_time
        return
    
    def current_day(self) -> int:
        return self.total_time // 1440 + 1
    
    def complete_day(self):
        minutes_to_complete = 1440 - (self.total_time % 1440) + 1 # +1 to ensure we get to a new day
        self.increment(minutes_to_complete)
        return
    
    def current_time(self) -> int:
        return self.total_time 

    def current_session_time(self) -> int:
        return self.session_time

    def new_session(self) -> None:
        self.session_time = 0
        return    

@dataclass
class Gear:
    level: int
    set: Gear_sets
    piece: Gear_pieces
    max_rarity: Gear_rarity
    rarity_list: Dict[Gear_rarity, int]
    merge_rules: Dict[Gear_rarity, List[MergeRequirement]]
    level_up_rules: pd.DataFrame
    time: Timer

    @staticmethod
    def initialize(gear_set: Gear_sets, gear_piece: Gear_pieces, gear_levels_df: pd.DataFrame, gear_merge_df: pd.DataFrame, time: Timer) -> 'Gear':

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
            level_up_rules=level_up_rules,
            time=time
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
             and (gear.set == requirement.set_requirement or requirement.set_requirement == Gear_sets.DEFAULT)),
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

        Logger.add_log(
            Log_Action.MERGE,
            self.time.get_timer_info(),   
            f"Successfully merged gear of {self.piece.value} and {self.set.value} to {target_rarity}",
            {
                "piece": self.piece.value,
                "set": self.set.value,
                "target_rarity": str(target_rarity),
                "max_rarity": str(self.max_rarity),
                "rarity_list": {str(rarity): count for rarity, count in self.rarity_list.items()},
                "affected_requirements": [(gear.piece.value, str(rarity)) for gear, rarity in affected_requirements]
            }
        )

        return True

    def level_up(self, meta_progression) -> bool:

        successful_level_up = True

        while (successful_level_up):

            expected_level = self.level + 1
            # Trobar la fila de configuració per a aquest nivell via l’índex
            if expected_level not in self.level_up_rules.index:
                successful_level_up = False
                break

            row_level = self.level_up_rules.loc[expected_level]

            required_gold = row_level[ConfigKeys.GOLD_COST.value]
            required_designs = row_level[ConfigKeys.DESIGN_COST.value]
            required_rarity = row_level[ConfigKeys.REQUIRED_RARITY.value]

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
                    Log_Action.LEVEL_UP,
                    self.time.get_timer_info(),
                    f"Level up gear of {self.piece.value} and {self.set.value} and {self.max_rarity} to level {expected_level}",
                    {
                    "level": self.level,
                    "set": self.set.value,
                    "piece": self.piece.value,
                    "max_rarity": str(self.max_rarity),
                    "required_gold": required_gold,
                    "required_designs": required_designs,
                    "required_rarity": required_rarity
                    }
                )
            else:
                successful_level_up = False

        return successful_level_up


@dataclass
class Player_meta_progression:
    
    gold: int
    gear_inventory: List[Gear]
    designs: Dict[Gear_pieces, int]
    equipped_gear: Dict[Gear_pieces, Gear]
    time: Timer
    chapter_level: int
    merge_rules: Dict[Gear_rarity, List[MergeRequirement]] = field(default_factory=dict)
   

    @staticmethod
    def initialize(gear_levels_config: pd.DataFrame, gear_merge_config: pd.DataFrame, time: Timer) -> 'Player_meta_progression':

        gear_levels_config[ConfigKeys.REQUIRED_RARITY.value] = (gear_levels_config[ConfigKeys.REQUIRED_RARITY.value].apply(Gear_rarity.parse))

        gold = 0
        chapter_level = 1

        designs = {s: 0 for s in Gear_pieces}
        equipped_gear = {}
        merge_rules = {}
        gear_inventory = [
                Gear.initialize(gear_set, gear_piece, gear_levels_config, gear_merge_config, time)
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
            merge_rules=merge_rules,
            time=time,
        )

        Logger.add_log(
            Log_Action.INITIALIZE,
            time.get_timer_info(),
            "Meta progression initialized",
            {"meta_progression": asdict(new_meta) }
            )       

        return new_meta

    def add_gear(self, piece: Gear_pieces, set: Gear_sets, rarity: Gear_rarity):

        matching_gear = next(
            (gear for gear in self.gear_inventory if gear.piece == piece and gear.set == set),
            None
        )

        if (piece == Gear_pieces.DEFAULT or set == Gear_sets.DEFAULT):
            Logger.add_log(
                Log_Action.ERROR,
                self.time.get_timer_info(),
                f"Added gear of {piece.value} and {set.value} to rarity {rarity}",
                {
                    "piece": piece.value,
                    "set": set.value,
                    "rarity": rarity.name
                }
            )

        if matching_gear:
            matching_gear.rarity_list[rarity] += 1

            if matching_gear.level == 0: #in case it is the first time this gear is added
                matching_gear.level = 1

            Logger.add_log(
                Log_Action.ADD_GEAR,
                self.time.get_timer_info(),
                f"Added gear of {piece.value} and {set.value} to rarity {rarity}",
                {
                    "piece": piece.value,
                    "set": set.value,
                    "rarity": rarity.name
                }
            )
        else:
            raise ValueError(f"Gear with piece {piece.value} and set {set.value} not found in inventory.")
        return
    
    def add_designs(self, amount: int):
        chosen_piece = random.choice([piece for piece in self.designs.keys() if piece != Gear_pieces.DEFAULT])
        self.designs[chosen_piece] += amount

        Logger.add_log(
            Log_Action.ADD_DESIGNS,
            self.time.get_timer_info(),
            f"Added {amount} designs to {chosen_piece.value}",
            {
                "piece": chosen_piece.value,
                "amount": amount,
                "total_designs": self.designs[chosen_piece]
            }
        )

    def apply_offer(self, offer_name: str, offers_df: pd.DataFrame, gacha: "Gacha_system") -> None:

        row = offers_df.loc[offers_df[ConfigKeys.OFFER_NAME.value] == offer_name].iloc[0]

        
        rare_chest_to_open = int(row.get("rare_chest", 0) or 0)
        epic_chest_to_open = int(row.get("epic_chest", 0) or 0)
        gold_to_add = int(row.get("gold", 0) or 0)
        designs_to_add = int(row.get("design", 0) or 0)

        Logger.add_log(
            Log_Action.PURCHASE_OFFER,
            self.time.get_timer_info(),
            f"Applied offer {offer_name}",
            {
                "offer_name": offer_name,
                "rare_chests_opened": rare_chest_to_open,
                "epic_chests_opened": epic_chest_to_open,
                "gold_added": gold_to_add,
                "designs_added": designs_to_add
            }
        )
        
        #row = offers_df.loc[offer_name].iloc[0]

        for _ in range(rare_chest_to_open):
            gacha.open_chest(self, ConfigKeys.RARE_CHEST_NAME.value)

        for _ in range(epic_chest_to_open):
            gacha.open_chest(self, ConfigKeys.EPIC_CHEST_NAME.value)

        if gold_to_add > 0:
            self.gold += gold_to_add

        if designs_to_add > 0:
            self.add_designs(designs_to_add)

        

    def simulate(self):

        # Pass Time
        self.time.increment_meta_progression()

        #Merge Gear
        sorted_gear_equipped = sorted(self.equipped_gear.items(), key=lambda g: g[1].level, reverse=False)

        for (piece_type, gear) in sorted_gear_equipped:
            for rarity in Gear_rarity:
                if rarity != Gear_rarity.COMMON:
                    success = gear.merge(rarity, self.gear_inventory)

        """
        sorted_gear_inventory = sorted(self.gear_inventory, key=lambda g: g.level, reverse=True)
        for gear in sorted_gear_inventory:
            for rarity in Gear_rarity:
                if rarity != Gear_rarity.COMMON:
                    success = gear.merge(rarity, self.gear_inventory)
                    """

        # Sort gear inventory by highest level and try to level up
        #Start for the lowest level gear to fast level ups
        sorted_gear_inventory = sorted(self.gear_inventory, key=lambda g: g.level, reverse=False)
        for gear in sorted_gear_inventory:
            gear.level_up(self)

        # Equip Gear
        for piece_type in Gear_pieces:
            if piece_type == Gear_pieces.DEFAULT:
                continue

            highest_level_gear = max(
                (gear for gear in self.gear_inventory if gear.piece == piece_type),
                key=lambda g: g.level
            )

            if highest_level_gear.level == 0:
                continue

            prev_equipped = self.equipped_gear.get(piece_type)
            if prev_equipped is None or highest_level_gear.level > prev_equipped.level:
                self.equipped_gear[piece_type] = highest_level_gear
                Logger.add_log(
                    Log_Action.EQUIP_GEAR,
                    self.time.get_timer_info(),
                    f"Equipped gear of {piece_type.value} with set {highest_level_gear.set.value} at level {highest_level_gear.level}",
                    {
                        "piece": piece_type.value,
                        "set": highest_level_gear.set.value,
                        "level": highest_level_gear.level
                    }
                )

        return
    
    def chapter_level_up(self):
        self.chapter_level += 1
        return


@dataclass
class Gacha_system:

    config_df: pd.DataFrame
    time: Timer

    @staticmethod
    def initialize(config_df: pd.DataFrame, time: Timer) -> 'Gacha_system':

        return Gacha_system(config_df = config_df, time=time)

    def open_chest(self, meta: Player_meta_progression, chest_name: str):


        row = self.config_df.loc[self.config_df['chest_name'] == chest_name].iloc[0]

        rarities: list[Gear_rarity] = []
        weights: list[float] = []

        for rarity in Gear_rarity:
            rarity_column = rarity.name.lower()
            if rarity_column in self.config_df.columns:
                raw_weight = row[rarity_column]

                if pd.isna(raw_weight) or raw_weight == "":
                    continue
                # Convert to float, allowing comma as decimal
                 #weight_f = float(str(raw_weight).replace(',', '.'))
                weight_f = float(raw_weight)

                if weight_f > 0:
                    rarities.append(rarity)
                    weights.append(weight_f)

        new_gear_rarity = random.choices(rarities, weights=weights, k=1)[0]
        new_gear_piece = random.choice([p for p in Gear_pieces if p != Gear_pieces.DEFAULT])
        new_gear_set = random.choice([s for s in Gear_sets if s != Gear_sets.DEFAULT])

        Logger.add_log(
            Log_Action.OPEN_GACHA,
            self.time.get_timer_info(),
            f"Opened {chest_name} chest and received gear piece {new_gear_piece.value}, set {new_gear_set.value}, rarity {new_gear_rarity}",
            {
                "chest_name": chest_name,
                "new_gear_piece": new_gear_piece.value,
                "new_gear_set": new_gear_set.value,
                "new_gear_rarity": str(new_gear_rarity)
            }
            )

        meta.add_gear(new_gear_piece, new_gear_set, new_gear_rarity)
        return


@dataclass
class Chapter:

    chapters_config: pd.DataFrame
    time: Timer

    @staticmethod
    def initialize(chapters_config: pd.DataFrame, time: Timer) -> 'Chapter':
        chapter = Chapter(
            chapters_config=chapters_config,
            time=time
        )
        return chapter

    def simulate(self, chapter_num: int, meta: Player_meta_progression, gacha_system: Gacha_system) -> bool:

        # Pass Time
        self.time.increment_play_chapter()

        chapter_config = self.chapters_config.loc[self.chapters_config[ConfigKeys.CHAPTER_NUM.value] == chapter_num]

        victory = False

        # Simulate the battle

        avg_gear_level_required = int(chapter_config[ConfigKeys.AVG_GEAR_LEVEL_REQUIRED.value].iloc[0])
        unique_gear_pieces_required = int(chapter_config[ConfigKeys.UNIQUE_GEAR_PIECES_REQUIRED.value].iloc[0])
        total_required_points = avg_gear_level_required * unique_gear_pieces_required

        total_player_points = 0

        for piece in meta.equipped_gear.values():
            if piece.level > 0:
                total_player_points += piece.level

        victory = total_player_points >= total_required_points

        # Give rewards based on result
        if(victory):
            victory = True
            win_reward_gold = chapter_config[ConfigKeys.WIN_REWARD_GOLD.value].iloc[0]
            win_reward_designs = chapter_config[ConfigKeys.WIN_REWARD_DESIGNS.value].iloc[0]
            win_reward_gacha = chapter_config[ConfigKeys.WIN_REWARD_GACHA.value].iloc[0]

            Logger.add_log(
                Log_Action.WIN_CHAPTER,
                self.time.get_timer_info(),
                f"Chapter {chapter_num} victory: awarded {win_reward_gold} gold, {win_reward_designs} designs, and opened {win_reward_gacha} chest",
                {
                    "chapter_num": chapter_num,
                    "victory": victory,
                    "player_points": total_player_points,
                    "required_points": total_required_points,
                    "gold_awarded": win_reward_gold,
                    "designs_awarded": win_reward_designs,
                    "gacha_chest_opened": win_reward_gacha
                }
            )

            meta.gold += win_reward_gold
            meta.add_designs(win_reward_designs)
            gacha_system.open_chest(meta, win_reward_gacha)     
            
        else:
            victory = False
            lose_reward_gold = chapter_config[ConfigKeys.LOSE_REWARD_GOLD.value].iloc[0]
            lose_reward_designs = chapter_config[ConfigKeys.LOSE_REWARD_DESIGNS.value].iloc[0]
            lose_reward_gacha = chapter_config[ConfigKeys.LOSE_REWARD_GACHA.value].iloc[0]

            Logger.add_log(
                Log_Action.LOSE_CHAPTER,
                self.time.get_timer_info(),
                f"Chapter {chapter_num} defeat: awarded {lose_reward_gold} gold, {lose_reward_designs} designs, and opened {lose_reward_gacha} chest",
                {
                    "chapter_num": chapter_num,
                    "victory": victory,
                    "player_points": total_player_points,
                    "required_points": total_required_points,
                    "gold_awarded": lose_reward_gold,
                    "designs_awarded": lose_reward_designs,
                    "gacha_chest_opened": lose_reward_gacha
                }
            )

            meta.gold += lose_reward_gold
            meta.add_designs(lose_reward_designs)
            gacha_system.open_chest(meta, lose_reward_gacha)

        return victory


def get_config_value(config_df, row: ConfigKeys, row_key: ConfigKeys, column_key: ConfigKeys) -> Any:
    return config_df.loc[config_df[row.value] == row_key.value, column_key.value].iloc[0]

def get_config_value_str_row(config_df, row: ConfigKeys, row_key: str, column_key: ConfigKeys) -> Any:
    return config_df.loc[config_df[row.value] == row_key, column_key.value].iloc[0]





@dataclass
class model:

    meta_progression: Player_meta_progression
    gacha_system: Gacha_system
    chapters: Chapter
    
    
    rounds_done: int
    max_allowed_rounds: int #value to block infinite loops in any while-true situation
    total_chapters: int
    timer: Timer

    current_day: int
    current_day_session: int
    current_session: int

    player_behavior: dict[str, int]

    main_config: Config

    @staticmethod
    def initialize(main_config: Config) -> 'model':
        
        rounds_done = 0
        max_allowed_rounds = 1000  #value to block infinite loops in any while-true situation
        total_chapters = main_config.get_total_chapters()

        gear_levels_config = main_config.gear_levels_df
        gear_merge_config = main_config.gear_merge_df
        chapters_config = main_config.chapters_df
        gacha_config = main_config.gacha_df
        offers_config = main_config.offers_df
        players_config = main_config.players_df


        #Player Behavior
        players_config[ConfigKeys.PLAYER_SIMULATE.value] = (players_config[ConfigKeys.PLAYER_SIMULATE.value].astype(str).str.upper().eq("TRUE")
)
        player_type = players_config.loc[players_config[ConfigKeys.PLAYER_SIMULATE.value] == True, ConfigKeys.PLAYER_TYPE.value].iloc[0]

        player_behavior = players_config.loc[players_config[ConfigKeys.PLAYER_TYPE.value] == player_type].to_dict(orient='records')[0]

        # Timer Section
        timer_instance = Timer.initialize(player_behavior)
        #free_rare_num = gacha_config.loc[gacha_config[ConfigKeys.CHEST_NAME.value] == ConfigKeys.RARE_CHEST_NAME.value,ConfigKeys.FREE_DAILY.value].iloc[0]
        #free_epic_num = gacha_config.loc[gacha_config[ConfigKeys.CHEST_NAME.value] == ConfigKeys.EPIC_CHEST_NAME.value,ConfigKeys.FREE_DAILY.value].iloc[0]
        #sessions_per_day = timer_config.loc[timer_config[ConfigKeys.TIMER_ACTION.value] == ConfigKeys.SESSIONS_PER_DAY.value,ConfigKeys.TIMER_AMOUNT.value].iloc[0]
        #avg_session_length = timer_config.loc[timer_config[ConfigKeys.TIMER_ACTION.value] == ConfigKeys.AVG_SESSION_LENGTH.value,ConfigKeys.TIMER_AMOUNT.value].iloc[0]
        current_day = timer_instance.current_day()
        current_day_session = 1 
        current_session = 1
        

        meta_progression = Player_meta_progression.initialize(gear_levels_config, gear_merge_config, timer_instance)
        gacha_system = Gacha_system.initialize(gacha_config, timer_instance)
        chapters = Chapter.initialize(chapters_config, timer_instance)

        

        return model(
            meta_progression=meta_progression,
            gacha_system=gacha_system,
            rounds_done=rounds_done,
            max_allowed_rounds=max_allowed_rounds,
            total_chapters=total_chapters,
            timer=timer_instance,
            chapters=chapters,
            current_day=current_day,
            player_behavior=player_behavior,
            current_day_session=current_day_session,
            current_session=current_session,
            main_config=main_config
            )
    
    def simulate(self):

        self.current_day = self.timer.current_day()
        self.current_day_session = 0
        self.current_session = 0

        # Give to the player enough gear to start
        for piece in Gear_pieces:
            if piece != Gear_pieces.DEFAULT:
                self.meta_progression.add_gear(piece, random.choice([s for s in Gear_sets if s != Gear_sets.DEFAULT]), Gear_rarity.COMMON)
                continue

        while(self.rounds_done<=self.max_allowed_rounds
              and self.meta_progression.chapter_level<=self.total_chapters):
            self.rounds_done+=1 # just for avoiding infinite loops
            self.current_day_session+= 1 # equivalent to rounds, every round is a session
            self.current_session += 1

            #fake progression for testing purposes
            #self.meta_progression.add_designs(1000)
        
            
            # Check current session time
            #if self.timer.current_session_time() >= self.player_behavior[ConfigKeys.PLAYER_AVG_SESSION_LENGTH.value]:
            #    self.timer.new_session()
            #    self.current_day_session += 1

            # Check max sessions per day
            if self.current_day_session > self.player_behavior[ConfigKeys.PLAYER_SESSIONS_PER_DAY.value]:
                self.timer.complete_day()
                self.timer.new_session()
                self.current_day_session = 1

            # Daily Gifts
            if self.timer.current_day() > self.current_day:
                self.current_day = self.timer.current_day()
                self.daily_free_gachas()

            # Purchase Offers
            offers_list = self.main_config.offers_df[ConfigKeys.OFFER_NAME.value].tolist()

            for offer in offers_list:
                if self.player_behavior[str(offer)] > 0:
                    self.meta_progression.apply_offer(str(offer), self.main_config.offers_df, self.gacha_system)
            

            # Meta Progression Simulation
            self.meta_progression.simulate()

            # Chapter Simulation
            chapter_level = self.meta_progression.chapter_level
            chapter_config = self.main_config.get_chapter_config(chapter_level)

            victory_bool = self.chapters.simulate(chapter_level, self.meta_progression, self.gacha_system)

            def _gear_level(piece: Gear_pieces) -> int:
                gear_obj = self.meta_progression.equipped_gear.get(piece)
                return gear_obj.level if gear_obj else 0

            def _gear_max_rarity(piece: Gear_pieces) -> str:
                gear_obj = self.meta_progression.equipped_gear.get(piece)
                return str(gear_obj.max_rarity) if gear_obj else str(Gear_rarity.COMMON)

            Logger.add_log(
                Log_Action.SESSION_END,
                self.timer.get_timer_info(),
                f"Chapter {chapter_level} simulation completed with {'victory' if victory_bool else 'defeat'}",
                {
                    "chapter_level": chapter_level,
                    "victory": victory_bool,
                    "current_day": self.current_day,
                    "current_day_session": self.current_day_session,
                    "current_session": self.current_session,
                    "current_coins": self.meta_progression.gold,
                    "designs": self.meta_progression.designs,
                    "weapon_gear_level": _gear_level(Gear_pieces.WEAPON),
                    "ring_gear_level": _gear_level(Gear_pieces.RING),
                    "gloves_gear_level": _gear_level(Gear_pieces.GLOVES),
                    "helmet_gear_level": _gear_level(Gear_pieces.HELMET),
                    "armor_gear_level": _gear_level(Gear_pieces.ARMOR),
                    "boots_gear_level": _gear_level(Gear_pieces.BOOTS),
                    "weapon_gear_rarity": _gear_max_rarity(Gear_pieces.WEAPON),
                    "ring_gear_rarity": _gear_max_rarity(Gear_pieces.RING),
                    "gloves_gear_rarity": _gear_max_rarity(Gear_pieces.GLOVES),
                    "helmet_gear_rarity": _gear_max_rarity(Gear_pieces.HELMET),
                    "armor_gear_rarity": _gear_max_rarity(Gear_pieces.ARMOR),
                    "boots_gear_rarity": _gear_max_rarity(Gear_pieces.BOOTS)
                }
            )

            # If victory, go to next chapter
            if victory_bool:
                if(self.meta_progression.chapter_level == self.total_chapters):
                    Logger.add_log(
                        Log_Action.SIMULATION_COMPLETED,
                        self.timer.get_timer_info(),
                        "Simulation completed: reached the last chapter",
                        {
                            "rounds_done": self.rounds_done,
                            "current_day": self.current_day,
                            "current_day_session": self.current_day_session,
                            "current_session": self.current_session,
                            "chapter_level": self.meta_progression.chapter_level
                        }
                    )
                    break
                self.meta_progression.chapter_level += 1

        return
    
    def daily_free_gachas(self) -> None:

        Logger.add_log(
            Log_Action.DAILY_FREE_GACHA,
            self.timer.get_timer_info(),
            f"Daily free gacha: {self.player_behavior[ConfigKeys.PLAYER_FREE_DAILY_RARE_CHEST.value]} rare and {self.player_behavior[ConfigKeys.PLAYER_FREE_DAILY_EPIC_CHEST.value]} epic",
            {
                "free_rare_num": self.player_behavior[ConfigKeys.PLAYER_FREE_DAILY_RARE_CHEST.value],
                "free_epic_num": self.player_behavior[ConfigKeys.PLAYER_FREE_DAILY_EPIC_CHEST.value]
            })

        for _ in range(self.player_behavior[ConfigKeys.PLAYER_FREE_DAILY_RARE_CHEST.value]):
            self.gacha_system.open_chest(self.meta_progression, ConfigKeys.RARE_CHEST_NAME.value)

        for _ in range(self.player_behavior[ConfigKeys.PLAYER_FREE_DAILY_EPIC_CHEST.value]):
            self.gacha_system.open_chest(self.meta_progression, ConfigKeys.EPIC_CHEST_NAME.value)
