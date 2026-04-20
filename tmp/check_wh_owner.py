import uuid

NAMESPACE = uuid.NAMESPACE_DNS
companies = {
    "CO_LOGISTICS_MX_ID": uuid.UUID("ad6cc8a6-34f9-42df-8f29-28254e0ad242"),
    "CO_LOGISTICS_US_ID": uuid.UUID("777cc8a6-34f9-42df-8f29-28254e0ad277"),
    "INTERNO_CORP_ID": uuid.UUID("9cd9986b-89da-48b7-8733-26a2a1225b01")
}

warehouse_codes = ["WH-TIJ", "WH-QUARANTINE", "WH-ENS", "WH-SDY", "WH-OTY"]

target_wh = uuid.UUID("ce699eae-5db7-5d0a-a808-fd57a400523a")

for name, cid in companies.items():
    for code in warehouse_codes:
        generated_id = uuid.uuid5(NAMESPACE, f"interno.warehouse.{cid}.{code}")
        if generated_id == target_wh:
            print(f"MATCH: {name} ({cid}) owns warehouse {code} ({generated_id})")
            exit(0)

print("No match found in known companies.")
