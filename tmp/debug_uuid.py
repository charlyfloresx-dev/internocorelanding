import uuid
cid = uuid.UUID("ad6cc8a6-34f9-42df-8f29-28254e0ad242")
# Maybe without prefix?
print("No prefix:", uuid.uuid5(uuid.NAMESPACE_DNS, f"{cid}.WH-TIJ"))
# Maybe with different prefix?
print("Warehouse prefix:", uuid.uuid5(uuid.NAMESPACE_DNS, f"interno.warehouse.{cid}.WH-TIJ"))
