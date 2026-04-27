import httpx
import asyncio

async def query_wms():
    bbox = "-13014303.18,3827944.74,-13014293.18,3827954.74"
    url = (
        "https://gemelodigital.implantijuana.gob.mx/geoserver-local-proxy/wms?"
        "SERVICE=WMS&VERSION=1.1.1&REQUEST=GetFeatureInfo&"
        "QUERY_LAYERS=catastro_pub:predios-211126_Predios&"
        "LAYERS=catastro_pub:predios-211126_Predios&"
        "INFO_FORMAT=application/json&"
        "X=160&Y=160&WIDTH=320&HEIGHT=320&SRS=EPSG:3857&"
        f"BBOX={bbox}"
    )
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Referer": "https://gemelodigital.implantijuana.gob.mx/catastro/",
        "Origin": "https://gemelodigital.implantijuana.gob.mx"
    }
    
    print(f"Querying WMS: {url}")
    
    async with httpx.AsyncClient(verify=False) as client:
        try:
            response = await client.get(url, headers=headers, timeout=15.0)
            if response.status_code == 200:
                data = response.json()
                features = data.get("features", [])
                if features:
                    properties = features[0].get("properties", {})
                    cve_cat = properties.get("cve_cat")
                    print(f"\n[SUCCESS] Found Cadastral Key: {cve_cat}")
                    print(f"Properties: {properties}")
                    return cve_cat
                else:
                    print("\n[FAILED] No features found at these coordinates.")
            else:
                print(f"\n[ERROR] WMS Error: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"\n[ERROR] Exception: {str(e)}")
    return None

if __name__ == "__main__":
    asyncio.run(query_wms())
