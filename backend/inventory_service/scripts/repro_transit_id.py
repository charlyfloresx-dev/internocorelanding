import uuid
import os
import sys

# Simulation of what happens in the service
TO_WH_ID_STR = "386261e6-6a8c-5755-8e70-12287f2dd9f3"
to_warehouse_id = uuid.UUID(TO_WH_ID_STR)

# ID calculation
transit_id_str = f"{to_warehouse_id}_transit"
transit_id = uuid.uuid5(uuid.NAMESPACE_OID, transit_id_str)

print(f"To WH ID: {to_warehouse_id}")
print(f"String used for uuid5: {transit_id_str}")
print(f"Calculated Transit ID: {transit_id}")

EXPECTED_ERROR_ID = "537af6a5-cd97-50f0-9509-0d1f6226845e"
if str(transit_id) == EXPECTED_ERROR_ID:
    print("MATCH! The ID generation is correct.")
else:
    print(f"NO MATCH! Expected {EXPECTED_ERROR_ID}, got {transit_id}")
