# Gipuzkoa Mobility: From Big Data to Multi-Agent Simulation

This repository contains a Data Engineering and Spatial Analysis pipeline designed to process massive mobility datasets from the Spanish Ministry of Transport (MITMA). The goal is to transform heavy, raw Origin-Destination (OD) matrices into actionable formats for interactive 3D visualizations (Kepler.gl / deck.gl) and Agent-Based Modeling (GAMA Platform).

The project focuses on the Gipuzkoa province (Basque Country), specifically analyzing rush-hour commuting and dynamic population flows.

##  Data Acquisition and Preprocessing

The simulation relies on several spatial and statistical data sources that required a rigorous processing pipeline. This workflow guarantees the fluidity, accuracy, and exactness of the regional traffic model.

### 1. Data Sources
Fusing heterogeneous data is at the core of this model. The following sources are used:
* **Mobility Flows (OD):** Origin-Destination traffic matrices come from the open data of **MITMA** (Ministerio de Transportes, Movilidad y Agenda Urbana). They are extracted from the section: *Estudios básicos > Pro-distritos > Viajes > Ficheros diarios*. Download here: https://www.transportes.gob.es/ministerio/proyectos-singulares/estudios-de-movilidad-con-big-data/opendata-movilidad
* **Administrative Zoning:** The Shapefile containing the polygons of the Gipuzkoa districts (`gipuzkoa_distritos.shp`) also comes from the **MITMA** zoning data. Download here: https://www.transportes.gob.es/ministerio/proyectos-singulares/estudios-de-movilidad-con-big-data/opendata-movilidad
* **Points of Interest (POI):** The spatial points used to refine movement targets within the districts were provided by the **City Science Lab**.
* **Road Network:** The raw geometric data for the roads comes from **OpenStreetMap (OSM)** (an extract downloaded in Shapefile format via Geofabrik for the Basque Country region). Download here: https://download.geofabrik.de/europe/spain/pais-vasco.html

### 2. Preprocessing Pipeline (Python Scripts)
To adapt these massive datasets to the constraints of a multi-agent simulation, a preparation pipeline was developed in Python (using libraries like GeoPandas). The data cleaning is performed in four steps via dedicated scripts:

* **`clean_day.py`**: Filters the massive MITMA files to isolate and extract only the trips corresponding to the specific day targeted by the simulation.
* **`cut_map.py`**: Performs spatial clipping. This script removes all peripheral geographic areas (Biscay, Alava, etc.) to crop and restrict the road network strictly to the borders of the Gipuzkoa districts.
* **`filter_road.py`**: Cleans the raw OpenStreetMap data by removing all paths inaccessible to motor vehicles (cycle paths, pedestrian footways, trails, stairs). This drastically lightens the spatial database.
* **`point_alignement.py`**: Corrects and aligns the coordinates of the Points of Interest (City Science Lab) to ensure they properly snap to the geometry of the regional map.

### 3. Pathfinding Resilience & Error Handling (GAMA Platform)
Collaborative OpenStreetMap data frequently contains topological flaws (invisible micro-cuts between two intersecting roads, unmapped dead ends) that inevitably cause agents to get stuck when calculating their routes ("disconnected graphs").
To ensure the continuity of the simulation despite an imperfect network, an algorithmic resilience logic was implemented directly into the behavior of the agents:
* **"Off-Road" Mode (Fallback):** When an agent detects that it is stuck in a graph dead end, it scans its environment to find the nearest connected road (within a 2 km radius) and flies there in a straight line to resume its navigation.
* **Final Approach:** If the agent gets stuck but is already close (less than 2 km) to its destination, the algorithm considers the road navigation complete and initiates an off-network final approach toward the target.
* **Garbage Collector:** An internal telemetry system monitors each agent. If a vehicle consecutively fails 10 times to advance on the network despite its repositioning attempts, it is automatically removed from the environment to preserve Random Access Memory (RAM) and prevent the creation of artificial traffic jams.

## Repository Structure & File Descriptions

### 1. Configuration & Version Control

* **`.gitignore`**
    * Ensures that massive data files (`.csv`, `.shp`, `.tar`) are excluded from version control to prevent repository bloat and Git timeout errors.

### 2. Generated Outputs (Locally)

*Note: Due to GitHub file size limits, the following generated files and raw inputs are not pushed to this repository.*

* `sim_trips_final.json`: The GeoJSON LineString dataset used to render animated "comet" trails in Kepler.gl/deck.gl.
* `population_dynamique_reelle.csv`: The temporal ledger used to animate district population changes.
* `road_pais_vasco_clean.shp`: The filtered and cropped OSM road network.

## How to Run Python Scripts Locally

1.  Clone this repository.
2.  Create an `includes/` and `road_gipuzkoa/` folder at the root.
3.  Place your MITMA open data CSVs and official Shapefiles in these folders.
4.  Install dependencies: `pip install pandas geopandas shapely pyproj`
5.  Execute the preprocessing and simulation scripts in numerical order.
6.  Import the resulting `.json` and `.csv` files into [Kepler.gl](https://kepler.gl/demo) to view the spatiotemporal animations.

## How to Run the GAMA Simulation (GUI Mode)

To run the agent-based simulation with full visual rendering on your local machine:

1. Open the **GAMA Platform** desktop application (version 2025.06 recommended).
2. Ensure your GAMA workspace is configured properly. Place all of the preprocessed datasets (OSM clean roads, POI CSV, MITMA flows, and District shapefiles) exactly in this directory path: 
    `GAMA_Workspace/Projet_Gipuzkoa/includes/`
3. Navigate to the `GAMA_Workspace/Projet_Gipuzkoa/models/` directory and open `visualisation_flux.gaml`.
4. Click the **Run** button (green play icon in the top toolbar) to instantiate the `RegionalTrafficAnalysis` experiment.
5. In the simulation parameters panel under *Traffic Settings*, adjust the **Flow Display Percentage (%)** slider (recommended values: `0.5%` to `5.0%` to optimize rendering performance on local hardware).
6. Click the **Play** button in the simulation control interface to start the visual execution.

## Tech Stack
* **Data Processing:** Python 3, Pandas (Chunking/Aggregations)
* **Geospatial Analysis:** GeoPandas, Shapely, PyProj
* **Agent-Based Modeling:** GAMA Platform (GAML)
* **Visualization:** Kepler.gl
