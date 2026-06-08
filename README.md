# YouTube Analytics Dashboard

This project provides a Python script to analyze video statistics for a given YouTube channel. It fetches data from the YouTube Data API, processes it, generates reports, and creates visualizations.

## Features
- Fetches video IDs using the uploads playlist.
- Retrieves video stats including views, publish date, and day of week.
- Calculates average views per video.
- Identifies best/worst performing videos by view count.
- Determines the day with the most views.
- Tracks growth rate over time.
- Generates a report in `report.txt`.
- Creates line chart for view growth over time (`view_growth_line.png`).
- Creates bar chart for total views per month (`monthly_views.png`).

## Requirements
1. Python 3.x
2. Google API Client Library for Python

## Setup Instructions

### Step 1: Install Dependencies
Install the required Python packages by running:
