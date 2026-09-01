model project_bubble

global {
    // --- 1. DATA SOURCES ---
    file shape_districts <- file("../includes/gipuzkoa_distritos.shp");
    file csv_traffic_flows <- csv_file("../includes/flux_gipuzkoa_final.csv", ",");
    
    // --- 2. ABSTRACT SPACE CONFIGURATION ---
    geometry shape <- square(10000); 
    point center_pt <- {5000, 5000};
    float circle_radius <- 4000.0;
    
    float display_percentage <- 1.0; 
    int total_particles <- 1000; 
    
    // Variable pour l'affichage du pourcentage en transit
    float transit_pct <- 0.0;

    init {
        starting_date <- date("2025-02-14 08:00:00");
        step <- 5 #s; 
        
        write ">>> Initializing Districts...";
        create district from: shape_districts with: [zone_id::string(read("ID"))]; 
        
        // --- FUSION AVEC LE DICTIONNAIRE DES COMARQUES INTÉGRÉ ---
        write ">>> Merging Comarca mapping...";
        map<string, string> dict_comarcas <- [
            "20005_AM"::"Tolosaldea", "20009"::"Buruntzaldea", "20010_AM"::"Tolosaldea", 
            "20013"::"Debagoiena", "20016_AM"::"Tolosaldea", "2001701"::"Urola Erdia", 
            "2001702"::"Urola Erdia", "2001703"::"Urola Erdia", "20018"::"Urola Erdia", 
            "20019"::"Goierri", "20022_AM"::"Debagoiena", "20025_AM"::"Goierri", 
            "20027_AM"::"Urola Kosta", "20028_AM"::"Tolosaldea", "20029"::"Debabarrena", 
            "2003001"::"Debabarrena", "2003002"::"Debabarrena", "2003003"::"Debabarrena", 
            "2003004"::"Debabarrena", "2003005"::"Debabarrena", "20032"::"Debabarrena", 
            "20034_AM"::"Debagoiena", "20036"::"Bidasoaldea", "20039"::"Urola Kosta", 
            "20040"::"Buruntzaldea", "20042"::"Tolosaldea", "20043_AM"::"Goierri", 
            "2004501"::"Bidasoaldea", "2004502"::"Bidasoaldea", "2004503"::"Bidasoaldea", 
            "2004504"::"Bidasoaldea", "20049"::"Goierri", "20051"::"Urola Garaia", 
            "20052_AM"::"Goierri", "20053"::"Oarsoaldea", "20055"::"Debagoiena", 
            "20056_AM"::"Debabarrena", "20059"::"Debagoiena", "20061"::"Urola Kosta", 
            "20063"::"Oarsoaldea", "20064"::"Oarsoaldea", "20065_AM"::"Debabarrena", 
            "20067"::"Oarsoaldea", "2006901"::"Donostialdea", "2006902"::"Donostialdea", 
            "2006903"::"Donostialdea", "2006904"::"Donostialdea", "2006905"::"Donostialdea", 
            "2006906"::"Donostialdea", "2006907"::"Donostialdea", "2007101"::"Tolosaldea", 
            "2007102"::"Tolosaldea", "2007103"::"Tolosaldea", "2007104"::"Tolosaldea", 
            "20072"::"Buruntzaldea", "20073"::"Buruntzaldea", "2007401"::"Debagoiena", 
            "2007402"::"Debagoiena", "2007403"::"Debagoiena", "20075"::"Tolosaldea", 
            "20076"::"Goierri", "20077_AM"::"Urola Garaia", "2007901"::"Urola Kosta", 
            "2007902"::"Urola Kosta", "20080"::"Urola Garaia", "20081"::"Urola Kosta", 
            "20902"::"Buruntzaldea", "20903"::"Buruntzaldea"
        ];
        
        ask district {
            if (zone_id in dict_comarcas.keys) {
                comarca_name <- dict_comarcas[zone_id];
            } else {
                comarca_name <- "Inconnu";
            }
        }
        
        // --- CRÉATION DES COMARQUES VISUELLES ---
        write ">>> Aggregating visually by Comarca...";
        list<string> unique_comarcas <- remove_duplicates(district where (each.comarca_name != "Inconnu" and each.comarca_name != "") collect each.comarca_name);
        
        loop c_name over: unique_comarcas {
            create comarca {
                comarca_id <- c_name;
            }
        }
        
        int num_comarcas <- length(comarca);
        float comarca_angle_step <- 360.0 / num_comarcas;
        int c_idx <- 0;
        
        ask comarca {
            list<district> my_districts <- district where (each.comarca_name = comarca_id);
            real_location <- length(my_districts) > 0 ? mean(my_districts collect each.location) : location;
            
            location <- {center_pt.x + circle_radius * cos(c_idx * comarca_angle_step), 
                         center_pt.y + circle_radius * sin(c_idx * comarca_angle_step)};
            my_color <- rnd_color(200); 
            c_idx <- c_idx + 1;
        }
        
        ask district {
            if (comarca_name != "Inconnu" and comarca_name != "") {
                my_comarca <- comarca first_with (each.comarca_id = comarca_name);
            }
        }
        
        map<string, district> district_index <- district as_map (each.zone_id::each);

        // --- CALCUL DU POIDS DE POPULATION (Agrégé par Comarque) ---
        write ">>> Analyzing CSV to estimate population distribution for 8h-10h...";
        matrix flow_data <- matrix(csv_traffic_flows);
        int total_records <- flow_data.rows - 1;
        float total_pop_flux <- 0.0;
        
        loop i from: 1 to: total_records {
            int record_hour <- int(flow_data[1, i]);
            string origin_id <- string(flow_data[2, i]);
            int p_count <- int(float(flow_data[13, i]));
            
            if ((record_hour = 8 or record_hour = 9) and origin_id in district_index.keys and p_count > 0) {
                if (district_index[origin_id].my_comarca != nil) {
                    comarca c <- district_index[origin_id].my_comarca;
                    c.pop_weight <- c.pop_weight + p_count;
                    total_pop_flux <- total_pop_flux + p_count;
                }
            }
        }

        // --- CRÉATION DES PARTICULES PROPORTIONNELLE DANS LES COMARQUES ---
        ask comarca {
            int my_particles <- (total_pop_flux > 0) ? round(total_particles * (pop_weight / total_pop_flux)) : (total_particles / num_comarcas);
            create commuter number: my_particles {
                current_z <- myself;
                location <- myself.location + {rnd(-150, 150), rnd(-150, 150)};
                current_color <- myself.my_color;
                state <- 2; 
            }
        }

        write ">>> Scheduling 8h-10h inter-comarca trips...";
        loop i from: 1 to: total_records {
            int record_hour <- int(flow_data[1, i]);
            string origin_id <- string(flow_data[2, i]);       
            string dest_id <- string(flow_data[3, i]);      
            int passenger_count <- int(float(flow_data[13, i])); 

            if ((record_hour = 8 or record_hour = 9) and origin_id in district_index.keys and dest_id in district_index.keys and passenger_count > 0) {
                
                comarca o_comarca <- district_index[origin_id].my_comarca;
                comarca d_comarca <- district_index[dest_id].my_comarca;
                
                if (o_comarca != nil and d_comarca != nil and o_comarca != d_comarca) {
                    create trip_scheduler {
                        total_passengers <- passenger_count;
                        depart_at <- starting_date + ((record_hour - 8) * 3600) + rnd(3599); 
                        origin_zone <- o_comarca;
                        dest_zone <- d_comarca;
                    }
                }
            }
        }
    }

    // Calcul global du pourcentage de particules en transit
    reflex update_transit_pct {
        int transit_count <- commuter count (each.state != 2);
        transit_pct <- length(commuter) > 0 ? (transit_count / length(commuter)) * 100.0 : 0.0;
    }

    reflex stop_at_10am when: current_date >= date("2025-02-14 10:00:00") {
        write ">>> 10:00 AM reached. Simulation ended.";
        do pause;
    }
}

// --- SPECIES DEFINITIONS ---

species district {
    string zone_id;
    string comarca_name;
    comarca my_comarca <- nil;
}

species comarca {
    string comarca_id;
    rgb my_color;
    float pop_weight <- 0.0;
    point real_location; 
    
    // Variable pourcentage local
    float current_pct <- 0.0;
    
    reflex update_pct {
        int my_count <- commuter count (each.state = 2 and each.current_z = self);
        current_pct <- length(commuter) > 0 ? (my_count / length(commuter)) * 100.0 : 0.0;
    }
    
    // Le cercle reste statique
    aspect base { 
        draw circle(150) color: my_color border: #darkgray width: 2.0; 
    }
    
    // Les textes s'actualisent et s'affichent par-dessus les particules (Z=15)
    aspect labels {
        // Le nom de la comarque en dessous du cercle
        draw comarca_id at: location + {0, 220, 15} anchor: #center color: #gray font: font("Helvetica", 18, #bold);
        // Le pourcentage très nettement en dessous du nom
        draw string(current_pct with_precision 1) + "%" at: location + {0, 450, 15} anchor: #center color: rgb(100,100,100) font: font("Helvetica", 16, #bold);
    }
}

species trip_scheduler {
    int total_passengers;
    date depart_at;
    comarca origin_zone;
    comarca dest_zone;

    reflex dispatch_vehicles when: current_date >= depart_at {
        float expected_vehicles <- total_passengers * (display_percentage / 100.0);
        int vehicles_to_move <- int(expected_vehicles);
        
        comarca my_oz <- origin_zone;
        comarca my_dz <- dest_zone;
        
        float real_dist_meters <- my_oz.real_location distance_to my_dz.real_location;
        float avg_road_speed_mps <- 60.0 #km/#h; 
        float travel_time_seconds <- real_dist_meters / avg_road_speed_mps;
        date target_arrival <- depart_at + travel_time_seconds;
        
        if (flip(expected_vehicles - vehicles_to_move)) {
            vehicles_to_move <- vehicles_to_move + 1;
        }
        
        if (vehicles_to_move > 0) {
            list<commuter> available <- commuter where (each.state = 2 and each.current_z = my_oz);
            int count <- min([vehicles_to_move, length(available)]);
            
            if (count > 0) {
                ask count among available {
                    dest_z <- my_dz;
                    target_pt <- center_pt + {rnd(-200, 200), rnd(-200, 200)}; 
                    state <- 0; 
                    my_speed <- 40.0; 
                    arrival_due <- target_arrival; 
                    current_color <- rgb(160, 160, 160); 
                }
            }
            
            if (count < vehicles_to_move) {
                int missing <- vehicles_to_move - count;
                list<commuter> other_available <- commuter where (each.state = 2 and each.current_z != my_oz);
                
                if (length(other_available) > 0) {
                    int to_take <- min([missing, length(other_available)]);
                    ask to_take among other_available {
                        location <- my_oz.location + {rnd(-100, 100), rnd(-100, 100)};
                        current_z <- my_oz;
                        dest_z <- my_dz;
                        target_pt <- center_pt + {rnd(-200, 200), rnd(-200, 200)};
                        state <- 0;
                        my_speed <- 40.0;
                        arrival_due <- target_arrival;
                        current_color <- rgb(160, 160, 160);
                    }
                }
            }
        }
        do die; 
    }
}

