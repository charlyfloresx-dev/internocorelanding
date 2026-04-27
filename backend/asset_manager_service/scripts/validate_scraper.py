import asyncio
import sys
import os

# Add parent directory to path to import the service
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.modules.investments.infrastructure.rppc_scraper import RppcScraperService

async def main():
    scraper = RppcScraperService()
    
    # User's test data
    address = "Venustiano Carranza 6319"
    target_unit = "C"
    
    print(f"--- Validating Scraper for: {address} (Unit {target_unit}) ---")
    
    # 1. Search by confirmed Clave Catastral from GIS
    confirmed_cve = "PK020027"
    print(f"Searching RPPC by confirmed Clave Catastral: {confirmed_cve}...")
    results = await scraper.get_ownership_data(confirmed_cve)
    
    if not results:
        print("No results found by Clave Catastral. Trying search by address...")
        results = await scraper.search_by_address("VENUSTIANO CARRANZA")
    
    if not results:
        print("No results found by address either.")
        return

    print(f"Found {len(results)} potential units/lots.")
    
    # 2. Filter for Unit C
    print(f"Filtering for Unit {target_unit}...")
    unit_data = scraper.filter_by_unit(results, target_unit)
    
    if unit_data:
        print("\n[SUCCESS] Unit Found:")
        print(f"Folio: {unit_data.get('FOLIO')}")
        print(f"Description: {unit_data.get('DESCRIPCION')}")
        print(f"Owner (Titular): {unit_data.get('TITULAR', 'N/A')}")
        print(f"Status: {unit_data.get('ESTADO')}")
    else:
        print("\n[FAILED] Unit C not found in results.")
        print("Available results (first 5):")
        for r in results[:5]:
            print(f"- {r.get('DESCRIPCION')} | Folio: {r.get('FOLIO')}")

if __name__ == "__main__":
    asyncio.run(main())
