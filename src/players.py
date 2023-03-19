import numpy as np
import pandas as pd
from pandas import DataFrame as PandasDataFrame
from typing import Dict, Any, Union, Optional
import logging
import sys

logger = logging.getLogger(__name__)
logging.basicConfig(format='%(message)s', level=logging.INFO, stream=sys.stdout)


class Player:
    
    def __init__(self, player_name: str, player_stats: PandasDataFrame):
        """Base class describing any individual player, batter or pitcher

        Args:
            player_name: name of the player (first/last)
            player_stats: year-by-year player statistics from baseball reference
        """
        
        self.player_name = player_name
        self.player_stats = player_stats

        self._peak_info: Optional[Dict[str, Any]] = None
        
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
    
    def set_peak(self, dur: int, stat: str = "WAR") -> None:
        """Sets the definition of a player's peak, in terms of how many years and what stat to use

        Args:
            dur: length of peak, in years
            stat: statistic used to define the peak. Assumes that higher values are better. Defaults to "WAR".

        Returns:
            dict describing the peak
                stretch_duration: number of years of the peak
                stretch_stat: stat defining the peak
                stretch_value: summed value of the stat over the peak
                stretch_start_year: first year of the peak
                stretch_end_year: last year of the peak
        """

        self._peak_info = self._peak_stretch_info(dur, stat)

        return None
    
    def get_counting_stat(self, stat: str, start_year: int, end_year: int) -> Union[int, float]:
        """Gets total count of any counting stat over a fixed time period for the player

        Args:
            stat: name of the counting statistic
            start_year: first year of the time window
            end_year: last year of the time window

        Returns:
            Total count of the statisttic over the time window
        """

        range_stats = self.player_stats[[s >= start_year and s <= end_year for s in self.player_stats["Season"]]]
        return range_stats[stat].sum()
    
    def peak_value(self, dur: Optional[int] = None, stat: str = "WAR") -> Union[int, float]:
        """Peak value of a player in terms of the specified statistic over the specified time window

        Args:
            dur: Time window defining peak. Defaults to None.
            stat: Statistic defining peak. Defaults to "WAR".

        Returns:
            Aggregate value over the peak
        """
        if (self._peak_info is not None) and (dur is None):
            return self._peak_info["stretch_value"]
        return self._peak_stretch_info(dur, stat)["stretch_value"]
    
    def peak_start_year(self, dur: Optional[int] = None, stat: str = "WAR") -> int:
        """First year of the player's peak

        Args:
            dur: Time window defining the peak. Defaults to None.
            stat: Statistic defining the peak. Defaults to "WAR".

        Returns:
            First year of the peak
        """
        if (self._peak_info is not None) and (dur is None):
            return self._peak_info["stretch_start_year"]
        return self._peak_stretch_info(dur, stat)["stretch_start_year"]
    
    def peak_end_year(self, dur: Optional[int] = None, stat: str = "WAR") -> int:
        """Last year of the player's peak

        Args:
            dur: Time window defining the peak. Defaults to None.
            stat: Statistic defining the peak. Defaults to "WAR".

        Returns:
            Last year of the peak
        """
        if (self._peak_info is not None) and (dur is None):
            return self._peak_info["stretch_end_year"]
        return self._peak_stretch_info(dur, stat)["stretch_end_year"]


class PeakBatter(Player):

    def __init__(self, player_name: str, player_stats: PandasDataFrame, peak_dur: int = 5, peak_stat: str = "WAR"):
        
        super().__init__(player_name, player_stats)
        self.set_peak(peak_dur, peak_stat)

    @property
    def free_base_rate(self) -> float:
        bb = self.get_counting_stat("BB", self.peak_start_year(), self.peak_end_year())
        hbp = self.get_counting_stat("HBP", self.peak_start_year(), self.peak_end_year())
        ab = self.get_counting_stat("AB", self.peak_start_year(), self.peak_end_year())
        return (bb + hbp) / (max([ab, 1]))



class Pitcher(Player):

    def __init__(self, player_name: str, player_stats: PandasDataFrame):
        
        super().__init__(player_name, player_stats)
