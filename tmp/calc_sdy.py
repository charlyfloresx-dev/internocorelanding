import uuid
cid = uuid.UUID("ad6cc8a6-34f9-42df-8f29-28254e0ad242")
print("WH-SDY:", uuid.uuid5(uuid.NAMESPACE_DNS, f"interno.warehouse.{cid}.WH-SDY"))
