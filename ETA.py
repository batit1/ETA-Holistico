import math
import json

class NextParkIntegrationEngine:
    """
    Motor de integración para el proyecto PERTE VEC.
    Une la predicción de tráfico en el Edge con el algoritmo NEXTPARK.
    """
    
    def __init__(self):
        # Parámetros técnicos definidos en la propuesta técnica
        self.walking_speed_kmh = 4.8  
        self.occupancy_threshold = 0.95  # Filtro de seguridad del 95%
        self.maneuver_time_min = 4.0     # Tiempo estimado de rampa y aparque
        
    def get_traffic_prediction(self, destination_id):
        """
        Simula la lectura del modelo de tráfico (Capa Edge).
        Representa los datos que no se pudieron descargar por el error de acceso.
        """
        # Simulamos una respuesta del modelo de tráfico actual
        return {
            "target_node": destination_id,
            "travel_time_min": 18.5,
            "status": "success"
        }

    def get_nextpark_availability(self, lat, lon):
        """
        Simula la consulta al algoritmo NEXTPARK.
        Busca parkings en un radio de 500m[cite: 5].
        """
        # Datos basados en los resultados de rendimiento de NEXTPARK[cite: 2, 5]
        return [
            {"id": "PK-01", "name": "Parking Centro", "coords": (40.415, -3.702), "occupancy": 0.75},
            {"id": "PK-02", "name": "Parking Recoletos", "coords": (40.418, -3.705), "occupancy": 0.98}, # Será filtrado
            {"id": "PK-03", "name": "Parking Atocha", "coords": (40.412, -3.698), "occupancy": 0.50}
        ]

    def calculate_walking_time(self, start_coords, end_coords):
        """
        Calcula el tiempo a pie (Last Mile).
        Implementa una aproximación de la distancia para el tramo peatonal[cite: 5].
        """
        # Distancia euclidiana simple convertida a km (aprox)
        dist = math.sqrt((start_coords[0] - end_coords[0])**2 + (start_coords[1] - end_coords[1])**2)
        dist_km = dist * 111.1  # Conversión de grados a km
        
        # Tiempo = (Distancia / Velocidad) * 60 minutos
        return (dist_km / self.walking_speed_kmh) * 60

    def solve_holistic_eta(self, user_lat, user_lon):
        """
        Algoritmo principal: Aplica la fórmula maestra de integración[cite: 5].
        ETA = T_tráfico + T_maniobra + T_caminata
        """
        print(f"Calculando ruta óptima para destino: ({user_lat}, {user_lon})...\n")
        
        # 1. Obtener predicción de tráfico hasta el área
        traffic = self.get_traffic_prediction("NODE_A1")
        t_drive = traffic["travel_time_min"]
        
        # 2. Obtener disponibilidad de NEXTPARK
        parking_list = self.get_nextpark_availability(user_lat, user_lon)
        
        results = []

        for pk in parking_list:
            # APLICACIÓN DE REGLA DE NEGOCIO: Filtro de ocupación[cite: 5]
            if pk["occupancy"] >= self.occupancy_threshold:
                print(f"[-] {pk['name']} descartado: Ocupación crítica ({pk['occupancy']*100}%).")
                continue
            
            # 3. Calcular tramo a pie
            t_walk = self.calculate_walking_time(pk["coords"], (user_lat, user_lon))
            
            # 4. Cálculo final del ETA Holístico[cite: 5]
            total_eta = t_drive + self.maneuver_time_min + t_walk
            
            results.append({
                "parking": pk["name"],
                "total_eta": round(total_eta, 2),
                "breakdown": {
                    "driving": t_drive,
                    "parking_maneuver": self.maneuver_time_min,
                    "walking": round(t_walk, 2)
                }
            })

        # 5. Selección de la mejor opción (Minimización de tiempo)[cite: 5]
        if not results:
            return "No se encontraron opciones viables con los criterios actuales."
            
        best_option = min(results, key=lambda x: x["total_eta"])
        return best_option

# --- Bloque de ejecución para prueba ---
if __name__ == "__main__":
    # Instanciamos el motor de integración
    engine = NextParkIntegrationEngine()
    
    # Coordenadas de destino (ejemplo en Madrid)
    destino_final = (40.416, -3.703)
    
    # Ejecutamos el cálculo
    propuesta = engine.solve_holistic_eta(destino_final[0], destino_final[1])
    
    # Mostramos el resultado formateado
    print("\n" + "="*40)
    print("RESULTADO DE LA INTEGRACIÓN PERTE VEC")
    print("="*40)
    print(json.dumps(propuesta, indent=4))
    print("="*40)