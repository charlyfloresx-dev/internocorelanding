import uuid
namespace = uuid.NAMESPACE_DNS
print(f"WH-MAIN: {uuid.uuid5(namespace, 'interno.warehouse.WH-MAIN')}")
print(f"WH-TRANSIT: {uuid.uuid5(namespace, 'interno.warehouse.WH-TRANSIT')}")
print(f"WH-QUARANTINE: {uuid.uuid5(namespace, 'interno.warehouse.WH-QUARANTINE')}")
print(f"WH-ENS: {uuid.uuid5(namespace, 'interno.warehouse.WH-ENS')}")
print(f"WH-OTY: {uuid.uuid5(namespace, 'interno.warehouse.WH-OTY')}")
