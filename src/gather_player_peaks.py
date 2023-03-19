#!/usr/bin/env python3

# Gathers player peak data from baseball reference and stores locally
# Generates two TSV files, one for batters and one for pitchers
# Output file format:
#   1 row per player
#   columns:
#       player_name: name of player
#       peak_value: aggregate WAR over the years of the peak
#       peak_start_year: first year of the player's peak
#       peak_end_year: last year of the player's peak
# Template usage:
# > python gather_player_peaks <start year> <end year> --peak-duration <number years defining peak> --storage-path <local path to store peak files> --batter-file <name of batters peak file> --pitcher-file <name of pitcher file>
# Example usage:
# > python gather_player_peaks 1990 2020 --peak-duration 5 --storage-path ./data/ --batter-file batter_peaks.tsv --pitcher-file pitcher_peaks.tsv

import logging
import argparse
import sys

from players import Player
import pandas as pd
from pandas import DataFrame as PandasDataFrame
from typing import Any
import pybaseball as bb

logger = logging.getLogger(__name__)
logging.basicConfig(format='%(message)s', level=logging.INFO, stream=sys.stdout)


def parse_arguments() -> Any:
    """Argument parsing

    Returns:
        Arguments object
    """

    parser = argparse.ArgumentParser()

    parser.add_argument(dest="start_year", type=int, help="initial season in span to search player peaks")
    parser.add_argument(dest="end_year", type=int, help="final season in span to search for player peaks")
    parser.add_argument("--peak-duration", dest="peak_duration", type=int, default=5, help="years defining a 'peak'")
    parser.add_argument("--storage-path", dest="storage_path", type=str, default="../data/", help="directory to store the peaks data")
    parser.add_argument("--batter-file", dest="batter_file", type=str, default="batter_peaks.tsv", help="filename for batters peak data")
    parser.add_argument("--pitcher-file", dest="pitcher_file", type=str, default="pitcher_peaks.tsv", help="filename for pitcher peak data")

    args = parser.parse_args()
    
    return args


def _load_pitching_stats(start_year: int, end_year: int) -> PandasDataFrame:
    """Loads per-player pitching stats by year from baseball reference

    Args:
        start_year: first year to load from
        end_year: last year to load from

    Returns:
        Dataframe with a row per player-year and all pitching stats from baseball reference
    """
    
    stats_by_year = []
    for year in range(start_year, end_year + 1):
        logger.info(f"loading pitcher stats for {year}")
        stats = bb.pitching_stats(year, qual=1)
        stats_by_year.append(stats)
    stats = pd.concat(stats_by_year).reset_index(drop=True)

    return stats


def _load_batting_stats(start_year: int, end_year:int) -> PandasDataFrame:
    """Loads per-player batting stats by year from baseball reference

    Args:
        start_year: first year to load from
        end_year: last year to load from

    Returns:
        Dataframe with a row per player-year and all batting stats from baseball reference
    """

    stats_by_year = []
    for year in range(start_year, end_year + 1):
        logger.info(f"loading batting stats for {year}")
        stats = bb.batting_stats(year, qual=1)
        stats_by_year.append(stats)
    stats = pd.concat(stats_by_year).reset_index(drop=True)

    return stats


def load_player_peaks(
    start_year: int,
    end_year: int,
    dur: int,
    category: str,
) -> PandasDataFrame:
    """Loads and calculates peak values for all players over a specified time window.

    Args:
        start_year: first year to load
        end_year: last year to load
        dur: duration that defines a peak
        category: batters or pitchers

    Returns:
        Row per player, describing their peak
    """

    assert category in {"batters", "pitchers"}, \
        f"category must be one of 'batters' or 'pitchers', received {category}"

    # load stats over the defined time interval
    logger.info(f"loading statistics for {category} from {start_year} to {end_year}")
    if category == "pitchers":
        stats = _load_pitching_stats(start_year, end_year)
    else:
        stats = _load_batting_stats(start_year, end_year)
        
    
    # get the set of players with careers long enough to have a peak of the specified duration
    career_durations = stats["Name"].value_counts().reset_index().rename(columns={"index": "Name", "Name": "Seasons"})
    candidates = sorted(list(set(career_durations[career_durations["Seasons"] >= dur]["Name"].values)))
    logger.info(f"# candidate {category}: {len(candidates)}")

    # get stats for each candidate player
    players = []
    for player in candidates:
        player_stats = stats[stats["Name"] == player].sort_values(by="Season", ascending=True).reset_index(drop=True)
        players.append(Player(player, player_stats))

    # get the stat value for the players peak, and the peak years
    rows = []
    for player in players:
        row = {
            "player_name": player.player_name,
            "peak_value": player.peak_value(dur, stat="WAR"),
            "peak_start_year": player.peak_start_year(dur, stat="WAR"),
            "peak_end_year": player.peak_end_year(dur, stat="WAR"),
        }
        rows.append(row)

    return pd.DataFrame(rows)


def main():

    # handle input arguments
    args = parse_arguments()
    start_year = args.start_year
    end_year = args.end_year
    peak_duration = args.peak_duration
    storage_path = args.storage_path
    if not storage_path.endswith("/"):
        storage_path += "/"
    batter_file = args.batter_file
    pitcher_file = args.pitcher_file

    logger.info(f"start year: {start_year}")
    logger.info(f"end year: {end_year}")
    logger.info(f"peak duration: {peak_duration}")
    logger.info(f"storage location: {storage_path}")
    logger.info(f"batter filename: {batter_file}")
    logger.info(f"pitcher filename: {pitcher_file}")
    
    # generate peaks info for batters
    logger.info(f"genarating batter peaks")
    batter_peaks = load_player_peaks(start_year, end_year, peak_duration, "batters")
    logger.info(f"writing {batter_peaks.shape[0]} records to {storage_path + batter_file}")
    batter_peaks.to_csv(storage_path + batter_file, sep="\t", index=False)

    # generate peaks info for pitchers
    logger.info(f"genarating pitcher peaks")
    pitcher_peaks = load_player_peaks(start_year, end_year, peak_duration, "pitchers")
    logger.info(f"writing {pitcher_peaks.shape[0]} records to {storage_path + pitcher_file}")
    pitcher_peaks.to_csv(storage_path + pitcher_file, sep="\t", index=False)

    return None    


if __name__ == "__main__":
    main()