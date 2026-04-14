model DonostiaTrafficSimulation

global {
    // --- 1. DATA SOURCES ---
    file shape_donostia <- file("../includes/donostia_distritos.shp");
    file shape_roads <- file("../includes/road_gipuzkoa/road_gipuzkoa.shp"); // GAMA will auto-filter this!
    file csv_points <- csv_file("../includes/points_prets.csv", true);
    
    // Highly optimized CSV for Donostia at 08:00 AM
    file csv_flows <- csv_file("../includes/Flux_08h_SanSebastian.csv", true);
    
    // Restrict the simulation world strictly to Donostia
    geometry shape <- envelope(shape_donostia);

    // --- 2. TEMPORAL CONFIGURATION (08:00 - 09:00) ---
    // Declaring the type 'date' and 'float' is mandatory here to avoid syntax errors.
    date starting_date <- date("2025-02-14 08:00:00");
    float step <- 10 #s; 
    
    graph road_network;
    int target_hour <- 8; 

    init {
        // --- STEP 1: DISTRICTS (Basemap) ---
        create district from: shape_donostia with: [zone_id::string(read("ID"))];
        
        // --- STEP 2: ROAD NETWORK ---
        create road from: shape_roads;
        road_network <- as_edge_graph(road);
        
        // --- STEP 3: ESTABLISHMENT HEATMAP ---
        matrix data_pts <- matrix(csv_points);
        loop i from: 0 to: data_pts.rows - 1 {
            create establishment {
                location <- {float(data_pts[0, i]), float(data_pts[1, i])};
            }
        }
        write "[*] Displaying " + length(establishment) + " points of interest (Heatmap active).";
        
        // --- STEP 4: TRAFFIC LOADING (Anti-Crash Logic) ---
        write "[*] Pre-calculating urban routes...";
        do initialize_traffic;
    }

    action initialize_traffic {
        matrix flow_data <- matrix(csv_flows);
        
        loop i from: 0 to: flow_data.rows - 1 {
            if (int(flow_data[1, i]) = target_hour) {
                
                string origin_id <- string(flow_data[2, i]);      
                string dest_id <- string(flow_data[3, i]);        
                int trip_count <- int(float(flow_data[4, i]));    
                string dep_time_str <- string(flow_data[7, i]);   
                
                list<string> t_parts <- split_with(dep_time_str, ":");
                date exact_departure <- date([2025, 2, 14, int(t_parts), int(t_parts), int(t_parts)]);
                
                district origin_zone <- district first_with (each.zone_id = origin_id);
                district dest_zone <- district first_with (each.zone_id = dest_id);
                
                // Safety check: Only create trips if both origin and destination are within Donostia
                if (origin_zone != nil and dest_zone != nil and trip_count > 0) {
                    
                    // --- OPTIMIZATION: SPATIAL PRE-CALCULATION ---
                    road start_road <- road closest_to (origin_zone.location);
                    road end_road <- road closest_to (dest_zone.location);
                    
                    if (start_road != nil and end_road != nil) {
                        point precalc_start <- any_location_in(start_road);
                        point precalc_end <- any_location_in(end_road);
                        
                        create trip_scheduler {
                            trips <- trip_count;
                            depart_at <- exact_departure;
                            start_node <- precalc_start; // Store exact location to save CPU later
                            target_node <- precalc_end;
                        }
                    }
                }
            }
        }
        write "[+] Traffic scheduled successfully: " + length(trip_scheduler) + " flows pre-calculated.";
    }

    // Auto-stop at 9:00 AM
    reflex stop_at_nine when: current_date.hour >= 9 {
        write "[+] 08:00 - 09:00 simulation window complete. Pausing execution.";
        do pause;
    }
}

// --- SPECIES ---

// 1. Invisible Scheduler
species trip_scheduler {
    int trips;
    date depart_at;
    point start_node;
    point target_node;

    reflex dispatch_agents when: current_date >= depart_at {
        // Spawn ratio: 1 agent per 10 real trips. Increase to trips/20 if it lags.
        create commuter number: max(1, trips / 5) {
            // Instant spawn using pre-calculated points (no heavy spatial queries here)
            location <- myself.start_node;
            target <- myself.target_node;
        }
        do die;
    }
}

// 2. Basemap / Districts
species district {
    string zone_id;
    aspect default {
        draw shape color: #lightgrey border: #grey;
    }
}

// 3. Road Network
species road {
    aspect default {
        // Using rgb() for dark grey instead of hex code
        draw shape color: rgb(50, 50, 50) width: 1.0;
    }
}

// 4. Points of Interest (Heatmap)
species establishment {
    aspect default {
        draw circle(120) color: rgb(220, 20, 60, 50); 
    }
}

// 5. Vehicles (Commuters)
species commuter skills: [moving] {
    point target;

    reflex move {
        // Urban speed limit set to 30 km/h
        do goto target: target speed: 30 #km/#h on: road_network;
        
        if (location distance_to target < 10 #m) {
            do die;
        }
    }

    aspect default {
        // Smaller glow for urban scale
        draw circle(80) color: rgb(0, 255, 255, 60); 
        // City-scale vehicle representation
        draw triangle(60) color: #cyan border: #white width: 1 rotate: heading + 90;
    }
}

// --- GUI / EXPERIMENT ---

experiment Urban_Traffic_Simulation type: gui {
    output {
        display Main_Map background: #white {
            // MODIFIED DISPLAY ORDER (from bottom/background to top/foreground)
            
            // 1. Districts (Bottom layer)
            species district aspect: default;
            
            // 2. Points of interest / Heatmap (Below the roads)
            species establishment aspect: default;
            
            // 3. Road network (On top of points of interest)
            species road aspect: default;
            
            // 4. Vehicles (Top layer, driving on the roads)
            species commuter aspect: default;
            
            graphics "Simulation_Clock" {
                string current_time_str <- string(current_date.hour) + ":" + 
                                           (current_date.minute < 10 ? "0" : "") + string(current_date.minute) + ":" + 
                                           (current_date.second < 10 ? "0" : "") + string(current_date.second);
                                           
                // Clock placed at top-left
                draw "Time: " + current_time_str at: {100, 100} color: #black font: font("SansSerif", 24, #bold);
            }
        }
    }
}