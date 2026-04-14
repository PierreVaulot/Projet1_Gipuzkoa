model GipuzkoaRegionalTraffic

global {
    // --- 1. DATA SOURCES ---
    file shape_districts <- file("../includes/gipuzkoa_distritos.shp");
    file shape_roads <- file("../includes/road_gipuzkoa/road_gipuzkoa.shp"); 
    file csv_traffic_flows <- csv_file("../includes/flux_gipuzkoa_final.csv", ",");

    // Set environment bounds based on the regional shapefile
    geometry shape <- envelope(shape_districts);
    graph road_network;

    // --- 2. CONFIGURATION PARAMETERS ---
    // Determines the percentage of trips to visualize to maintain CPU performance
    float display_percentage <- 5.0; 

    init {
        // --- 3. TEMPORAL SETUP ---
        starting_date <- date("2025-02-14 08:00:00");
        step <- 5 #s; 
        
        // --- 4. SPATIAL INITIALIZATION ---
        write ">>> Initializing spatial environment...";
        create district from: shape_districts with: [zone_id::string(read("ID"))]; 
        
        // Build spatial index for O(1) origin-destination lookups
        map<string, district> district_index <- district as_map (each.zone_id::each);

        write ">>> Building regional road network...";
        create road from: shape_roads;
        road_network <- as_edge_graph(road);

        // --- 5. TRAFFIC DATA INGESTION ---
        write ">>> Loading traffic flow matrices...";
        matrix flow_data <- matrix(csv_traffic_flows);
        int total_records <- flow_data.rows - 1;
        
        write "Total OD pairs to process: " + total_records;

        loop i from: 1 to: total_records {
            // Filter for 08:00 AM window
            if (int(flow_data[1, i]) = 8) {
                string origin_id <- string(flow_data[2, i]);       
                string dest_id <- string(flow_data[3, i]);      
                int passenger_count <- int(float(flow_data[13, i])); 

                // Validate geometries before scheduling
                if (origin_id in district_index.keys and dest_id in district_index.keys) {
                    if (passenger_count > 0) {
                        create trip_scheduler {
                            total_passengers <- passenger_count;
                            
                            // Distribute departures uniformly across the 1-hour window (3600s)
                            int departure_delay <- rnd(3600);
                            depart_at <- starting_date + departure_delay; 
                            
                            origin_zone <- district_index[origin_id];
                            dest_zone <- district_index[dest_id];
                        }
                    }
                }
            }
        }
        write ">>> System Ready: " + length(trip_scheduler) + " flow operations scheduled.";
        write "----------------------------------------------------";
    }

    // --- 6. TELEMETRY & LOGGING ---
    // Outputs simulation metrics to the console every simulated minute
    reflex telemetry_logger when: current_date.second = 0 {
        string h <- string(current_date.hour);
        string m <- (current_date.minute < 10 ? "0" : "") + string(current_date.minute);
        int compute_time <- int(total_duration);
        
        write "[Sim Time: " + h + ":" + m + "] | [Compute: " + compute_time + "s] | [Active Vehicles: " + length(commuter) + "]";
    }
}

// --- SPECIES DEFINITIONS ---

// Invisible agent responsible for releasing traffic at the correct timestamp
species trip_scheduler {
    int total_passengers;
    date depart_at;
    district origin_zone;
    district dest_zone;

    reflex dispatch_vehicles when: current_date >= depart_at {
        // Apply rendering threshold based on UI parameter
        int vehicles_to_spawn <- round(total_passengers * (display_percentage / 100.0));
        
        if (vehicles_to_spawn > 0) {
            create commuter number: vehicles_to_spawn {
                location <- any_location_in(myself.origin_zone);
                target <- any_location_in(myself.dest_zone);
            }
        }
        do die; // Free memory after dispatch
    }
}

species district {
    string zone_id;
    aspect default { 
        draw shape color: rgb(240, 240, 240) border: #silver; 
    }
}

species road {
    aspect default { 
        draw shape color: rgb(110, 110, 110) width: 1.0; 
    }
}

species commuter skills: [moving] {
    point target;
    
    reflex move {
        // Regional highway speed assumption (80 km/h)
        do goto target: target speed: 80 #km/#h on: road_network;
        
        // Arrival threshold (50m) to clear intersections efficiently
        if (location distance_to target < 50 #m) { 
            do die; 
        }
    }
    
    aspect default {
        // High-visibility rendering for regional scale viewing
        draw circle(300) color: rgb(255, 0, 0, 40); 
        draw triangle(400) color: #red border: #white width: 2 rotate: heading + 90;
    }
}

// --- EXPERIMENT / GUI ---

experiment RegionalTrafficAnalysis type: gui {
    
    // UI Parameter to adjust rendering load on-the-fly
    parameter "Flow Display Percentage (%)" var: display_percentage min: 0.1 max: 100.0 step: 0.5 category: "Traffic Settings";

    output {
        display "Regional Map" type: java2D background: #white {
            // Layer rendering order: Bottom to Top
            species district aspect: default;
            species road aspect: default;
            species commuter aspect: default;
        }
    }
}