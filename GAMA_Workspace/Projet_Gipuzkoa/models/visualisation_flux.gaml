model FluxGipuzkoa

global {
    file shape_file_zones <- file("../includes/gipuzkoa_distritos.shp");
    file csv_file_data <- csv_file("../includes/flux_gipuzkoa_final.csv", ",");

    geometry shape <- envelope(shape_file_zones);

    init {
        write "1. Création de la carte...";
        
      
        create zone from: shape_file_zones with: [id::string(read("ID"))]; 

        
        map<string, zone> map_zones <- zone as_map (each.id::each);

        write "2. Chargement des données...";
        matrix data <- matrix(csv_file_data);
        
        
        int total_lignes <- data.rows - 1;
        int palier <- int(total_lignes / 10); 
        
        write "Total des trajets à analyser : " + total_lignes;

        loop i from: 1 to: total_lignes {
            
            
            if (palier > 0 and (i mod palier = 0)) {
                int pourcentage <- int((i / total_lignes) * 100);
                write "   ⏳ En cours : " + pourcentage + "% (" + i + " lignes lues)";
            }
            
           
            string id_depart <- string(data[2, i]);       // Col 2: origen
            string id_arrivee <- string(data[3, i]);      // Col 3: destino
            float nombre_personnes <- float(data[13, i]); // Col 13: viajes

            
            if (id_depart in map_zones.keys and id_arrivee in map_zones.keys) {
                
                if (nombre_personnes > 0) {
                    create voyage {
                        depart <- map_zones[id_depart];
                        arrivee <- map_zones[id_arrivee];
                        nb_personnes <- nombre_personnes;
                        
                        
                        shape <- line([depart.location, arrivee.location]);
                    }
                }
            }
        }
        
        write "✅ 3. Simulation prête ! " + length(voyage) + " flux générés.";
    }
}


species zone {
    string id;
    
    aspect base {
        
        draw shape color: #gainsboro border: #gray;
    }
}

species voyage {
    zone depart;
    zone arrivee;
    float nb_personnes;

    aspect flow {
        
        float epaisseur <- nb_personnes / 100;
        if (epaisseur < 0.1) { epaisseur <- 0.1; }

        draw shape width: epaisseur color: rgb(255, 0, 0, 100);
    }
}


experiment Visualisation type: gui {
    output {
        display map type: java2D background: #white {
            species zone aspect: base;
            species voyage aspect: flow;
        }
    }
}