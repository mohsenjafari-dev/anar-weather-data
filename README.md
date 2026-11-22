# Anar Pistachio Weather Data

An automated weather-data pipeline supporting agricultural research and pistachio farming in Anar, Kerman Province, Iran.

## Project Overview

This repository maintains a Python-based workflow for collecting and publishing hourly temperature data from the Copernicus ERA5-Land dataset.

The data supports downstream analysis of winter chill accumulation, an important factor in pistachio cultivation.

## Features

- Automated data updates using GitHub Actions.
- Hourly 2-meter air temperature data.
- Publicly accessible CSV output.
- A reproducible Python-based data retrieval workflow.
- Weather data for the Anar agricultural region.

## Repository Structure

- `.github/workflows/` — GitHub Actions automation.
- `tool/` — Python data processing scripts.
- `data/anar_latest.csv` — Published hourly weather data.

## Data Information

**Source:** Copernicus Climate Change Service (ERA5-Land)

**Geographic grid point:** 30.9° N, 55.3° E

**Temperature variable:** `t2m` (2-meter air temperature)

**Unit:** Kelvin

Temperature conversion:

`Celsius = Kelvin - 273.15`

ERA5-Land is a gridded reanalysis dataset, not a direct measurement from an orchard weather station. Data availability may lag behind the current date.

## Agricultural Applications

The hourly temperature records can support calculations of:

- Chilling Hours (CH)
- Chill Portions (CP)
- Seasonal winter temperature patterns

Chill calculations and cultivar-specific requirements are handled separately from this data repository.

## Data Source

[Copernicus Climate Data Store](https://cds.climate.copernicus.eu/datasets/reanalysis-era5-land-timeseries)

## Project Status

This repository is being actively developed as a small agricultural weather-data project. Its goal is to make weather data processing more accessible and reproducible for agricultural developers and researchers.
