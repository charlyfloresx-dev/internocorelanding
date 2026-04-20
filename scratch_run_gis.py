import asyncio
import sys

# Ensure backend directory is in the path so we can import 'common'
sys.path.append("/app")

from common.gis.infrastructure.services.arcgis_tijuana_provider import ArcGisTijuanaProvider

async def main():
    service = ArcGisTijuanaProvider()
    print("Iniciando validación de la dirección 'Venustiano Carranza 6319-C'...")
    try:
        response = await service.get_location_by_address("Venustiano Carranza 6319-C")
        print("\n--- Resultados de PropertyValidationResponse ---")
        if response:
            print(f"Address: {response.address}")
            print(f"Cadastral Key: {response.cadastral_key}")
            print(f"Owner Name: {response.owner_name}")
            print(f"Land Use (Zonificación): {response.land_use}")
            print(f"Location: Lat {response.location.lat}, Lng {response.location.lng}")
        else:
            print("No se encontraron resultados.")
    except Exception as e:
        print(f"Error durante la validación por dirección: {e}")

    print("\nIniciando validación de coordenadas (32.49081, -116.90954)...")
    try:
        coord_response = await service.get_data_by_coordinates(32.49081, -116.90954, company_id="TEST_CO")
        print("\n--- Resultados de Coordenadas ---")
        if coord_response:
            print(f"Cadastral Key: {coord_response.cadastral_key}")
            print(f"Owner Name: {coord_response.owner_name}")
            print(f"Land Use: {coord_response.land_use}")
        else:
            print("No se encontraron resultados.")
    except Exception as e:
         print(f"Error durante la validación por coordenadas: {e}")

if __name__ == "__main__":
    asyncio.run(main())