species commuter skills: [moving] {
    comarca current_z;
    comarca dest_z;
    point target_pt <- nil;
    rgb current_color;
    float my_speed <- 40.0;
    date arrival_due;
    
    int state <- 2; 
    
    // --- 1. MOUVEMENT ---
    reflex move {
        if (state = 2) {
            float dist_to_home <- location distance_to current_z.location;
            if (dist_to_home > 0) {
                location <- location + ((current_z.location - location) / dist_to_home) * (dist_to_home * 0.01);
            }
            do wander amplitude: 30.0 speed: 1.0; 
        } 
        else if (state = 0) { 
            do goto target: target_pt speed: my_speed; 
            if (location distance_to target_pt < 60) {
                state <- 1; 
                current_color <- rgb(160, 160, 160); 
            }
        } 
        else if (state = 1) { 
            float dist_to_hub <- location distance_to center_pt;
            if (dist_to_hub > 0) {
                location <- location + ((center_pt - location) / dist_to_hub) * (dist_to_hub * 0.01);
            }
            do wander amplitude: 30.0 speed: 1.0;
            
            float dist_to_dest <- location distance_to dest_z.location;
            float time_to_reach <- dist_to_dest / my_speed;
            
            if (current_date + time_to_reach >= arrival_due) {
                state <- 3; 
                target_pt <- dest_z.location + {rnd(-100, 100), rnd(-100, 100)}; 
                current_color <- dest_z.my_color; 
            }
        }
        else if (state = 3) { 
            do goto target: target_pt speed: my_speed; 
            if (location distance_to target_pt < 60) {
                state <- 2; 
                current_z <- dest_z;
                target_pt <- nil;
            }
        }
    }

    // --- 2. RÉPULSION ORGANIQUE ---
    reflex separation {
        list<commuter> neighbors <- commuter at_distance 100;
        if (length(neighbors) > 0) {
            point push_force <- {0, 0};
            ask neighbors {
                float dist <- myself.location distance_to location;
                if (dist > 0) {
                    push_force <- push_force + ((myself.location - location) / dist) * (100 - dist) * 0.3;
                }
            }
            location <- location + push_force;
        }
    }
    
    aspect default {
        draw circle(45) at: {location.x, location.y, 5} color: current_color; 
    }
}

// --- EXPERIMENT / GUI ---

experiment VideoPresentation type: gui {
    
    output {
        display "Abstract Particle Flow" type: opengl background: #white axes: false refresh: every(1 #cycles) autosave: true {
            
            // COUCHE 1 : Les cercles de base (figés pour la performance)
            graphics "Transit Zone Base" refresh: false {
                draw circle(800) at: center_pt color: #transparent border: rgb(180,180,180) width: 2;
            }
            species comarca aspect: base refresh: false;
            
            // COUCHE 2 : Les particules dynamiques (Z=5)
            species commuter aspect: default;
            
            // COUCHE 3 : Les labels (Noms + Pourcentages) dessinés TOUT AU-DESSUS (Z=15)
            species comarca aspect: labels;
            graphics "Transit Zone Labels" {
                draw "IN TRANSIT" at: center_pt + {0, 0, 15} anchor: #center color: rgb(120,120,120) font: font("Helvetica", 18, #bold);
                // Le pourcentage bien espacé en dessous
                draw string(transit_pct with_precision 1) + "%" at: center_pt + {0, 180, 15} anchor: #center color: rgb(150,150,150) font: font("Helvetica", 16, #bold);
            }
            
            // COUCHE 4 : L'heure
            graphics "HUD" {
                string h <- string(current_date.hour);
                string m <- (current_date.minute < 10 ? "0" : "") + string(current_date.minute);
                
                point time_pos <- {world.shape.width * 0.03, world.shape.height * 0.08};
                draw h + ":" + m at: time_pos color: rgb(50, 50, 50) font: font("Helvetica", 80, #bold);
            }
        }
    }
}