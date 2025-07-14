#!/usr/bin/env python3
"""
Immigration Draw Data Processor

This module processes immigration draw data to generate trend analyses for:
- CRS (Comprehensive Ranking System) trends
- Pool distribution trends across different CRS ranges
- Draw size and candidate volume trends over time

Author: Habibur Rahman
License: MIT
"""

import json
import sys
import os
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import re


class ImmigrationDataProcessor:
    """Main class for processing immigration draw data and generating trend analyses."""
    
    # Configuration constants
    BATCH_SIZE = 8
    CRS_POOL_RANGES = [
        "601-1200", "501-600", "451-500", "491-500", "481-490", "471-480",
        "461-470", "451-460", "401-450", "441-450", "431-440", "421-430",
        "411-420", "401-410", "351-400", "301-350", "0-300"
    ]
    
    def __init__(self, input_file: str, batch_size: Optional[int] = None, output_dir: Optional[Path] = None):
        """
        Initialize the processor with input file and optional batch size.
        
        Args:
            input_file: Path to the input JSON file
            batch_size: Optional batch size for processing (default: 8)
            output_dir: Path to save the processed files
        """
        self.input_file = Path(input_file)
        self.batch_size = batch_size or self.BATCH_SIZE
        self.output_dir = output_dir or Path("data")  # fallback to ./data

        self.OUTPUT_PATHS = {
            'crs_trend': self.output_dir / "processed_data_crs_trend.json",
            'pool_trend': self.output_dir / "processed_data_pool_trend.json",
            'draw_size': self.output_dir / "processed_data_draw_size.json"
        }

        self.logger = self._setup_logging()
        
        # Validate input file
        if not self.input_file.exists():
            raise FileNotFoundError(f"Input file not found: {input_file}")
        
        self.logger.info(f"Initialized processor with batch size: {self.batch_size}")
        self.logger.info(f"Input file: {self.input_file}")
    
    def _setup_logging(self) -> logging.Logger:
        """Set up logging configuration."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        return logging.getLogger(__name__)
    
    def _load_data(self) -> Dict[str, Any]:
        """
        Load and parse the JSON input file.
        
        Returns:
            Parsed JSON data
            
        Raises:
            json.JSONDecodeError: If the file is not valid JSON
            FileNotFoundError: If the input file doesn't exist
        """
        try:
            with open(self.input_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if 'rounds' not in data:
                raise ValueError("Input data must contain 'rounds' key")
            
            self.logger.info(f"Loaded {len(data['rounds'])} rounds from input file")
            return data
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON in input file: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Error loading data: {e}")
            raise
    
    def _extract_draw_name(self, draw_name: str) -> str:
        """
        Extract the main draw name by removing parenthetical information.
        
        Args:
            draw_name: Original draw name string
            
        Returns:
            Extracted draw name without parentheses
        """
        match = re.search(r'(.*)(?=\s\()', draw_name)
        return match.group(0) if match else draw_name
    
    def _parse_numeric_value(self, value: str) -> int:
        """
        Parse a numeric string value, removing commas.
        
        Args:
            value: String representation of a number (may contain commas)
            
        Returns:
            Parsed integer value
        """
        return int(value.replace(',', ''))
    
    def _sort_data_by_date(self, data: Dict[str, Dict]) -> None:
        """
        Sort data arrays by date in ascending order.
        
        Args:
            data: Dictionary containing data with x (dates) and y (values) arrays
        """
        for key in data:
            data_item = data[key]
            try:
                # Create sorted indices based on date
                sorted_indices = sorted(
                    range(len(data_item['x'])),
                    key=lambda i: datetime.strptime(data_item['x'][i], '%Y-%m-%d')
                )
                
                # Reorder x and y arrays based on sorted indices
                data_item['x'] = [data_item['x'][i] for i in sorted_indices]
                data_item['y'] = [data_item['y'][i] for i in sorted_indices]
                
            except ValueError as e:
                self.logger.warning(f"Date parsing error for key {key}: {e}")
    
    def _save_json_data(self, data: Any, output_path: str) -> None:
        """
        Save data to a JSON file, creating directories if necessary.
        
        Args:
            data: Data to save
            output_path: Path to the output file
        """
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Saved data to: {output_path}")
            
        except Exception as e:
            self.logger.error(f"Error saving data to {output_path}: {e}")
            raise
    
    def _process_crs_trends(self, rounds: List[Dict]) -> Dict[str, Dict]:
        """
        Process rounds data for CRS trend analysis.
        
        Args:
            rounds: List of round data dictionaries
            
        Returns:
            Dictionary containing CRS trend data organized by draw name
        """
        accumulated_data = {}
        
        # Process in batches
        for i in range(0, len(rounds), self.batch_size):
            batch = rounds[i:i + self.batch_size]
            if not batch:
                continue
                
            batch_data = {}
            
            for round_data in batch:
                try:
                    draw_name = round_data['drawName']
                    draw_date = round_data['drawDate']
                    draw_crs = round_data['drawCRS']
                    
                    # Extract draw name (remove parentheses part)
                    extracted_draw_name = self._extract_draw_name(draw_name)
                    
                    if extracted_draw_name not in batch_data:
                        batch_data[extracted_draw_name] = {
                            'x': [],
                            'y': [],
                            'type': 'scatter',
                            'mode': 'lines+markers',
                            'name': extracted_draw_name.title()
                        }
                    
                    batch_data[extracted_draw_name]['x'].append(draw_date)
                    batch_data[extracted_draw_name]['y'].append(
                        self._parse_numeric_value(draw_crs)
                    )
                    
                except (KeyError, ValueError) as e:
                    self.logger.warning(f"Error processing round data: {e}")
                    continue
            
            # Merge batch data into accumulated data
            for key, value in batch_data.items():
                if key in accumulated_data:
                    accumulated_data[key]['x'].extend(value['x'])
                    accumulated_data[key]['y'].extend(value['y'])
                else:
                    accumulated_data[key] = value
        
        # Sort data by date
        self._sort_data_by_date(accumulated_data)
        
        # Sort by key name
        return {key: accumulated_data[key] for key in sorted(accumulated_data.keys())}
    
    def _process_pool_trends(self, rounds: List[Dict]) -> Dict[str, Dict]:
        """
        Process rounds data for pool trend analysis.
        
        Args:
            rounds: List of round data dictionaries
            
        Returns:
            Dictionary containing pool trend data organized by CRS range
        """
        accumulated_data = {}
        
        # Process in batches
        for i in range(0, len(rounds), self.batch_size):
            batch = rounds[i:i + self.batch_size]
            if not batch:
                continue
                
            batch_data = {}
            
            for round_data in batch:
                try:
                    draw_date = round_data['drawDate']
                    
                    # Check if all pools are 0 (skip if so)
                    zero_count = sum(1 for i in range(1, 18) 
                                   if round_data.get(f'dd{i}', '0') == '0')
                    
                    if zero_count == 17:
                        continue
                    
                    # Process each pool
                    for i in range(1, 18):
                        pool_key = f'dd{i}'
                        if pool_key not in round_data:
                            continue
                            
                        draw_pool = round_data[pool_key].replace(',', '')
                        if not draw_pool or draw_pool == '0':
                            continue
                            
                        pool_name = f"CRS Range: {self.CRS_POOL_RANGES[i - 1]}"
                        
                        if pool_name not in batch_data:
                            batch_data[pool_name] = {
                                'x': [],
                                'y': [],
                                'type': 'scatter',
                                'mode': 'lines+markers',
                                'name': pool_name.title()
                            }
                        
                        batch_data[pool_name]['x'].append(draw_date)
                        batch_data[pool_name]['y'].append(int(draw_pool))
                        
                except (KeyError, ValueError, IndexError) as e:
                    self.logger.warning(f"Error processing pool data: {e}")
                    continue
            
            # Merge batch data into accumulated data
            for key, value in batch_data.items():
                if key in accumulated_data:
                    accumulated_data[key]['x'].extend(value['x'])
                    accumulated_data[key]['y'].extend(value['y'])
                else:
                    accumulated_data[key] = value
        
        # Sort data by date
        self._sort_data_by_date(accumulated_data)
        
        # Sort by key name
        return {key: accumulated_data[key] for key in sorted(accumulated_data.keys())}
    
    def _process_draw_size_trends(self, rounds: List[Dict]) -> List[Dict]:
        """
        Process rounds data for draw size and candidate volume trends.
        
        Args:
            rounds: List of round data dictionaries
            
        Returns:
            List containing draw invitations and total candidates trend data
        """
        draw_invitations_per_month = {}
        candidates_per_month = {}
        
        for round_data in rounds:
            try:
                draw_date = round_data['drawDate']
                # Extract year-month (YYYY-MM)
                year_month = '-'.join(draw_date.split('-')[:2])
                
                # Process draw invitations
                draw_size = self._parse_numeric_value(round_data['drawSize'])
                draw_invitations_per_month[year_month] = \
                    draw_invitations_per_month.get(year_month, 0) + draw_size
                
                # Process total candidates (dd18 field)
                total_candidates = self._parse_numeric_value(round_data['dd18'])
                if year_month not in candidates_per_month:
                    candidates_per_month[year_month] = []
                candidates_per_month[year_month].append(total_candidates)
                
            except (KeyError, ValueError) as e:
                self.logger.warning(f"Error processing draw size data: {e}")
                continue
        
        # Calculate mean candidates per month
        mean_candidates_per_month = {
            month: sum(candidates) / len(candidates) if candidates else 0
            for month, candidates in candidates_per_month.items()
        }
        
        # Remove months with zero candidates
        valid_months = {
            month: value for month, value in mean_candidates_per_month.items()
            if value > 0
        }
        
        # Filter invitations to match valid months
        filtered_invitations = {
            month: draw_invitations_per_month[month]
            for month in valid_months.keys()
            if month in draw_invitations_per_month
        }
        
        # Sort by month
        sorted_months = sorted(valid_months.keys())
        
        return [
            {
                'x': sorted_months,
                'y': [filtered_invitations[month] for month in sorted_months],
                'type': 'scatter',
                'mode': 'lines+markers',
                'name': 'Draw Invitations'
            },
            {
                'x': sorted_months,
                'y': [valid_months[month] for month in sorted_months],
                'type': 'scatter',
                'mode': 'lines+markers',
                'name': 'Total(Mean) Candidates'
            }
        ]
    
    def process_all_trends(self) -> None:
        """
        Process all trend analyses and save results to JSON files.
        
        This method orchestrates the entire processing pipeline:
        1. Load input data
        2. Process CRS trends
        3. Process pool trends
        4. Process draw size trends
        5. Save all results to respective output files
        """
        try:
            # Load data
            data = self._load_data()
            rounds = data['rounds']
            
            # Process CRS trends
            self.logger.info("Processing CRS trends...")
            crs_trends = self._process_crs_trends(rounds)
            self._save_json_data(crs_trends, self.OUTPUT_PATHS['crs_trend'])
            
            # Process pool trends
            self.logger.info("Processing pool trends...")
            pool_trends = self._process_pool_trends(rounds)
            self._save_json_data(pool_trends, self.OUTPUT_PATHS['pool_trend'])
            
            # Process draw size trends
            self.logger.info("Processing draw size trends...")
            draw_size_trends = self._process_draw_size_trends(rounds)
            self._save_json_data(draw_size_trends, self.OUTPUT_PATHS['draw_size'])
            
            self.logger.info("Processing completed successfully!")
            
        except Exception as e:
            self.logger.error(f"Error during processing: {e}")
            raise


def main():
    """
    Main entry point for the script.

    Usage:
        python immigration_processor.py <input_file> [batch_size] [output_dir]

    Examples:
        python immigration_processor.py data/rounds.json
        python immigration_processor.py data/rounds.json 10
        python immigration_processor.py data/rounds.json 10 public/data
    """
    if len(sys.argv) < 3:
        print("Usage: python immigration_processor.py <input_file> <output_dir> [batch_size]")
        sys.exit(1)

    input_file = sys.argv[1]
    output_dir = Path(sys.argv[2])
    batch_size = int(sys.argv[3]) if len(sys.argv) > 3 else None

    try:
        processor = ImmigrationDataProcessor(input_file, batch_size, output_dir)
        processor.process_all_trends()
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
    except ValueError as e:
        print(f"Error: Invalid data format - {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()