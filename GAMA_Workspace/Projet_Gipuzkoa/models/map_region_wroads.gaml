model GipuzkoaFinalStable

global {
    // 1. Vos deux fichiers sources originaux dans le dossier includes
    file shape_region <- file("../includes/gipuzkoa_distritos.shp"); 
    file shape_roads <- file("../includes/road_gipuzkoa/road_gipuzkoa.shp");
    
    // Le monde est défini par la province (0,0 est le coin en haut à gauche)
    geometry shape <- envelope(shape_region);

    init {
        // Création de la province
        create region_map from: shape_region;
        
        // 2. Création des routes
        create road from: shape_roads;
        
        // 3. REPOSITIONNEMENT MANUEL (Pour éviter les erreurs d'opérateurs)
        // On vérifie si les routes sont à leurs coordonnées GPS (ex: 500.000) 
        // ou si elles sont déjà proches de la province (0,0)
        
        if (!empty(road)) {
            // On prend le point le plus à l'ouest et le plus au nord du fichier de routes
            geometry road_box <- envelope(road);
            
            // On calcule l'écart (le décalage)
            // On utilise la position du centre moins la demi-largeur
            float off_x <- road_box.location.x - (road_box.width / 2);
            float off_y <- road_box.location.y + (road_box.height / 2);
            
            // Si le décalage est important, on translate tout le monde
            if (off_x > 1000) {
                write "🛠️ Alignement des routes en cours...";
                ask road {
                    // On déplace chaque segment : (Coordonnée Réelle - Minimum)
                    // Pour le Y, on inverse pour que le Nord reste en haut (GAMA inverse le Y)
                    location <- {location.x - off_x, off_y - location.y};
                }
                write "✅ Alignement terminé.";
            }
        }
    }
}

species region_map {
    aspect default {
        draw shape color: rgb(240, 240, 240) border: #gray;
    }
}

species road {
    aspect default {
        // Noir fin pour voir tout le réseau provincial
        draw shape color: #black width: 0.8;
    }
}

experiment Main type: gui {
    output {
        display Carte_Gipuzkoa background: #white {
            species region_map aspect: default;
            species road aspect: default;
        }
    }
}