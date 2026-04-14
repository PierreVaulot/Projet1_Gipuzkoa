model SimulationGipuzkoaSimple

global {
    // 1. Déclaration des fichiers
    file shape_file_distritos <- file("../includes/gipuzkoa_distritos.shp");
    file csv_establishments <- csv_file("../includes/df_establishments.csv", true);
    
    geometry shape <- envelope(shape_file_distritos);

    init {
        // --- Étape A : Districts ---
        write "⏳ Chargement du fond de carte...";
        create district from: shape_file_distritos;
        
        // --- Étape B : Établissements ---
        matrix data <- matrix(csv_establishments);
        int total_rows <- data.rows;
        write "📊 Traitement de " + total_rows + " points de travail...";
        
        loop i from: 0 to: total_rows - 1 {
            // Barre de progression simple
            if (i mod 10000 = 0) {
                write "   > " + round((i / total_rows) * 100) + "% effectués...";
            }

            create establishment {
                // On ne lit que les coordonnées pour aller plus vite
                point gps_precis <- {float(data[13, i]), float(data[12, i])};
                point gps_fallback <- {float(data[16, i]), float(data[15, i])};

                // Conversion de coordonnées
                if (gps_precis.x != 0.0) {
                    location <- CRS_transform(gps_precis, "EPSG:4326").location;
                } else {
                    location <- CRS_transform(gps_fallback, "EPSG:4326").location;
                }
                
                // IMPORTANT : On a supprimé le "my_district <- ..." pour gagner du temps
            }
        }
        write "✅ TERMINÉ ! La carte est prête.";
    }
}

// --- DÉFINITION DES ESPÈCES ---

species district {
    aspect default {
        draw shape color: #gray border: #white; // Fond gris neutre
    }
}

species establishment {
    aspect default {
        // Taille constante (plus de calcul de capacité) et couleur unique
        draw circle(120) color: #royalblue; 
    }
}

// --- INTERFACE ---

experiment Main type: gui {
    output {
        display Carte_Simplifiee {
            species district aspect: default;
            species establishment aspect: default;
        }
    }
}