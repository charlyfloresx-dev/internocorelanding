import uuid
cid = uuid.UUID("ad6cc8a6-34f9-42df-8f29-28254e0ad242")
code = "WH-TIJ"
print(uuid.uuid5(uuid.NAMESPACE_DNS, f"interno.warehouse.{cid}.{code}"))
