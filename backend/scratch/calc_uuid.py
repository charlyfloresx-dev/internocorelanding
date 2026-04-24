
import uuid
namespace = uuid.NAMESPACE_DNS
ENTERPRISE_ID = uuid.UUID("9cd9986b-89da-48b7-8733-26a2a1225b01")
ccode = "SAL-VEN"
c_id = uuid.uuid5(namespace, f"interno.concept.{ENTERPRISE_ID}.{ccode}")
print(f"Venta (SAL-VEN) ID: {c_id}")
