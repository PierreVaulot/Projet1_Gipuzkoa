model GipuzkoaRegionalTraffic

global {
    // Data sources
    file shape_districts <- file("../includes/gipuzkoa_distritos.shp");
    file shape_roads <- file("../includes/road_pais_vasco_clean/road_pais_vasco_speedlimit.shp"); 
    file csv_traffic_flows <- csv_file("../includes/flux_gipuzkoa_final.csv", ",");
    file shape_buildings <- file("../includes/ERAIKINAK_EDIFICIOS/ERAIKINAK_EDIFICIOS_alignes.shp");

    geometry shape <- envelope(shape_districts);
    graph road_network;

    // Configuration parameters
    float display_percentage <- 75.0; 
    float total_distance_km <- 0.0; 

    init {
        // Temporal setup
        starting_date <- date("2025-02-14 08:00:00");
        step <- 5 #s; 
        
        // Spatial initialization
        write ">>> Initializing spatial environment...";
        create district from: shape_districts with: [zone_id::string(read("ID"))]; 
        map<string, district> district_index <- district as_map (each.zone_id::each);

        write ">>> Building regional road network...";
        create road from: shape_roads with: [speed_limit::float(read("maxspeed"))];
        road_network <- as_edge_graph(road, 1.0);

        write ">>> Loading buildings...";
        create building from: shape_buildings;

        write ">>> Assigning buildings to districts...";
        ask district {
            my_buildings <- building overlapping self;
        }

        // Traffic data ingestion
        write ">>> Loading traffic flow matrices...";
        matrix flow_data <- matrix(csv_traffic_flows);
        int total_records <- flow_data.rows - 1;

        loop i from: 1 to: total_records {
            int record_hour <- int(flow_data[1, i]);
            
            if (record_hour = 8) {
                string origin_id <- string(flow_data[2, i]);       
                string dest_id <- string(flow_data[3, i]);      
                int passenger_count <- int(float(flow_data[13, i])); 

                if (origin_id in district_index.keys and dest_id in district_index.keys) {
                    if (passenger_count > 0) {
                        create trip_scheduler {
                            total_passengers <- passenger_count;
                            int departure_delay <- rnd(3600);
                            depart_at <- starting_date + departure_delay; 
                            origin_zone <- district_index[origin_id];
                            dest_zone <- district_index[dest_id];
                        }
                    }
                }
            }
        }
        write ">>> System Ready.";
    }

    // Telemetry & logging
    reflex telemetry_logger when: current_date.second = 0 {
        string h <- string(current_date.hour);
        string m <- (current_date.minute < 10 ? "0" : "") + string(current_date.minute);
        write "[Sim Time: " + h + ":" + m + "] | [Compute: " + int(total_duration) + "s] | [Active Vehicles: " + length(commuter) + "]";
    }

    // Dynamic heatmap update based on traffic
    reflex update_road_network when: (cycle mod 2 = 0) {
        ask road { traffic <- 0; }
        
        ask commuter {
            road current_r <- road(current_edge);
            if (current_r = nil) { current_r <- road closest_to location; }
            if (current_r != nil) { current_r.traffic <- current_r.traffic + 1; }
        }
        
        ask road {
            if (traffic = 0) { road_color <- rgb(40, 40, 40); } 
            else if (traffic = 1) { road_color <- #yellow; } 
            else if (traffic = 2) { road_color <- #orange; } 
            else { road_color <- #red; }
        }
    }
}

// --- SPECIES DEFINITIONS ---

species trip_scheduler {
    int total_passengers;
    date depart_at;
    district origin_zone;
    district dest_zone;

    reflex dispatch_vehicles when: current_date >= depart_at {
        int vehicles_to_spawn <- round(total_passengers * (display_percentage / 100.0));
        
        if (vehicles_to_spawn > 0) {
            create commuter number: vehicles_to_spawn {
                building start_bldg <- (length(myself.origin_zone.my_buildings) > 0) ? one_of(myself.origin_zone.my_buildings) : nil;
                building end_bldg <- (length(myself.dest_zone.my_buildings) > 0) ? one_of(myself.dest_zone.my_buildings) : nil;

                location <- (start_bldg != nil) ? any_location_in(start_bldg) : any_location_in(myself.origin_zone);
                target <- (end_bldg != nil) ? any_location_in(end_bldg) : any_location_in(myself.dest_zone);
            }
        }
        do die; 
    }
}

species district {
    string zone_id;
    rgb color <- rgb(rnd(20, 70), rnd(20, 70), rnd(20, 70)); // Dark random color for background
    list<building> my_buildings;
    
    aspect default { 
        draw shape color: color border: #darkgray; 
    }
}

species building {
    aspect default {
        draw shape color: rgb(34, 34, 34) border: rgb(17, 17, 17); 
    }
}

species road {
    float speed_limit; 
    int traffic <- 0;
    rgb road_color <- rgb(40, 40, 40); 

    aspect default { 
        draw shape color: road_color width: (traffic = 0 ? 1.0 : (traffic <= 2 ? 2.5 : 4.0)); 
    }
}

species commuter skills: [moving] {
    point target;
    bool is_offroad <- false;
    bool is_final_approach <- false;
    point recovery_target <- nil;
    int stuck_count <- 0;
    
    reflex move {
        point old_position <- copy(location);
        float current_speed <- 50 #km/#h; 
        
        // Read speed limit from current road
        if (current_edge != nil) {
            road current_r <- road(current_edge);
            if (current_r != nil) {
                current_speed <- current_r.speed_limit #km/#h;
            }
        }
        
        // Movement logic and unblocking mechanism
        if (is_final_approach) {
            do goto target: target speed: 50 #km/#h;
        } 
        else if (is_offroad) {
            do goto target: recovery_target speed: 50 #km/#h;
            if (location distance_to recovery_target < 10 #m) {
                is_offroad <- false;
            }
        } 
        else {
            do goto target: target speed: current_speed on: road_network;
            
            if (location = old_position) {
                stuck_count <- stuck_count + 1;
                
                if (stuck_count >= 10) {
                    do die;
                    return;
                }
                
                if (location distance_to target < 2000 #m) {
                    is_final_approach <- true;
                } else {
                    is_offroad <- true;
                    road current_road <- road closest_to location;
                    list<road> nearby_roads <- (road at_distance 2000 #m) - current_road;
                    
                    if (length(nearby_roads) > 0) {
                        road new_road <- nearby_roads closest_to location;
                        recovery_target <- new_road.shape.points closest_to location;
                    } else {
                        is_final_approach <- true; 
                    }
                }
            } else {
                stuck_count <- 0;
            }
        }
        
        float dist_moved <- location distance_to old_position;
        if (dist_moved > 0) {
            total_distance_km <- total_distance_km + (dist_moved / 1000.0);
        }
        
        if (location distance_to target < 100 #m) { 
            do die; 
            return;
        }
    }
    
    aspect default {
        draw circle(100) at: {location.x, location.y, 10} color: #dodgerblue; 
    }
}

// --- EXPERIMENT / GUI ---

experiment RegionalTrafficAnalysis type: gui {
    
    parameter "Flow Display Percentage (%)" var: display_percentage min: 0.1 max: 100.0 step: 0.5 category: "Traffic Settings";

    output {
        display "Regional Map" type: opengl background: #black axes: false camera: "Vue_2D" refresh: every(2 #cycles) autosave: true {
            
            camera "Vue_2D" location: {world.shape.width / 2, world.shape.height / 2, world.shape.width} target: {world.shape.width / 2, world.shape.height / 2, 0};
            
            // Rendering order
            species district aspect: default refresh: false;
            species building aspect: default refresh: false; 
            species road aspect: default;
            species commuter aspect: default trace: 8 fading: true;
            
            // On-screen data metrics
            graphics "HUD" {
                string h <- string(current_date.hour);
                string m <- (current_date.minute < 10 ? "0" : "") + string(current_date.minute);
                string s <- (current_date.second < 10 ? "0" : "") + string(current_date.second);
                
                point time_pos <- {world.shape.width * 0.02, world.shape.height * 0.05};
                draw "Time : " + h + ":" + m + ":" + s at: time_pos color: #white font: font("SansSerif", 45, #bold);
                
                point count_pos <- {world.shape.width * 0.02, world.shape.height * 0.12};
                draw "Active Vehicles : " + length(commuter) at: count_pos color: #white font: font("SansSerif", 30, #bold);
                
                point dist_pos <- {world.shape.width * 0.02, world.shape.height * 0.18};
                draw "Total Distance : " + string(total_distance_km with_precision 1) + " km" at: dist_pos color: #white font: font("SansSerif", 30, #bold);
            }
        }
    }
}