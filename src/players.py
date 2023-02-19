import numpy as np
import pandas as pd
from pandas import DataFrame as PandasDataFrame
from typing import Dict, Any, Union


class Player:
    
    def __init__(self, player_name: str, player_stats: PandasDataFrame):
        
        self.player_name = player_name
        self.player_stats = player_stats
        
    def _peak_stretch_info(self, dur: int, stat) -> Dict[str, Any]:
        
        data = self.player_stats[["Season", stat]].sort_values(by="Season")
        stat_vals = data[stat].values
        season_vals = data["Season"].values
        
        windowed_stat_vals = np.convolve(stat_vals, np.ones(dur, dtype=int), "valid")
        windowed_max_loc = np.argmax(windowed_stat_vals)
        windowed_max_val = np.max(windowed_stat_vals)
        
        return {
            "stretch_duration": dur,
            "stretch_stat": stat,
            "stretch_value": windowed_max_val,
            "stretch_start_year": season_vals[windowed_max_loc],
            "stretch_end_year": season_vals[windowed_max_loc + dur - 1],
        }
    
    def peak_value(self, dur: int, stat: str = "WAR") -> Union[int, float]:
        return self._peak_stretch_info(dur, stat)["stretch_value"]
    
    def peak_start_year(self, dur: int, stat: str = "WAR") -> int:
        return self._peak_stretch_info(dur, stat)["stretch_start_year"]
    
    def peak_end_year(self, dur: int, stat: str = "WAR") -> int:
        return self._peak_stretch_info(dur, stat)["stretch_end_year"]
