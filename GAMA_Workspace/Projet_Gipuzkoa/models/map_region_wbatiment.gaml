model SimulationGipuzkoaHeatmap

global {
    // 1. Remplacez par le nom exact de votre fichier Shapefile de la région
    file shape_region <- file("../includes/gipuzkoa_distritos.shp");
    file csv_points <- csv_file("../includes/points_region_prets.csv", true);
    
    geometry shape <- envelope(shape_region);

    init {
        // Création du fond de carte (communes ou province)
        create region_map from: shape_region;
        
        // Chargement massif des 55 000 points
        matrix data <- matrix(csv_points);
        loop i from: 0 to: data.rows - 1 {
            create establishment {
                // Utilisation des colonnes gama_x (0) et gama_y (1)
                location <- {float(data[0, i]), float(data[1, i])};
            }
        }
        write "Région chargée avec " + length(establishment) + " établissements.";
    }
}

species region_map {
    aspect default {
        draw shape color: #lightgrey border: #grey;
    }
}

species establishment {
    aspect default {
        // Pour la région, on utilise des cercles plus petits (60m)
        // et une transparence plus forte (30 sur 255)
        draw circle(60) color: rgb(220, 20, 60, 30); 
    }
}

experiment Main type: gui {
    output {
        display Carte_Regionale {
            species region_map aspect: default;
            species establishment aspect: default;
        }
    }
}