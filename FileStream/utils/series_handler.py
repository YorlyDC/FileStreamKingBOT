import re
import json
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Tuple

@dataclass
class Episode:
    file_id: str
    name: str
    season: int
    episode: int
    size: int
    stream_link: str
    download_link: str

@dataclass
class Season:
    number: int
    episodes: List[Episode]

class SeriesHandler:
    def __init__(self):
        self.seasons: Dict[int, Season] = {}
        self.current_series: Optional[str] = None

    def start_series(self, series_title: str):
        """Initialize a new series"""
        self.current_series = series_title
        self.seasons.clear()

    def add_file(self, file_info: dict, stream_link: str, download_link: str) -> Tuple[int, int]:
        """Add a file to the series and return its season and episode numbers"""
        season_num, episode_num = self._parse_episode_info(file_info['file_name'])
        
        if season_num not in self.seasons:
            self.seasons[season_num] = Season(number=season_num, episodes=[])

        episode = Episode(
            file_id=file_info['file_id'],
            name=file_info['file_name'],
            season=season_num,
            episode=episode_num,
            size=file_info['file_size'],
            stream_link=stream_link,
            download_link=download_link
        )

        self.seasons[season_num].episodes.append(episode)
        self.seasons[season_num].episodes.sort(key=lambda x: x.episode)
        
        return season_num, episode_num

    def _parse_episode_info(self, filename: str) -> Tuple[int, int]:
        """Extract season and episode numbers from filename"""
        # Common patterns for episode naming
        patterns = [
            r'[Ss](\d{1,2})[Ee](\d{1,2})',  # S01E02
            r'(\d{1,2})x(\d{1,2})',         # 1x02
            r'[Tt]emporada[. _-]*(\d{1,2})[. _-]*[Ee]pisodio[. _-]*(\d{1,2})',  # Temporada 1 Episodio 2
            r'[Ss]eason[. _-]*(\d{1,2})[. _-]*[Ee]pisode[. _-]*(\d{1,2})'  # Season 1 Episode 2
        ]

        for pattern in patterns:
            match = re.search(pattern, filename)
            if match:
                return int(match.group(1)), int(match.group(2))

        # If no pattern matches, assume it's season 1
        # Try to find just an episode number
        ep_match = re.search(r'[Ee]pisodio[. _-]*(\d{1,2})|[Ee]p[. _-]*(\d{1,2})', filename)
        if ep_match:
            episode = int(ep_match.group(1) or ep_match.group(2))
            return 1, episode

        # If all else fails, return season 1, episode 1
        return 1, 1

    def export_to_json(self) -> str:
        """Export series information to JSON format"""
        series_data = {
            "title": self.current_series,
            "seasons": [
                {
                    "number": season.number,
                    "episodes": [asdict(ep) for ep in sorted(season.episodes, key=lambda x: x.episode)]
                }
                for season in sorted(self.seasons.values(), key=lambda x: x.number)
            ]
        }
        return json.dumps(series_data, indent=2, ensure_ascii=False)

    def export_to_txt(self) -> str:
        """Export series information to human-readable text format"""
        lines = [f"Serie: {self.current_series}\n"]
        
        for season in sorted(self.seasons.values(), key=lambda x: x.number):
            lines.append(f"\nTemporada {season.number}")
            lines.append("=" * 20)
            
            for episode in sorted(season.episodes, key=lambda x: x.episode):
                lines.append(f"\nEpisodio {episode.episode}: {episode.name}")
                lines.append(f"Stream: {episode.stream_link}")
                lines.append(f"Download: {episode.download_link}\n")
        
        return "\n".join(lines)

    def clear(self):
        """Clear current series data"""
        self.current_series = None
        self.seasons.clear() 