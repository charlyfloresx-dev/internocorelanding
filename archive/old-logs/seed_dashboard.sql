-- SEED DATA FOR MISSION CONTROL DASHBOARD
SET search_path TO public;
DELETE FROM inventory_movements WHERE company_id = '{COMPANY_ID}';
DELETE FROM inventory_levels WHERE company_id = '{COMPANY_ID}';

                INSERT INTO inventory_levels (id, company_id, warehouse_id, product_id, uom_id, quantity, weighted_average_cost, currency_code, is_active, version_id, created_at)
                VALUES ('dad554bb-e002-494e-a5b5-b117801ea4f6', '9cd9986b-89da-48b7-8733-26a2a1225b01', '536d182d-3447-5788-87d9-e488ae0af797', '73acb311-dd79-5f5c-bfe8-dc872aace290', '550e8400-e29b-41d4-a716-446655440000', 1044, 89.17369979008681, 'USD', true, 1, now());
            

                INSERT INTO inventory_levels (id, company_id, warehouse_id, product_id, uom_id, quantity, weighted_average_cost, currency_code, is_active, version_id, created_at)
                VALUES ('22868fc7-0030-428e-bd99-a3823585742f', '9cd9986b-89da-48b7-8733-26a2a1225b01', '536d182d-3447-5788-87d9-e488ae0af797', 'db856803-a63d-5468-9a7c-9039702acca9', '550e8400-e29b-41d4-a716-446655440000', 1005, 20.253116420474264, 'USD', true, 1, now());
            

                INSERT INTO inventory_levels (id, company_id, warehouse_id, product_id, uom_id, quantity, weighted_average_cost, currency_code, is_active, version_id, created_at)
                VALUES ('fdca703f-0869-4d07-a995-8efc12f94532', '9cd9986b-89da-48b7-8733-26a2a1225b01', '536d182d-3447-5788-87d9-e488ae0af797', '83acb311-dd79-5f5c-bfe8-dc872aace290', '550e8400-e29b-41d4-a716-446655440000', 1108, 32.323823689517525, 'USD', true, 1, now());
            

                INSERT INTO inventory_levels (id, company_id, warehouse_id, product_id, uom_id, quantity, weighted_average_cost, currency_code, is_active, version_id, created_at)
                VALUES ('e963060b-0976-42d6-ad10-bf6b9d12522c', '9cd9986b-89da-48b7-8733-26a2a1225b01', '536d182d-3447-5788-87d9-e488ae0af797', '93acb311-dd79-5f5c-bfe8-dc872aace290', '550e8400-e29b-41d4-a716-446655440000', 1428, 105.50348697556474, 'USD', true, 1, now());
            

                INSERT INTO inventory_levels (id, company_id, warehouse_id, product_id, uom_id, quantity, weighted_average_cost, currency_code, is_active, version_id, created_at)
                VALUES ('f02256de-c0db-4ae7-970c-28803e54ace1', '9cd9986b-89da-48b7-8733-26a2a1225b01', '22222222-2222-2222-2222-222222222222', '73acb311-dd79-5f5c-bfe8-dc872aace290', '550e8400-e29b-41d4-a716-446655440000', 311, 116.13758690833855, 'USD', true, 1, now());
            

                INSERT INTO inventory_levels (id, company_id, warehouse_id, product_id, uom_id, quantity, weighted_average_cost, currency_code, is_active, version_id, created_at)
                VALUES ('527c78dc-4dc0-4feb-aaea-20c0a9c68b29', '9cd9986b-89da-48b7-8733-26a2a1225b01', '22222222-2222-2222-2222-222222222222', 'db856803-a63d-5468-9a7c-9039702acca9', '550e8400-e29b-41d4-a716-446655440000', 777, 25.164459144170245, 'USD', true, 1, now());
            

                INSERT INTO inventory_levels (id, company_id, warehouse_id, product_id, uom_id, quantity, weighted_average_cost, currency_code, is_active, version_id, created_at)
                VALUES ('2a064aea-437f-4584-8663-1023ac611f0e', '9cd9986b-89da-48b7-8733-26a2a1225b01', '22222222-2222-2222-2222-222222222222', '83acb311-dd79-5f5c-bfe8-dc872aace290', '550e8400-e29b-41d4-a716-446655440000', 665, 94.49667237566703, 'USD', true, 1, now());
            

                INSERT INTO inventory_levels (id, company_id, warehouse_id, product_id, uom_id, quantity, weighted_average_cost, currency_code, is_active, version_id, created_at)
                VALUES ('106293ee-ebff-4548-9d3c-87e0b6f062a8', '9cd9986b-89da-48b7-8733-26a2a1225b01', '22222222-2222-2222-2222-222222222222', '93acb311-dd79-5f5c-bfe8-dc872aace290', '550e8400-e29b-41d4-a716-446655440000', 1472, 63.57953108678762, 'USD', true, 1, now());
            

                INSERT INTO inventory_levels (id, company_id, warehouse_id, product_id, uom_id, quantity, weighted_average_cost, currency_code, is_active, version_id, created_at)
                VALUES ('383f3511-c854-412b-a19d-dbad3a3df685', '9cd9986b-89da-48b7-8733-26a2a1225b01', 'bb18f763-3f93-53af-9fb8-ca1c752f3873', '73acb311-dd79-5f5c-bfe8-dc872aace290', '550e8400-e29b-41d4-a716-446655440000', 1371, 66.61842752730593, 'USD', true, 1, now());
            

                INSERT INTO inventory_levels (id, company_id, warehouse_id, product_id, uom_id, quantity, weighted_average_cost, currency_code, is_active, version_id, created_at)
                VALUES ('9c3484ef-a8f3-4079-97be-996d7c895aa5', '9cd9986b-89da-48b7-8733-26a2a1225b01', 'bb18f763-3f93-53af-9fb8-ca1c752f3873', 'db856803-a63d-5468-9a7c-9039702acca9', '550e8400-e29b-41d4-a716-446655440000', 614, 60.93239011451783, 'USD', true, 1, now());
            

                INSERT INTO inventory_levels (id, company_id, warehouse_id, product_id, uom_id, quantity, weighted_average_cost, currency_code, is_active, version_id, created_at)
                VALUES ('5f403d8e-3788-415f-8ace-26acf5070568', '9cd9986b-89da-48b7-8733-26a2a1225b01', 'bb18f763-3f93-53af-9fb8-ca1c752f3873', '83acb311-dd79-5f5c-bfe8-dc872aace290', '550e8400-e29b-41d4-a716-446655440000', 729, 15.003150429651063, 'USD', true, 1, now());
            

                INSERT INTO inventory_levels (id, company_id, warehouse_id, product_id, uom_id, quantity, weighted_average_cost, currency_code, is_active, version_id, created_at)
                VALUES ('9651a244-06ac-4e50-ab02-73dad6be7522', '9cd9986b-89da-48b7-8733-26a2a1225b01', 'bb18f763-3f93-53af-9fb8-ca1c752f3873', '93acb311-dd79-5f5c-bfe8-dc872aace290', '550e8400-e29b-41d4-a716-446655440000', 431, 73.7569121347918, 'USD', true, 1, now());
            

                INSERT INTO inventory_levels (id, company_id, warehouse_id, product_id, uom_id, quantity, weighted_average_cost, currency_code, is_active, version_id, created_at)
                VALUES ('95bc3377-ffa5-4462-8ccd-834a2f3d67db', '9cd9986b-89da-48b7-8733-26a2a1225b01', '33333333-3333-3333-3333-333333333333', '73acb311-dd79-5f5c-bfe8-dc872aace290', '550e8400-e29b-41d4-a716-446655440000', 1345, 77.20874464358465, 'USD', true, 1, now());
            

                INSERT INTO inventory_levels (id, company_id, warehouse_id, product_id, uom_id, quantity, weighted_average_cost, currency_code, is_active, version_id, created_at)
                VALUES ('c6e48028-3efc-4413-8f79-69e8fbd0337c', '9cd9986b-89da-48b7-8733-26a2a1225b01', '33333333-3333-3333-3333-333333333333', 'db856803-a63d-5468-9a7c-9039702acca9', '550e8400-e29b-41d4-a716-446655440000', 850, 30.902236511782625, 'USD', true, 1, now());
            

                INSERT INTO inventory_levels (id, company_id, warehouse_id, product_id, uom_id, quantity, weighted_average_cost, currency_code, is_active, version_id, created_at)
                VALUES ('8914263c-3936-4de5-9885-77c4efc64893', '9cd9986b-89da-48b7-8733-26a2a1225b01', '33333333-3333-3333-3333-333333333333', '83acb311-dd79-5f5c-bfe8-dc872aace290', '550e8400-e29b-41d4-a716-446655440000', 1166, 22.160205585388972, 'USD', true, 1, now());
            

                INSERT INTO inventory_levels (id, company_id, warehouse_id, product_id, uom_id, quantity, weighted_average_cost, currency_code, is_active, version_id, created_at)
                VALUES ('a6ab95e6-a828-49a7-ba32-0755177f541f', '9cd9986b-89da-48b7-8733-26a2a1225b01', '33333333-3333-3333-3333-333333333333', '93acb311-dd79-5f5c-bfe8-dc872aace290', '550e8400-e29b-41d4-a716-446655440000', 763, 107.14112830616149, 'USD', true, 1, now());
            

                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('796ab3db-d6df-49e0-8ca8-d1cfbc90f9c6', '9cd9986b-89da-48b7-8733-26a2a1225b01', '536d182d-3447-5788-87d9-e488ae0af797', '93acb311-dd79-5f5c-bfe8-dc872aace290', '550e8400-e29b-41d4-a716-446655440000', 59, 1.5, 'IN', 'ENT', 'fa992a36-a2c2-48a1-add8-cb14b33fb649', true, 1, '2026-03-15 06:50:48');
            

                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('f7e8a3d3-7f51-47dd-9366-7d018fef7147', '9cd9986b-89da-48b7-8733-26a2a1225b01', '536d182d-3447-5788-87d9-e488ae0af797', '73acb311-dd79-5f5c-bfe8-dc872aace290', '550e8400-e29b-41d4-a716-446655440000', 40, 1.2, 'OUT', 'SAL', '52658cd5-837c-46c6-8272-2bd0cd6713e6', true, 1, '2026-03-15 06:50:48');
            

                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('bec9d97a-21bc-48f4-a878-8c0dca81199d', '9cd9986b-89da-48b7-8733-26a2a1225b01', '536d182d-3447-5788-87d9-e488ae0af797', '83acb311-dd79-5f5c-bfe8-dc872aace290', '550e8400-e29b-41d4-a716-446655440000', 33, 1.5, 'IN', 'ENT', '9dbd6fc0-266c-420d-a5cd-83d98e7dbde9', true, 1, '2026-03-15 05:50:48');
            

                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('54178d1e-ed03-44fc-9fc5-c0e4432418ab', '9cd9986b-89da-48b7-8733-26a2a1225b01', '536d182d-3447-5788-87d9-e488ae0af797', '93acb311-dd79-5f5c-bfe8-dc872aace290', '550e8400-e29b-41d4-a716-446655440000', 44, 1.2, 'OUT', 'SAL', 'cb4f066b-7792-4bcb-bc9c-5321b9ecd253', true, 1, '2026-03-15 05:50:48');
            

                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('14462fe7-5764-444f-abf1-8d1c31624549', '9cd9986b-89da-48b7-8733-26a2a1225b01', '536d182d-3447-5788-87d9-e488ae0af797', '73acb311-dd79-5f5c-bfe8-dc872aace290', '550e8400-e29b-41d4-a716-446655440000', 22, 1.5, 'IN', 'ENT', 'a68cf2d1-4d6e-43ba-ba4c-f371f74fb070', true, 1, '2026-03-15 04:50:48');
            

                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('0d930a5a-bea5-4720-ad82-db7a2cdae9b1', '9cd9986b-89da-48b7-8733-26a2a1225b01', '536d182d-3447-5788-87d9-e488ae0af797', '83acb311-dd79-5f5c-bfe8-dc872aace290', '550e8400-e29b-41d4-a716-446655440000', 21, 1.2, 'OUT', 'SAL', '57057390-b98e-4eea-98cd-97e76921c959', true, 1, '2026-03-15 04:50:48');
            

                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('19227255-8950-4bb6-9f0b-63453295e17b', '9cd9986b-89da-48b7-8733-26a2a1225b01', '536d182d-3447-5788-87d9-e488ae0af797', '73acb311-dd79-5f5c-bfe8-dc872aace290', '550e8400-e29b-41d4-a716-446655440000', 37, 1.5, 'IN', 'ENT', '5715319c-7b8c-4dea-b4da-536e1d8f07d2', true, 1, '2026-03-15 03:50:48');
            

                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('b4e3b409-5b3e-4501-84c2-d142e3708e29', '9cd9986b-89da-48b7-8733-26a2a1225b01', '536d182d-3447-5788-87d9-e488ae0af797', 'db856803-a63d-5468-9a7c-9039702acca9', '550e8400-e29b-41d4-a716-446655440000', 40, 1.2, 'OUT', 'SAL', 'ef3463a0-c2ff-48ee-92fc-a1fe4206e00f', true, 1, '2026-03-15 03:50:48');
            

                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('9806610b-f387-4aee-b19a-b6570956de13', '9cd9986b-89da-48b7-8733-26a2a1225b01', '536d182d-3447-5788-87d9-e488ae0af797', 'db856803-a63d-5468-9a7c-9039702acca9', '550e8400-e29b-41d4-a716-446655440000', 57, 1.5, 'IN', 'ENT', 'f6f99889-36b9-4389-a54d-013c4653bb74', true, 1, '2026-03-15 02:50:48');
            

                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('dd3fe4d7-f99f-4401-a4a2-43dfa17c9ae2', '9cd9986b-89da-48b7-8733-26a2a1225b01', '536d182d-3447-5788-87d9-e488ae0af797', '93acb311-dd79-5f5c-bfe8-dc872aace290', '550e8400-e29b-41d4-a716-446655440000', 30, 1.2, 'OUT', 'SAL', '83b60e84-52a1-47ab-abda-be93963e4e6a', true, 1, '2026-03-15 02:50:48');
            

                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('6ec5f91e-f2c4-4c88-a510-18246316e40e', '9cd9986b-89da-48b7-8733-26a2a1225b01', '536d182d-3447-5788-87d9-e488ae0af797', '93acb311-dd79-5f5c-bfe8-dc872aace290', '550e8400-e29b-41d4-a716-446655440000', 43, 1.5, 'IN', 'ENT', 'd22706b3-7dd6-45a5-9e13-50189a23bbeb', true, 1, '2026-03-15 01:50:48');
            

                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('b4d9e602-13a8-4e4d-8de4-763b2927466b', '9cd9986b-89da-48b7-8733-26a2a1225b01', '536d182d-3447-5788-87d9-e488ae0af797', '73acb311-dd79-5f5c-bfe8-dc872aace290', '550e8400-e29b-41d4-a716-446655440000', 22, 1.2, 'OUT', 'SAL', '98cb209c-0367-4c4e-8e55-0d588746105a', true, 1, '2026-03-15 01:50:48');
            

                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('eb498654-9732-408a-95c1-a8e4f77291b5', '9cd9986b-89da-48b7-8733-26a2a1225b01', '536d182d-3447-5788-87d9-e488ae0af797', '73acb311-dd79-5f5c-bfe8-dc872aace290', '550e8400-e29b-41d4-a716-446655440000', 40, 1.5, 'IN', 'ENT', 'decb9c00-cda6-4e48-b635-d4991e16d67c', true, 1, '2026-03-15 00:50:48');
            

                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('bb4535d1-3f50-47d4-b415-6abdb0475dbe', '9cd9986b-89da-48b7-8733-26a2a1225b01', '536d182d-3447-5788-87d9-e488ae0af797', 'db856803-a63d-5468-9a7c-9039702acca9', '550e8400-e29b-41d4-a716-446655440000', 8, 1.2, 'OUT', 'SAL', '83e5458e-40d9-479a-becc-deacabfd2a7d', true, 1, '2026-03-15 00:50:48');
            

                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('90c60652-3398-4567-91a1-9bb5c60d5ab2', '9cd9986b-89da-48b7-8733-26a2a1225b01', '536d182d-3447-5788-87d9-e488ae0af797', '73acb311-dd79-5f5c-bfe8-dc872aace290', '550e8400-e29b-41d4-a716-446655440000', 13, 1.5, 'IN', 'ENT', 'fde2145b-bf84-4a5d-8601-32ae9fd40277', true, 1, '2026-03-14 23:50:48');
            

                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('71280968-0f63-41a4-87d6-9daca3ce0e3a', '9cd9986b-89da-48b7-8733-26a2a1225b01', '536d182d-3447-5788-87d9-e488ae0af797', '93acb311-dd79-5f5c-bfe8-dc872aace290', '550e8400-e29b-41d4-a716-446655440000', 39, 1.2, 'OUT', 'SAL', 'cec4622a-5cf3-4133-9930-fd38ba77414b', true, 1, '2026-03-14 23:50:48');
            

                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('908791d4-30a9-4eea-90cd-5f56f3937231', '9cd9986b-89da-48b7-8733-26a2a1225b01', '536d182d-3447-5788-87d9-e488ae0af797', '93acb311-dd79-5f5c-bfe8-dc872aace290', '550e8400-e29b-41d4-a716-446655440000', 17, 1.5, 'IN', 'ENT', 'f5de3929-ae50-4526-b99b-3adfe3bc88bc', true, 1, '2026-03-14 22:50:48');
            

                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('3d46dc9f-fd3a-465e-ab5c-6826ca0d8e92', '9cd9986b-89da-48b7-8733-26a2a1225b01', '536d182d-3447-5788-87d9-e488ae0af797', '73acb311-dd79-5f5c-bfe8-dc872aace290', '550e8400-e29b-41d4-a716-446655440000', 25, 1.2, 'OUT', 'SAL', '86f931ee-6ec9-4114-9792-75e87a8a8449', true, 1, '2026-03-14 22:50:48');
            

                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('af1b6494-faad-45d1-af9d-12c8a7d9096e', '9cd9986b-89da-48b7-8733-26a2a1225b01', '536d182d-3447-5788-87d9-e488ae0af797', '93acb311-dd79-5f5c-bfe8-dc872aace290', '550e8400-e29b-41d4-a716-446655440000', 11, 1.5, 'IN', 'ENT', 'd4fad683-4443-4a60-9244-3e14477d8730', true, 1, '2026-03-14 21:50:48');
            

                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('22d97864-81be-4b14-a3cc-5dc2acb0693b', '9cd9986b-89da-48b7-8733-26a2a1225b01', '536d182d-3447-5788-87d9-e488ae0af797', '73acb311-dd79-5f5c-bfe8-dc872aace290', '550e8400-e29b-41d4-a716-446655440000', 33, 1.2, 'OUT', 'SAL', 'fda17e16-0a5b-47af-a9f0-2f49d7588fbf', true, 1, '2026-03-14 21:50:48');
            

                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('a6c8d958-2a0a-4212-88b3-5d194f797b85', '9cd9986b-89da-48b7-8733-26a2a1225b01', '536d182d-3447-5788-87d9-e488ae0af797', '73acb311-dd79-5f5c-bfe8-dc872aace290', '550e8400-e29b-41d4-a716-446655440000', 37, 1.5, 'IN', 'ENT', '807de893-37e8-43c1-b4a0-432e6b380996', true, 1, '2026-03-14 20:50:48');
            

                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('804a1437-edf6-4c00-9c72-84dfb738da32', '9cd9986b-89da-48b7-8733-26a2a1225b01', '536d182d-3447-5788-87d9-e488ae0af797', 'db856803-a63d-5468-9a7c-9039702acca9', '550e8400-e29b-41d4-a716-446655440000', 18, 1.2, 'OUT', 'SAL', '71606a97-7359-46eb-be0c-cac3623d9387', true, 1, '2026-03-14 20:50:48');
            

                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('4e029a50-02d9-4493-9626-dc0748757b4f', '9cd9986b-89da-48b7-8733-26a2a1225b01', '536d182d-3447-5788-87d9-e488ae0af797', '83acb311-dd79-5f5c-bfe8-dc872aace290', '550e8400-e29b-41d4-a716-446655440000', 21, 1.5, 'IN', 'ENT', '7596536e-eb5e-4c54-b1f5-1ff06a35f435', true, 1, '2026-03-14 19:50:48');
            

                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('90dd4e46-f567-4a87-ae14-cc97e3918dd9', '9cd9986b-89da-48b7-8733-26a2a1225b01', '536d182d-3447-5788-87d9-e488ae0af797', 'db856803-a63d-5468-9a7c-9039702acca9', '550e8400-e29b-41d4-a716-446655440000', 19, 1.2, 'OUT', 'SAL', 'cae3e7a1-ff43-4026-9c80-89fbf84e34aa', true, 1, '2026-03-14 19:50:48');
            

                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('591a02b1-8788-44de-81cb-a65b0960d51e', '9cd9986b-89da-48b7-8733-26a2a1225b01', '536d182d-3447-5788-87d9-e488ae0af797', '93acb311-dd79-5f5c-bfe8-dc872aace290', '550e8400-e29b-41d4-a716-446655440000', 38, 1.5, 'IN', 'ENT', '7b0b235a-98c6-4b62-aeb3-b6340ecc7f83', true, 1, '2026-03-14 18:50:48');
            

                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('46af4994-7b3f-40b0-8615-1aea3d668b15', '9cd9986b-89da-48b7-8733-26a2a1225b01', '536d182d-3447-5788-87d9-e488ae0af797', 'db856803-a63d-5468-9a7c-9039702acca9', '550e8400-e29b-41d4-a716-446655440000', 10, 1.2, 'OUT', 'SAL', '873c75bb-79b0-444f-848f-d47978c0583c', true, 1, '2026-03-14 18:50:48');
            

                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('af57e449-249e-4511-8470-0d6fe6a1bf39', '9cd9986b-89da-48b7-8733-26a2a1225b01', '536d182d-3447-5788-87d9-e488ae0af797', '73acb311-dd79-5f5c-bfe8-dc872aace290', '550e8400-e29b-41d4-a716-446655440000', 47, 1.5, 'IN', 'ENT', 'c6971379-658a-4b23-a9ca-2892ec850d67', true, 1, '2026-03-14 17:50:48');
            

                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('19705a30-8b64-4660-9218-7b1dbcb4f344', '9cd9986b-89da-48b7-8733-26a2a1225b01', '536d182d-3447-5788-87d9-e488ae0af797', 'db856803-a63d-5468-9a7c-9039702acca9', '550e8400-e29b-41d4-a716-446655440000', 44, 1.2, 'OUT', 'SAL', '9d274aed-d3d4-4513-ada8-2db92f016430', true, 1, '2026-03-14 17:50:48');
            

                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('38a0042d-d565-4df2-81bd-9544852e4853', '9cd9986b-89da-48b7-8733-26a2a1225b01', '536d182d-3447-5788-87d9-e488ae0af797', 'db856803-a63d-5468-9a7c-9039702acca9', '550e8400-e29b-41d4-a716-446655440000', 42, 1.5, 'IN', 'ENT', '98e76f72-4412-44fe-91c8-67de821fac79', true, 1, '2026-03-14 16:50:48');
            

                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('1070676c-c8cf-4146-b160-1fb0b5c7f59a', '9cd9986b-89da-48b7-8733-26a2a1225b01', '536d182d-3447-5788-87d9-e488ae0af797', '83acb311-dd79-5f5c-bfe8-dc872aace290', '550e8400-e29b-41d4-a716-446655440000', 26, 1.2, 'OUT', 'SAL', 'f0ba4d8b-aca7-47c0-9a35-2a63f93091a9', true, 1, '2026-03-14 16:50:48');
            

                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('0faafa30-5d86-43aa-8507-9a8370a776d8', '9cd9986b-89da-48b7-8733-26a2a1225b01', '536d182d-3447-5788-87d9-e488ae0af797', '73acb311-dd79-5f5c-bfe8-dc872aace290', '550e8400-e29b-41d4-a716-446655440000', 39, 1.5, 'IN', 'ENT', 'd319808d-28c2-4940-837d-00a3a9b586c1', true, 1, '2026-03-14 15:50:48');
            

                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('5bce8c33-3584-42a8-ac33-3a8381bde626', '9cd9986b-89da-48b7-8733-26a2a1225b01', '536d182d-3447-5788-87d9-e488ae0af797', '83acb311-dd79-5f5c-bfe8-dc872aace290', '550e8400-e29b-41d4-a716-446655440000', 37, 1.2, 'OUT', 'SAL', 'b3469d73-fc32-4ced-8c54-8acd5d81bf06', true, 1, '2026-03-14 15:50:48');
            

                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('5db16a72-7621-48b9-bdf7-cee546f7d067', '9cd9986b-89da-48b7-8733-26a2a1225b01', '536d182d-3447-5788-87d9-e488ae0af797', '83acb311-dd79-5f5c-bfe8-dc872aace290', '550e8400-e29b-41d4-a716-446655440000', 41, 1.5, 'IN', 'ENT', '0644d0b3-ea44-41d3-95e0-99025acb21dd', true, 1, '2026-03-14 14:50:48');
            

                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('69b6c27f-71df-476a-9db4-24a5cffc682e', '9cd9986b-89da-48b7-8733-26a2a1225b01', '536d182d-3447-5788-87d9-e488ae0af797', '83acb311-dd79-5f5c-bfe8-dc872aace290', '550e8400-e29b-41d4-a716-446655440000', 12, 1.2, 'OUT', 'SAL', '081be3e5-f267-4998-adcd-6212f34ec201', true, 1, '2026-03-14 14:50:48');
            

                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('53c0e0f5-05ec-4267-9aa0-03d054614c6e', '9cd9986b-89da-48b7-8733-26a2a1225b01', '536d182d-3447-5788-87d9-e488ae0af797', '93acb311-dd79-5f5c-bfe8-dc872aace290', '550e8400-e29b-41d4-a716-446655440000', 28, 1.5, 'IN', 'ENT', 'f5370646-d2a4-464e-a852-b7bac4bcd640', true, 1, '2026-03-14 13:50:48');
            

                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('4778dea3-5e02-4a59-a3c3-e57e89037802', '9cd9986b-89da-48b7-8733-26a2a1225b01', '536d182d-3447-5788-87d9-e488ae0af797', '93acb311-dd79-5f5c-bfe8-dc872aace290', '550e8400-e29b-41d4-a716-446655440000', 44, 1.2, 'OUT', 'SAL', '6ac5a39d-c876-4303-b3c1-df2996ca1441', true, 1, '2026-03-14 13:50:48');
            

                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('fa7ddefa-9ea5-4adb-ba00-ad542ce8ef3c', '9cd9986b-89da-48b7-8733-26a2a1225b01', '536d182d-3447-5788-87d9-e488ae0af797', '93acb311-dd79-5f5c-bfe8-dc872aace290', '550e8400-e29b-41d4-a716-446655440000', 28, 1.5, 'IN', 'ENT', '950e1ef3-f90a-42f1-ae1b-035ca949f037', true, 1, '2026-03-14 12:50:48');
            

                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('c34f86d0-2905-415a-9a7b-4fc0fc513f12', '9cd9986b-89da-48b7-8733-26a2a1225b01', '536d182d-3447-5788-87d9-e488ae0af797', '73acb311-dd79-5f5c-bfe8-dc872aace290', '550e8400-e29b-41d4-a716-446655440000', 40, 1.2, 'OUT', 'SAL', '5fffa75d-1230-45ab-9308-281bf8b7a640', true, 1, '2026-03-14 12:50:48');
            

                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('bf186e5a-efda-4a8b-bb4a-69fc433335a8', '9cd9986b-89da-48b7-8733-26a2a1225b01', '536d182d-3447-5788-87d9-e488ae0af797', '73acb311-dd79-5f5c-bfe8-dc872aace290', '550e8400-e29b-41d4-a716-446655440000', 56, 1.5, 'IN', 'ENT', 'cee49c85-33be-4af0-b2e2-78935e723473', true, 1, '2026-03-14 11:50:48');
            

                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('ec138df4-fe8c-4833-b969-dc470eca97c9', '9cd9986b-89da-48b7-8733-26a2a1225b01', '536d182d-3447-5788-87d9-e488ae0af797', '73acb311-dd79-5f5c-bfe8-dc872aace290', '550e8400-e29b-41d4-a716-446655440000', 19, 1.2, 'OUT', 'SAL', '0eb27af2-4c9b-4aa0-a031-a99525b0a8a8', true, 1, '2026-03-14 11:50:48');
            

                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('486a1c89-d91e-486c-aa6a-1bf656d52017', '9cd9986b-89da-48b7-8733-26a2a1225b01', '536d182d-3447-5788-87d9-e488ae0af797', '93acb311-dd79-5f5c-bfe8-dc872aace290', '550e8400-e29b-41d4-a716-446655440000', 51, 1.5, 'IN', 'ENT', 'bdb848fa-3ed8-4fbf-a9e9-622b544855b2', true, 1, '2026-03-14 10:50:48');
            

                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('c825ebd4-d6e7-4d12-902e-e8b264cff48d', '9cd9986b-89da-48b7-8733-26a2a1225b01', '536d182d-3447-5788-87d9-e488ae0af797', '93acb311-dd79-5f5c-bfe8-dc872aace290', '550e8400-e29b-41d4-a716-446655440000', 29, 1.2, 'OUT', 'SAL', 'f0fef21b-6fcf-453b-85fa-86a6012b7bd1', true, 1, '2026-03-14 10:50:48');
            

                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('743864bd-3b06-4e01-bcc0-67de228d1fc9', '9cd9986b-89da-48b7-8733-26a2a1225b01', '536d182d-3447-5788-87d9-e488ae0af797', 'db856803-a63d-5468-9a7c-9039702acca9', '550e8400-e29b-41d4-a716-446655440000', 37, 1.5, 'IN', 'ENT', 'a2a6870a-324e-414d-bd84-cb52d62f6f15', true, 1, '2026-03-14 09:50:48');
            

                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('5d9af0e8-1d6a-492c-aee4-1ce710f16894', '9cd9986b-89da-48b7-8733-26a2a1225b01', '536d182d-3447-5788-87d9-e488ae0af797', 'db856803-a63d-5468-9a7c-9039702acca9', '550e8400-e29b-41d4-a716-446655440000', 30, 1.2, 'OUT', 'SAL', 'a8b7a3a2-64bc-4248-8b4a-bc2c3125b337', true, 1, '2026-03-14 09:50:48');
            

                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('047a904d-9497-4220-83f4-47fd68453e74', '9cd9986b-89da-48b7-8733-26a2a1225b01', '536d182d-3447-5788-87d9-e488ae0af797', '93acb311-dd79-5f5c-bfe8-dc872aace290', '550e8400-e29b-41d4-a716-446655440000', 57, 1.5, 'IN', 'ENT', '613ccb3d-86d7-4a2a-b5a9-291fd55dd4c1', true, 1, '2026-03-14 08:50:48');
            

                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('80a7acfd-cd70-4016-afae-b62303aab773', '9cd9986b-89da-48b7-8733-26a2a1225b01', '536d182d-3447-5788-87d9-e488ae0af797', 'db856803-a63d-5468-9a7c-9039702acca9', '550e8400-e29b-41d4-a716-446655440000', 25, 1.2, 'OUT', 'SAL', 'b404a132-6e89-4691-ae99-97035a5c2bcf', true, 1, '2026-03-14 08:50:48');
            

                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('775ebbc8-8b39-4a77-b538-840530179c26', '9cd9986b-89da-48b7-8733-26a2a1225b01', '536d182d-3447-5788-87d9-e488ae0af797', '93acb311-dd79-5f5c-bfe8-dc872aace290', '550e8400-e29b-41d4-a716-446655440000', 58, 1.5, 'IN', 'ENT', '27d24d9c-3b23-4c52-9acf-96a07336a4c8', true, 1, '2026-03-14 07:50:48');
            

                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('90d5b59e-8e84-4bad-8fe3-fda6c9477c6f', '9cd9986b-89da-48b7-8733-26a2a1225b01', '536d182d-3447-5788-87d9-e488ae0af797', '83acb311-dd79-5f5c-bfe8-dc872aace290', '550e8400-e29b-41d4-a716-446655440000', 9, 1.2, 'OUT', 'SAL', '6b571378-b616-4d20-85f0-163bb688ad81', true, 1, '2026-03-14 07:50:48');
            

                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('c780162b-9144-46d0-9c1c-47383391bff0', '9cd9986b-89da-48b7-8733-26a2a1225b01', '22222222-2222-2222-2222-222222222222', '93acb311-dd79-5f5c-bfe8-dc872aace290', '550e8400-e29b-41d4-a716-446655440000', 59, 1.5, 'IN', 'ENT', '46f54d29-1e76-48b5-a562-e3c31b4129a8', true, 1, '2026-03-15 06:50:48');
            

                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('96c98099-170e-403f-be3a-2252a53c0fa8', '9cd9986b-89da-48b7-8733-26a2a1225b01', '22222222-2222-2222-2222-222222222222', '93acb311-dd79-5f5c-bfe8-dc872aace290', '550e8400-e29b-41d4-a716-446655440000', 47, 1.2, 'OUT', 'SAL', '02f7b832-0aa3-4d7f-ad9e-3cccd15208a8', true, 1, '2026-03-15 06:50:48');
            

                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('cc3b3c0a-7058-4f6a-85ce-fede18e021b4', '9cd9986b-89da-48b7-8733-26a2a1225b01', '22222222-2222-2222-2222-222222222222', 'db856803-a63d-5468-9a7c-9039702acca9', '550e8400-e29b-41d4-a716-446655440000', 16, 1.5, 'IN', 'ENT', '9045f9d5-0a17-4f94-b405-a4e2b649f66f', true, 1, '2026-03-15 05:50:48');
            

                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('403068d8-7d25-4f90-98c6-05dc22a6a457', '9cd9986b-89da-48b7-8733-26a2a1225b01', '22222222-2222-2222-2222-222222222222', '73acb311-dd79-5f5c-bfe8-dc872aace290', '550e8400-e29b-41d4-a716-446655440000', 7, 1.2, 'OUT', 'SAL', '990ffc9e-8f0e-41a9-b739-dcbff4abcfaf', true, 1, '2026-03-15 05:50:48');
            

                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('9ad61945-9528-4a03-88e8-770874751093', '9cd9986b-89da-48b7-8733-26a2a1225b01', '22222222-2222-2222-2222-222222222222', '93acb311-dd79-5f5c-bfe8-dc872aace290', '550e8400-e29b-41d4-a716-446655440000', 12, 1.5, 'IN', 'ENT', '03d2e8b6-8014-41fc-90e1-4608f746ff99', true, 1, '2026-03-15 04:50:48');
            

                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('5efa3e63-3090-432a-83d5-780ce442e6ba', '9cd9986b-89da-48b7-8733-26a2a1225b01', '22222222-2222-2222-2222-222222222222', '73acb311-dd79-5f5c-bfe8-dc872aace290', '550e8400-e29b-41d4-a716-446655440000', 39, 1.2, 'OUT', 'SAL', 'fa4f907a-c6fc-41f5-a18d-f960694ea2ed', true, 1, '2026-03-15 04:50:48');
            

                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('49b1e1a9-a0ed-4caa-acf4-4706d821d861', '9cd9986b-89da-48b7-8733-26a2a1225b01', '22222222-2222-2222-2222-222222222222', 'db856803-a63d-5468-9a7c-9039702acca9', '550e8400-e29b-41d4-a716-446655440000', 34, 1.5, 'IN', 'ENT', 'dbfd6342-62d5-4234-a2cf-6701fdcb4e79', true, 1, '2026-03-15 03:50:48');
            

                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('cf772b7f-51c4-431c-b479-33c1a8119a27', '9cd9986b-89da-48b7-8733-26a2a1225b01', '22222222-2222-2222-2222-222222222222', '93acb311-dd79-5f5c-bfe8-dc872aace290', '550e8400-e29b-41d4-a716-446655440000', 35, 1.2, 'OUT', 'SAL', '2894b618-71be-48d3-8837-e221bca966ff', true, 1, '2026-03-15 03:50:48');
            

                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('c85e711a-8302-4076-926e-65ac15daef00', '9cd9986b-89da-48b7-8733-26a2a1225b01', '22222222-2222-2222-2222-222222222222', '93acb311-dd79-5f5c-bfe8-dc872aace290', '550e8400-e29b-41d4-a716-446655440000', 27, 1.5, 'IN', 'ENT', 'd7478eb3-1799-46a7-8a5b-850c73c01baf', true, 1, '2026-03-15 02:50:48');
            

                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('66bd76e5-69b7-4d4b-8866-f2a81d41ebdd', '9cd9986b-89da-48b7-8733-26a2a1225b01', '22222222-2222-2222-2222-222222222222', '73acb311-dd79-5f5c-bfe8-dc872aace290', '550e8400-e29b-41d4-a716-446655440000', 49, 1.2, 'OUT', 'SAL', '3a33dc6b-c251-4b12-8d25-7af022ec1b0f', true, 1, '2026-03-15 02:50:48');
            

                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('6eb39e7f-e30e-476c-9479-1d0dc68173ac', '9cd9986b-89da-48b7-8733-26a2a1225b01', '22222222-2222-2222-2222-222222222222', '73acb311-dd79-5f5c-bfe8-dc872aace290', '550e8400-e29b-41d4-a716-446655440000', 32, 1.5, 'IN', 'ENT', '99d927c3-e9b3-4fb1-9889-9ff627edb7b8', true, 1, '2026-03-15 01:50:48');
            

                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('9625863d-88f2-4800-a16e-3b430aff08b6', '9cd9986b-89da-48b7-8733-26a2a1225b01', '22222222-2222-2222-2222-222222222222', '93acb311-dd79-5f5c-bfe8-dc872aace290', '550e8400-e29b-41d4-a716-446655440000', 34, 1.2, 'OUT', 'SAL', 'b1bbe95b-c4fc-4c51-92b5-3841fe74ad3b', true, 1, '2026-03-15 01:50:48');
            

                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('484d64f9-02b3-4554-9d17-b4656d59af8b', '9cd9986b-89da-48b7-8733-26a2a1225b01', '22222222-2222-2222-2222-222222222222', '83acb311-dd79-5f5c-bfe8-dc872aace290', '550e8400-e29b-41d4-a716-446655440000', 18, 1.5, 'IN', 'ENT', 'a6d919fe-5a53-4b23-99b9-1566557c0a82', true, 1, '2026-03-15 00:50:48');
            

                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('38293a54-a800-48f7-b78d-dce7890b164b', '9cd9986b-89da-48b7-8733-26a2a1225b01', '22222222-2222-2222-2222-222222222222', '83acb311-dd79-5f5c-bfe8-dc872aace290', '550e8400-e29b-41d4-a716-446655440000', 32, 1.2, 'OUT', 'SAL', '97ef2db7-5dd1-40ea-8ff2-f661bfd93c0b', true, 1, '2026-03-15 00:50:48');
            

                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('0d059348-a3d7-4204-ad42-554fabae3a77', '9cd9986b-89da-48b7-8733-26a2a1225b01', '22222222-2222-2222-2222-222222222222', '83acb311-dd79-5f5c-bfe8-dc872aace290', '550e8400-e29b-41d4-a716-446655440000', 32, 1.5, 'IN', 'ENT', 'c9c5aad1-8d90-43dd-a27d-647655fd6c2d', true, 1, '2026-03-14 23:50:48');
            

                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('57301447-f137-437d-be2d-fdb5dbf7275e', '9cd9986b-89da-48b7-8733-26a2a1225b01', '22222222-2222-2222-2222-222222222222', 'db856803-a63d-5468-9a7c-9039702acca9', '550e8400-e29b-41d4-a716-446655440000', 11, 1.2, 'OUT', 'SAL', 'f8136a42-575d-4b29-8839-6c4662aa7083', true, 1, '2026-03-14 23:50:48');
            

                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('5e4f2b9e-c1df-4617-9fbc-c14dd7a60908', '9cd9986b-89da-48b7-8733-26a2a1225b01', '22222222-2222-2222-2222-222222222222', '93acb311-dd79-5f5c-bfe8-dc872aace290', '550e8400-e29b-41d4-a716-446655440000', 29, 1.5, 'IN', 'ENT', 'fdb7ba3e-767b-4192-a70c-d30e0b41e4fd', true, 1, '2026-03-14 22:50:48');
            

                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('abacf410-c039-433c-ae83-bbf2457204a6', '9cd9986b-89da-48b7-8733-26a2a1225b01', '22222222-2222-2222-2222-222222222222', 'db856803-a63d-5468-9a7c-9039702acca9', '550e8400-e29b-41d4-a716-446655440000', 23, 1.2, 'OUT', 'SAL', '381ce694-a876-4239-bc45-7f0a3266bac7', true, 1, '2026-03-14 22:50:48');
            

                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('21990bb7-0d69-4851-99c3-a2b6fe3cf01b', '9cd9986b-89da-48b7-8733-26a2a1225b01', '22222222-2222-2222-2222-222222222222', '93acb311-dd79-5f5c-bfe8-dc872aace290', '550e8400-e29b-41d4-a716-446655440000', 46, 1.5, 'IN', 'ENT', 'a3e4acb4-af9b-4928-9b50-144a56d167a5', true, 1, '2026-03-14 21:50:48');
            

                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('24621cc4-f54e-4183-83e3-48d75d98aaef', '9cd9986b-89da-48b7-8733-26a2a1225b01', '22222222-2222-2222-2222-222222222222', '83acb311-dd79-5f5c-bfe8-dc872aace290', '550e8400-e29b-41d4-a716-446655440000', 50, 1.2, 'OUT', 'SAL', '68014004-a2a2-48f9-a9d6-a8206d53d6e0', true, 1, '2026-03-14 21:50:48');
            

                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('0d43082d-71fa-4e7a-b4fb-9199a1d401de', '9cd9986b-89da-48b7-8733-26a2a1225b01', '22222222-2222-2222-2222-222222222222', '83acb311-dd79-5f5c-bfe8-dc872aace290', '550e8400-e29b-41d4-a716-446655440000', 47, 1.5, 'IN', 'ENT', '0418a3dc-12a9-4538-8890-f60e154f5b17', true, 1, '2026-03-14 20:50:48');
            

                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('7541ed17-af86-482e-bed8-5751ed86388d', '9cd9986b-89da-48b7-8733-26a2a1225b01', '22222222-2222-2222-2222-222222222222', '73acb311-dd79-5f5c-bfe8-dc872aace290', '550e8400-e29b-41d4-a716-446655440000', 35, 1.2, 'OUT', 'SAL', 'c0867241-0ee1-4395-ba57-12898f52d60a', true, 1, '2026-03-14 20:50:48');
            

                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('6dc5d5da-055b-42d7-81d6-1201630ed748', '9cd9986b-89da-48b7-8733-26a2a1225b01', '22222222-2222-2222-2222-222222222222', '83acb311-dd79-5f5c-bfe8-dc872aace290', '550e8400-e29b-41d4-a716-446655440000', 51, 1.5, 'IN', 'ENT', '2c7c0b11-9001-4bc2-870e-24f73c9f7984', true, 1, '2026-03-14 19:50:48');
            

                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('239c2c65-02c5-4023-9a6b-8016cfffa2bb', '9cd9986b-89da-48b7-8733-26a2a1225b01', '22222222-2222-2222-2222-222222222222', '93acb311-dd79-5f5c-bfe8-dc872aace290', '550e8400-e29b-41d4-a716-446655440000', 6, 1.2, 'OUT', 'SAL', 'd1e126cf-e7d5-44c6-8184-cb88a0e768df', true, 1, '2026-03-14 19:50:48');
            

                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('10d998ad-bbed-4d0a-997b-9e53e1401784', '9cd9986b-89da-48b7-8733-26a2a1225b01', '22222222-2222-2222-2222-222222222222', '83acb311-dd79-5f5c-bfe8-dc872aace290', '550e8400-e29b-41d4-a716-446655440000', 58, 1.5, 'IN', 'ENT', '92937696-ad99-4699-982e-26e29224a3c9', true, 1, '2026-03-14 18:50:48');
            

                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('e7928d68-40ce-4e2f-8fa0-d6bb565a72a2', '9cd9986b-89da-48b7-8733-26a2a1225b01', '22222222-2222-2222-2222-222222222222', '83acb311-dd79-5f5c-bfe8-dc872aace290', '550e8400-e29b-41d4-a716-446655440000', 16, 1.2, 'OUT', 'SAL', 'a3026a8f-754d-439d-ad3a-00cf61c1dce0', true, 1, '2026-03-14 18:50:48');
            

                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('c2ba07bc-cd59-4c3a-8b55-af3f2f5d57a8', '9cd9986b-89da-48b7-8733-26a2a1225b01', '22222222-2222-2222-2222-222222222222', '83acb311-dd79-5f5c-bfe8-dc872aace290', '550e8400-e29b-41d4-a716-446655440000', 48, 1.5, 'IN', 'ENT', '6441ec28-da06-409f-99f6-f72a70904399', true, 1, '2026-03-14 17:50:48');
            

                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('69ba645b-5176-4f4b-b17a-272d716fa5cb', '9cd9986b-89da-48b7-8733-26a2a1225b01', '22222222-2222-2222-2222-222222222222', '93acb311-dd79-5f5c-bfe8-dc872aace290', '550e8400-e29b-41d4-a716-446655440000', 21, 1.2, 'OUT', 'SAL', '7f407340-6163-4e32-a61d-0d5166fcc885', true, 1, '2026-03-14 17:50:48');
            

                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('b5556324-8254-49f0-afaa-5689142228cf', '9cd9986b-89da-48b7-8733-26a2a1225b01', '22222222-2222-2222-2222-222222222222', 'db856803-a63d-5468-9a7c-9039702acca9', '550e8400-e29b-41d4-a716-446655440000', 12, 1.5, 'IN', 'ENT', 'c987041e-e5dc-4907-9c5f-54e97be65349', true, 1, '2026-03-14 16:50:48');
            

                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('154a39a0-d35b-42c3-a56d-d9aaab910412', '9cd9986b-89da-48b7-8733-26a2a1225b01', '22222222-2222-2222-2222-222222222222', 'db856803-a63d-5468-9a7c-9039702acca9', '550e8400-e29b-41d4-a716-446655440000', 35, 1.2, 'OUT', 'SAL', '24e6ceb8-7dc5-4e2b-bdab-b893474cc40b', true, 1, '2026-03-14 16:50:48');
            

                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('379a2554-6928-48e6-b062-eb6dabf85fbd', '9cd9986b-89da-48b7-8733-26a2a1225b01', '22222222-2222-2222-2222-222222222222', 'db856803-a63d-5468-9a7c-9039702acca9', '550e8400-e29b-41d4-a716-446655440000', 12, 1.5, 'IN', 'ENT', '5d29f85e-c06e-4699-881c-48eb1a03e06e', true, 1, '2026-03-14 15:50:48');
            

                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('1083d8de-2246-407e-a25c-506bfa800f69', '9cd9986b-89da-48b7-8733-26a2a1225b01', '22222222-2222-2222-2222-222222222222', '73acb311-dd79-5f5c-bfe8-dc872aace290', '550e8400-e29b-41d4-a716-446655440000', 21, 1.2, 'OUT', 'SAL', '3d77d57f-d6cc-47c0-a284-b97c9f9b9fdf', true, 1, '2026-03-14 15:50:48');
            

                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('f5014a5d-4582-4443-9e07-320375263d17', '9cd9986b-89da-48b7-8733-26a2a1225b01', '22222222-2222-2222-2222-222222222222', '73acb311-dd79-5f5c-bfe8-dc872aace290', '550e8400-e29b-41d4-a716-446655440000', 22, 1.5, 'IN', 'ENT', 'b19d8956-59ab-4a45-a9f3-b9ff4aa27912', true, 1, '2026-03-14 14:50:48');
            

                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('c1980b67-282e-4fcb-b181-99fe3a2d05a7', '9cd9986b-89da-48b7-8733-26a2a1225b01', '22222222-2222-2222-2222-222222222222', '73acb311-dd79-5f5c-bfe8-dc872aace290', '550e8400-e29b-41d4-a716-446655440000', 23, 1.2, 'OUT', 'SAL', '51fb54b3-3ff9-4801-b461-09d0d5156026', true, 1, '2026-03-14 14:50:48');
            

                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('49f482f3-3438-4305-8e5e-ee23ed343a66', '9cd9986b-89da-48b7-8733-26a2a1225b01', '22222222-2222-2222-2222-222222222222', 'db856803-a63d-5468-9a7c-9039702acca9', '550e8400-e29b-41d4-a716-446655440000', 12, 1.5, 'IN', 'ENT', 'eda2b477-1f44-4bf4-be1c-619647d9967c', true, 1, '2026-03-14 13:50:48');
            

                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('f49a6eae-11c2-421a-89ea-504cfcf75a92', '9cd9986b-89da-48b7-8733-26a2a1225b01', '22222222-2222-2222-2222-222222222222', '83acb311-dd79-5f5c-bfe8-dc872aace290', '550e8400-e29b-41d4-a716-446655440000', 32, 1.2, 'OUT', 'SAL', 'c1b1f2b1-aa9b-4f5f-94ae-b62970637753', true, 1, '2026-03-14 13:50:48');
            

                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('b960b30f-9dc7-414f-be48-7c9cf6286d49', '9cd9986b-89da-48b7-8733-26a2a1225b01', '22222222-2222-2222-2222-222222222222', '93acb311-dd79-5f5c-bfe8-dc872aace290', '550e8400-e29b-41d4-a716-446655440000', 19, 1.5, 'IN', 'ENT', '445915c3-3ac8-4bb2-9c31-350acabff5d1', true, 1, '2026-03-14 12:50:48');
            

                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('33fb7289-fea2-4605-8a75-a0ebc535c234', '9cd9986b-89da-48b7-8733-26a2a1225b01', '22222222-2222-2222-2222-222222222222', 'db856803-a63d-5468-9a7c-9039702acca9', '550e8400-e29b-41d4-a716-446655440000', 6, 1.2, 'OUT', 'SAL', '46d68733-4498-45e3-8dcd-b3aca6f04966', true, 1, '2026-03-14 12:50:48');
            

                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('2fac64e5-fb9a-4b87-8661-92300be90413', '9cd9986b-89da-48b7-8733-26a2a1225b01', '22222222-2222-2222-2222-222222222222', '83acb311-dd79-5f5c-bfe8-dc872aace290', '550e8400-e29b-41d4-a716-446655440000', 56, 1.5, 'IN', 'ENT', 'd56c11c8-44cd-4760-94d9-9877c8f0dd6d', true, 1, '2026-03-14 11:50:48');
            

                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('ad11aa15-7226-4822-bbef-f2d8c102ad19', '9cd9986b-89da-48b7-8733-26a2a1225b01', '22222222-2222-2222-2222-222222222222', '73acb311-dd79-5f5c-bfe8-dc872aace290', '550e8400-e29b-41d4-a716-446655440000', 31, 1.2, 'OUT', 'SAL', '95e68737-a882-4557-a52a-8b180e426745', true, 1, '2026-03-14 11:50:48');
            

                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('94aa4679-fd53-45c7-9338-727ee070abdc', '9cd9986b-89da-48b7-8733-26a2a1225b01', '22222222-2222-2222-2222-222222222222', '83acb311-dd79-5f5c-bfe8-dc872aace290', '550e8400-e29b-41d4-a716-446655440000', 37, 1.5, 'IN', 'ENT', 'be02122d-5547-4747-86bd-9323e3a1c57d', true, 1, '2026-03-14 10:50:48');
            

                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('8fb03a08-ccbc-492f-a18c-f2f02248c200', '9cd9986b-89da-48b7-8733-26a2a1225b01', '22222222-2222-2222-2222-222222222222', '73acb311-dd79-5f5c-bfe8-dc872aace290', '550e8400-e29b-41d4-a716-446655440000', 16, 1.2, 'OUT', 'SAL', 'b4c6e4e3-4cb7-495a-b0cf-42a9fe0963a6', true, 1, '2026-03-14 10:50:48');
            

                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('dec45f29-cf5e-4121-afeb-fa9e4e71454d', '9cd9986b-89da-48b7-8733-26a2a1225b01', '22222222-2222-2222-2222-222222222222', '93acb311-dd79-5f5c-bfe8-dc872aace290', '550e8400-e29b-41d4-a716-446655440000', 49, 1.5, 'IN', 'ENT', '5b1ee582-be1d-4713-b48a-a00b855c8eb7', true, 1, '2026-03-14 09:50:48');
            

                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('b7e3ed35-ce69-4b14-9c31-5849d681af20', '9cd9986b-89da-48b7-8733-26a2a1225b01', '22222222-2222-2222-2222-222222222222', 'db856803-a63d-5468-9a7c-9039702acca9', '550e8400-e29b-41d4-a716-446655440000', 34, 1.2, 'OUT', 'SAL', 'c665b04d-dcbe-4f30-beed-709de33c0e01', true, 1, '2026-03-14 09:50:48');
            

                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('87e70822-8f7f-4c0b-924a-9317a8af9e4f', '9cd9986b-89da-48b7-8733-26a2a1225b01', '22222222-2222-2222-2222-222222222222', '73acb311-dd79-5f5c-bfe8-dc872aace290', '550e8400-e29b-41d4-a716-446655440000', 14, 1.5, 'IN', 'ENT', 'dca00bb3-f3d4-4233-a47f-49498d4c4946', true, 1, '2026-03-14 08:50:48');
            

                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('a103adb3-b141-442a-87a0-5245743b86ce', '9cd9986b-89da-48b7-8733-26a2a1225b01', '22222222-2222-2222-2222-222222222222', '93acb311-dd79-5f5c-bfe8-dc872aace290', '550e8400-e29b-41d4-a716-446655440000', 43, 1.2, 'OUT', 'SAL', '4fca7948-644c-4ef0-b91c-a53885a99d19', true, 1, '2026-03-14 08:50:48');
            

                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('170dcd9c-413b-42ee-9139-5e12c10b9e46', '9cd9986b-89da-48b7-8733-26a2a1225b01', '22222222-2222-2222-2222-222222222222', '73acb311-dd79-5f5c-bfe8-dc872aace290', '550e8400-e29b-41d4-a716-446655440000', 53, 1.5, 'IN', 'ENT', '21785263-1400-40c8-b9fb-8a0fe5e176bc', true, 1, '2026-03-14 07:50:48');
            

                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('066b2717-27b8-4607-8f6c-cd4ded1f4484', '9cd9986b-89da-48b7-8733-26a2a1225b01', '22222222-2222-2222-2222-222222222222', '73acb311-dd79-5f5c-bfe8-dc872aace290', '550e8400-e29b-41d4-a716-446655440000', 9, 1.2, 'OUT', 'SAL', 'f4d085d5-540c-443b-95ed-759bd5ed4a6c', true, 1, '2026-03-14 07:50:48');
            

                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('dada3843-09f0-4d4b-8a89-f3fe605e86db', '9cd9986b-89da-48b7-8733-26a2a1225b01', 'bb18f763-3f93-53af-9fb8-ca1c752f3873', '73acb311-dd79-5f5c-bfe8-dc872aace290', '550e8400-e29b-41d4-a716-446655440000', 20, 1.5, 'IN', 'ENT', '77c6f710-00dd-4766-bec4-d7067b640c08', true, 1, '2026-03-15 06:50:48');
            

                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('ba4c62e7-1375-4753-b118-f502815ca043', '9cd9986b-89da-48b7-8733-26a2a1225b01', 'bb18f763-3f93-53af-9fb8-ca1c752f3873', 'db856803-a63d-5468-9a7c-9039702acca9', '550e8400-e29b-41d4-a716-446655440000', 29, 1.2, 'OUT', 'SAL', 'f70f4651-88a9-48a7-ad54-4f2255da72c9', true, 1, '2026-03-15 06:50:48');
            

                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('7c8876f7-5b4d-4efa-ac78-3f47ba7593af', '9cd9986b-89da-48b7-8733-26a2a1225b01', 'bb18f763-3f93-53af-9fb8-ca1c752f3873', '83acb311-dd79-5f5c-bfe8-dc872aace290', '550e8400-e29b-41d4-a716-446655440000', 58, 1.5, 'IN', 'ENT', '167d8217-2335-431b-971c-94ac1487b387', true, 1, '2026-03-15 05:50:48');
            

                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('759276f5-cfe5-42aa-8524-0ebd491cc0d2', '9cd9986b-89da-48b7-8733-26a2a1225b01', 'bb18f763-3f93-53af-9fb8-ca1c752f3873', '73acb311-dd79-5f5c-bfe8-dc872aace290', '550e8400-e29b-41d4-a716-446655440000', 24, 1.2, 'OUT', 'SAL', '0e103a4f-0ad8-42e4-9e7c-87bc61267bd2', true, 1, '2026-03-15 05:50:48');
            

                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('9d54111d-6b0f-435f-a6d3-b2d166f9179d', '9cd9986b-89da-48b7-8733-26a2a1225b01', 'bb18f763-3f93-53af-9fb8-ca1c752f3873', 'db856803-a63d-5468-9a7c-9039702acca9', '550e8400-e29b-41d4-a716-446655440000', 22, 1.5, 'IN', 'ENT', '9ba59f1e-81bf-4a9b-9b2d-f3500030bed3', true, 1, '2026-03-15 04:50:48');
            

                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('bdeb6d27-9b90-4fee-8782-b7782ee3d5b7', '9cd9986b-89da-48b7-8733-26a2a1225b01', 'bb18f763-3f93-53af-9fb8-ca1c752f3873', '83acb311-dd79-5f5c-bfe8-dc872aace290', '550e8400-e29b-41d4-a716-446655440000', 23, 1.2, 'OUT', 'SAL', 'b50e79a4-5716-4053-910b-b6527c6bd959', true, 1, '2026-03-15 04:50:48');
            

                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('fc3a0f9e-3f37-408f-82d5-7701b8e3415a', '9cd9986b-89da-48b7-8733-26a2a1225b01', 'bb18f763-3f93-53af-9fb8-ca1c752f3873', '93acb311-dd79-5f5c-bfe8-dc872aace290', '550e8400-e29b-41d4-a716-446655440000', 54, 1.5, 'IN', 'ENT', '12feffe8-64cf-4f5c-8861-545380d4b0b3', true, 1, '2026-03-15 03:50:48');
            

                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('7a3bd015-7b82-4031-956b-485cc261d1db', '9cd9986b-89da-48b7-8733-26a2a1225b01', 'bb18f763-3f93-53af-9fb8-ca1c752f3873', '93acb311-dd79-5f5c-bfe8-dc872aace290', '550e8400-e29b-41d4-a716-446655440000', 7, 1.2, 'OUT', 'SAL', '01382dca-510c-4cc9-9ac9-ad48b9879f9b', true, 1, '2026-03-15 03:50:48');
            

                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('08055214-0e4c-4c50-bbaf-ef9e64706c5f', '9cd9986b-89da-48b7-8733-26a2a1225b01', 'bb18f763-3f93-53af-9fb8-ca1c752f3873', 'db856803-a63d-5468-9a7c-9039702acca9', '550e8400-e29b-41d4-a716-446655440000', 46, 1.5, 'IN', 'ENT', 'b99679d2-d44d-44c8-88f1-a35f49655586', true, 1, '2026-03-15 02:50:48');
            

                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('a0d8cbcb-0cb1-450d-bb80-8f9adf41ddfc', '9cd9986b-89da-48b7-8733-26a2a1225b01', 'bb18f763-3f93-53af-9fb8-ca1c752f3873', '83acb311-dd79-5f5c-bfe8-dc872aace290', '550e8400-e29b-41d4-a716-446655440000', 15, 1.2, 'OUT', 'SAL', '7548e0a5-07c7-4fd2-9268-09b784fe89e7', true, 1, '2026-03-15 02:50:48');
            

                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('49e3f6b4-bf83-494f-bf96-7b7b238069cb', '9cd9986b-89da-48b7-8733-26a2a1225b01', 'bb18f763-3f93-53af-9fb8-ca1c752f3873', 'db856803-a63d-5468-9a7c-9039702acca9', '550e8400-e29b-41d4-a716-446655440000', 35, 1.5, 'IN', 'ENT', '19098197-5d7a-4222-b4f2-ff3f2c5c679f', true, 1, '2026-03-15 01:50:48');
            

                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('df9da9b1-c9f0-433e-af00-542eb0c27ee1', '9cd9986b-89da-48b7-8733-26a2a1225b01', 'bb18f763-3f93-53af-9fb8-ca1c752f3873', 'db856803-a63d-5468-9a7c-9039702acca9', '550e8400-e29b-41d4-a716-446655440000', 8, 1.2, 'OUT', 'SAL', '4d2843ed-4c18-4ce4-a475-498485d285c9', true, 1, '2026-03-15 01:50:48');
            

                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('073c2832-3606-4574-a88c-b8ac0baefa4f', '9cd9986b-89da-48b7-8733-26a2a1225b01', 'bb18f763-3f93-53af-9fb8-ca1c752f3873', '73acb311-dd79-5f5c-bfe8-dc872aace290', '550e8400-e29b-41d4-a716-446655440000', 27, 1.5, 'IN', 'ENT', 'a71619cb-1d97-481f-ae6a-86a3eeb20ee1', true, 1, '2026-03-15 00:50:48');
            

                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('43bf95a7-54ca-4ece-95bc-7abc29ff60b0', '9cd9986b-89da-48b7-8733-26a2a1225b01', 'bb18f763-3f93-53af-9fb8-ca1c752f3873', '93acb311-dd79-5f5c-bfe8-dc872aace290', '550e8400-e29b-41d4-a716-446655440000', 38, 1.2, 'OUT', 'SAL', '95f77b60-4ace-4e92-9793-aad526662764', true, 1, '2026-03-15 00:50:48');
            

                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('9146bd2f-5706-463b-98a0-3d86a95d2026', '9cd9986b-89da-48b7-8733-26a2a1225b01', 'bb18f763-3f93-53af-9fb8-ca1c752f3873', '73acb311-dd79-5f5c-bfe8-dc872aace290', '550e8400-e29b-41d4-a716-446655440000', 60, 1.5, 'IN', 'ENT', '9861a36d-14c8-4119-8efd-cdc58b88cc3d', true, 1, '2026-03-14 23:50:48');
            

                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('6d66ed3e-3967-4daf-84b7-ce17d1847945', '9cd9986b-89da-48b7-8733-26a2a1225b01', 'bb18f763-3f93-53af-9fb8-ca1c752f3873', '93acb311-dd79-5f5c-bfe8-dc872aace290', '550e8400-e29b-41d4-a716-446655440000', 36, 1.2, 'OUT', 'SAL', '06f5f667-ac98-40c1-b577-9ec76c054e9e', true, 1, '2026-03-14 23:50:48');
            

                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('9d3d0d11-c26b-4cae-80c8-03e7ee3a2150', '9cd9986b-89da-48b7-8733-26a2a1225b01', 'bb18f763-3f93-53af-9fb8-ca1c752f3873', 'db856803-a63d-5468-9a7c-9039702acca9', '550e8400-e29b-41d4-a716-446655440000', 43, 1.5, 'IN', 'ENT', 'dd1f917c-1782-4a38-bea7-09b1732d10c0', true, 1, '2026-03-14 22:50:48');
            

                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('591dc461-7f50-4569-ae0b-496184a24515', '9cd9986b-89da-48b7-8733-26a2a1225b01', 'bb18f763-3f93-53af-9fb8-ca1c752f3873', 'db856803-a63d-5468-9a7c-9039702acca9', '550e8400-e29b-41d4-a716-446655440000', 5, 1.2, 'OUT', 'SAL', 'bc274c4d-1ea7-4b99-97ca-e5c4ef0e0c97', true, 1, '2026-03-14 22:50:48');
            

                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('38e60c5e-e188-4c72-b32b-33d9cfef6486', '9cd9986b-89da-48b7-8733-26a2a1225b01', 'bb18f763-3f93-53af-9fb8-ca1c752f3873', '73acb311-dd79-5f5c-bfe8-dc872aace290', '550e8400-e29b-41d4-a716-446655440000', 24, 1.5, 'IN', 'ENT', 'bb024b80-81a9-457e-9bf1-2a3127082ccc', true, 1, '2026-03-14 21:50:48');
            

                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('f7f4c074-e962-4ad9-8088-9cfea11cf412', '9cd9986b-89da-48b7-8733-26a2a1225b01', 'bb18f763-3f93-53af-9fb8-ca1c752f3873', '93acb311-dd79-5f5c-bfe8-dc872aace290', '550e8400-e29b-41d4-a716-446655440000', 36, 1.2, 'OUT', 'SAL', '37d28c79-9b7a-4751-960b-02413bf62770', true, 1, '2026-03-14 21:50:48');
            

                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('49b6b85b-8558-4834-b2ba-439c25cee6a2', '9cd9986b-89da-48b7-8733-26a2a1225b01', 'bb18f763-3f93-53af-9fb8-ca1c752f3873', '93acb311-dd79-5f5c-bfe8-dc872aace290', '550e8400-e29b-41d4-a716-446655440000', 33, 1.5, 'IN', 'ENT', 'ae025001-1b9d-4dff-a97f-8e3b1ccad6e5', true, 1, '2026-03-14 20:50:48');
            

                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('73e62320-d7cb-42b6-ab82-eab0ab42106e', '9cd9986b-89da-48b7-8733-26a2a1225b01', 'bb18f763-3f93-53af-9fb8-ca1c752f3873', '93acb311-dd79-5f5c-bfe8-dc872aace290', '550e8400-e29b-41d4-a716-446655440000', 38, 1.2, 'OUT', 'SAL', '05f184d9-8b22-4466-b3b1-91f93f37c2be', true, 1, '2026-03-14 20:50:48');
            

                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('067954cc-9976-4059-b3fd-f866c6265dcd', '9cd9986b-89da-48b7-8733-26a2a1225b01', 'bb18f763-3f93-53af-9fb8-ca1c752f3873', '93acb311-dd79-5f5c-bfe8-dc872aace290', '550e8400-e29b-41d4-a716-446655440000', 51, 1.5, 'IN', 'ENT', '0bb21d22-bfd6-456e-aa59-0c9c3139c853', true, 1, '2026-03-14 19:50:48');
            

                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('3ea429b7-4d12-4bd3-a03a-faeeee1f3a1e', '9cd9986b-89da-48b7-8733-26a2a1225b01', 'bb18f763-3f93-53af-9fb8-ca1c752f3873', '93acb311-dd79-5f5c-bfe8-dc872aace290', '550e8400-e29b-41d4-a716-446655440000', 22, 1.2, 'OUT', 'SAL', '452d6b33-f51b-4441-bfb7-e84c14208397', true, 1, '2026-03-14 19:50:48');
            

                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('d0849738-7b4e-4ac4-a122-45e8f7f3a910', '9cd9986b-89da-48b7-8733-26a2a1225b01', 'bb18f763-3f93-53af-9fb8-ca1c752f3873', 'db856803-a63d-5468-9a7c-9039702acca9', '550e8400-e29b-41d4-a716-446655440000', 17, 1.5, 'IN', 'ENT', '0eb75f2a-2e0f-4742-8fca-82b278fdb20b', true, 1, '2026-03-14 18:50:48');
            

                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('4cc36ed1-4b68-4af5-8cb1-bc6ffd57c45f', '9cd9986b-89da-48b7-8733-26a2a1225b01', 'bb18f763-3f93-53af-9fb8-ca1c752f3873', 'db856803-a63d-5468-9a7c-9039702acca9', '550e8400-e29b-41d4-a716-446655440000', 44, 1.2, 'OUT', 'SAL', '9ada884a-0332-4bf2-99ed-7325c236f996', true, 1, '2026-03-14 18:50:48');
            

                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('f79bd0f6-7fa2-4e62-a328-3fb2adbd7493', '9cd9986b-89da-48b7-8733-26a2a1225b01', 'bb18f763-3f93-53af-9fb8-ca1c752f3873', 'db856803-a63d-5468-9a7c-9039702acca9', '550e8400-e29b-41d4-a716-446655440000', 58, 1.5, 'IN', 'ENT', '745a9e6e-f7ad-4dfa-8a94-9f8971398667', true, 1, '2026-03-14 17:50:48');
            

                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('6cb5bf12-320b-4150-b23b-5add10dfe9b8', '9cd9986b-89da-48b7-8733-26a2a1225b01', 'bb18f763-3f93-53af-9fb8-ca1c752f3873', 'db856803-a63d-5468-9a7c-9039702acca9', '550e8400-e29b-41d4-a716-446655440000', 9, 1.2, 'OUT', 'SAL', '9998c2a7-2986-4ad0-91d5-dcc80e2df487', true, 1, '2026-03-14 17:50:48');
            

                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('1e4a3016-a691-4a5b-b6ea-c3b019f8ed4f', '9cd9986b-89da-48b7-8733-26a2a1225b01', 'bb18f763-3f93-53af-9fb8-ca1c752f3873', '73acb311-dd79-5f5c-bfe8-dc872aace290', '550e8400-e29b-41d4-a716-446655440000', 48, 1.5, 'IN', 'ENT', '39e7f086-731a-4bb4-80e8-e2f2ab1ea877', true, 1, '2026-03-14 16:50:48');
            

                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('7e302fe9-2bee-4ace-a414-6acf127c96ea', '9cd9986b-89da-48b7-8733-26a2a1225b01', 'bb18f763-3f93-53af-9fb8-ca1c752f3873', '73acb311-dd79-5f5c-bfe8-dc872aace290', '550e8400-e29b-41d4-a716-446655440000', 14, 1.2, 'OUT', 'SAL', 'bbd2b7b6-a354-4c35-b80c-8a489db8eec0', true, 1, '2026-03-14 16:50:48');
            

                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('60bdc8fd-610e-40eb-b9d9-498075813119', '9cd9986b-89da-48b7-8733-26a2a1225b01', 'bb18f763-3f93-53af-9fb8-ca1c752f3873', 'db856803-a63d-5468-9a7c-9039702acca9', '550e8400-e29b-41d4-a716-446655440000', 15, 1.5, 'IN', 'ENT', '5e24068b-ace4-42c9-860f-7b285e3309ed', true, 1, '2026-03-14 15:50:48');
            

                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('3a3eab1e-6241-4278-980c-49cc9993cad6', '9cd9986b-89da-48b7-8733-26a2a1225b01', 'bb18f763-3f93-53af-9fb8-ca1c752f3873', 'db856803-a63d-5468-9a7c-9039702acca9', '550e8400-e29b-41d4-a716-446655440000', 5, 1.2, 'OUT', 'SAL', 'ae995e2f-aa92-4874-ad97-4101b7805938', true, 1, '2026-03-14 15:50:48');
            

                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('89ee5607-020c-482b-8da0-f689cee66908', '9cd9986b-89da-48b7-8733-26a2a1225b01', 'bb18f763-3f93-53af-9fb8-ca1c752f3873', '93acb311-dd79-5f5c-bfe8-dc872aace290', '550e8400-e29b-41d4-a716-446655440000', 49, 1.5, 'IN', 'ENT', 'ffe1e58c-58fb-4da4-9d82-7fae972e4433', true, 1, '2026-03-14 14:50:48');
            

                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('28a4dca9-757a-4b1e-8369-1926d751ac93', '9cd9986b-89da-48b7-8733-26a2a1225b01', 'bb18f763-3f93-53af-9fb8-ca1c752f3873', '93acb311-dd79-5f5c-bfe8-dc872aace290', '550e8400-e29b-41d4-a716-446655440000', 48, 1.2, 'OUT', 'SAL', '6ca454ec-c238-4687-8256-d91193f390f3', true, 1, '2026-03-14 14:50:48');
            

                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('efc61837-b068-4f56-823a-4a0818c2f14e', '9cd9986b-89da-48b7-8733-26a2a1225b01', 'bb18f763-3f93-53af-9fb8-ca1c752f3873', '73acb311-dd79-5f5c-bfe8-dc872aace290', '550e8400-e29b-41d4-a716-446655440000', 16, 1.5, 'IN', 'ENT', '89824931-80f5-4d81-8273-2254a93d55f3', true, 1, '2026-03-14 13:50:48');
            

                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('5edd797a-6d20-4504-864d-f58457bcd123', '9cd9986b-89da-48b7-8733-26a2a1225b01', 'bb18f763-3f93-53af-9fb8-ca1c752f3873', '93acb311-dd79-5f5c-bfe8-dc872aace290', '550e8400-e29b-41d4-a716-446655440000', 16, 1.2, 'OUT', 'SAL', 'fed29f95-f3a5-4d12-9879-a94659b7d1c8', true, 1, '2026-03-14 13:50:48');
            

                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('e30fd3e6-e386-4cec-8107-3d24eb5fc800', '9cd9986b-89da-48b7-8733-26a2a1225b01', 'bb18f763-3f93-53af-9fb8-ca1c752f3873', '73acb311-dd79-5f5c-bfe8-dc872aace290', '550e8400-e29b-41d4-a716-446655440000', 29, 1.5, 'IN', 'ENT', '4e0e59c8-e75a-487e-82c8-e13b4925ebae', true, 1, '2026-03-14 12:50:48');
            

                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('7468627c-3e28-4ecf-9b76-c0d01da4d9e0', '9cd9986b-89da-48b7-8733-26a2a1225b01', 'bb18f763-3f93-53af-9fb8-ca1c752f3873', '83acb311-dd79-5f5c-bfe8-dc872aace290', '550e8400-e29b-41d4-a716-446655440000', 22, 1.2, 'OUT', 'SAL', '9d45b605-7d49-4c99-80d3-f409ea4afe98', true, 1, '2026-03-14 12:50:48');
            

                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('1a8c6b70-3675-4a00-b05d-48fe756ea8cd', '9cd9986b-89da-48b7-8733-26a2a1225b01', 'bb18f763-3f93-53af-9fb8-ca1c752f3873', '83acb311-dd79-5f5c-bfe8-dc872aace290', '550e8400-e29b-41d4-a716-446655440000', 23, 1.5, 'IN', 'ENT', '99ce6fd2-df30-499b-8fca-525dd7a3798f', true, 1, '2026-03-14 11:50:48');
            

                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('232b0a2a-15f8-4bf1-95b7-267a90bd978a', '9cd9986b-89da-48b7-8733-26a2a1225b01', 'bb18f763-3f93-53af-9fb8-ca1c752f3873', 'db856803-a63d-5468-9a7c-9039702acca9', '550e8400-e29b-41d4-a716-446655440000', 42, 1.2, 'OUT', 'SAL', '9da36c67-3038-48d1-845c-a5530f913fef', true, 1, '2026-03-14 11:50:48');
            

                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('23c26ac5-c3d9-4334-a376-eca734019ce1', '9cd9986b-89da-48b7-8733-26a2a1225b01', 'bb18f763-3f93-53af-9fb8-ca1c752f3873', 'db856803-a63d-5468-9a7c-9039702acca9', '550e8400-e29b-41d4-a716-446655440000', 39, 1.5, 'IN', 'ENT', '6303fee4-32f8-4f19-be8b-3eddd737f13c', true, 1, '2026-03-14 10:50:48');
            

                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('7b0f300f-104a-4055-8b03-42d5c54626e4', '9cd9986b-89da-48b7-8733-26a2a1225b01', 'bb18f763-3f93-53af-9fb8-ca1c752f3873', '93acb311-dd79-5f5c-bfe8-dc872aace290', '550e8400-e29b-41d4-a716-446655440000', 46, 1.2, 'OUT', 'SAL', '16160a2c-e3c6-499d-887b-bcb2dd988dce', true, 1, '2026-03-14 10:50:48');
            

                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('dd2c97ad-83d5-4f67-8b96-3ddfe678408a', '9cd9986b-89da-48b7-8733-26a2a1225b01', 'bb18f763-3f93-53af-9fb8-ca1c752f3873', 'db856803-a63d-5468-9a7c-9039702acca9', '550e8400-e29b-41d4-a716-446655440000', 34, 1.5, 'IN', 'ENT', '35208a6d-93d5-49b9-8e15-3c0dd1d81663', true, 1, '2026-03-14 09:50:48');
            

                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('1bc9e436-9ad5-448d-979b-1ac8cfa0698c', '9cd9986b-89da-48b7-8733-26a2a1225b01', 'bb18f763-3f93-53af-9fb8-ca1c752f3873', 'db856803-a63d-5468-9a7c-9039702acca9', '550e8400-e29b-41d4-a716-446655440000', 7, 1.2, 'OUT', 'SAL', '3f5ca563-194c-406f-9788-a8da45d90559', true, 1, '2026-03-14 09:50:48');
            

                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('f11d3029-40b2-4679-881c-7b20b479c124', '9cd9986b-89da-48b7-8733-26a2a1225b01', 'bb18f763-3f93-53af-9fb8-ca1c752f3873', '93acb311-dd79-5f5c-bfe8-dc872aace290', '550e8400-e29b-41d4-a716-446655440000', 51, 1.5, 'IN', 'ENT', '83ff8e99-1a20-4afa-be69-f9854ba0d787', true, 1, '2026-03-14 08:50:48');
            

                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('e422f35d-7563-4a03-b614-add6d0593ecf', '9cd9986b-89da-48b7-8733-26a2a1225b01', 'bb18f763-3f93-53af-9fb8-ca1c752f3873', '93acb311-dd79-5f5c-bfe8-dc872aace290', '550e8400-e29b-41d4-a716-446655440000', 16, 1.2, 'OUT', 'SAL', '3ee1d100-605a-48b6-8419-2e61bfaa07ab', true, 1, '2026-03-14 08:50:48');
            

                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('f45f8d8d-f273-4faa-bfb9-2113ccd329ae', '9cd9986b-89da-48b7-8733-26a2a1225b01', 'bb18f763-3f93-53af-9fb8-ca1c752f3873', 'db856803-a63d-5468-9a7c-9039702acca9', '550e8400-e29b-41d4-a716-446655440000', 51, 1.5, 'IN', 'ENT', '62f964ce-8503-48ac-aa2a-0447c36e3ae8', true, 1, '2026-03-14 07:50:48');
            

                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('d4e1336c-66e7-4b47-a82f-f6d923425c46', '9cd9986b-89da-48b7-8733-26a2a1225b01', 'bb18f763-3f93-53af-9fb8-ca1c752f3873', '93acb311-dd79-5f5c-bfe8-dc872aace290', '550e8400-e29b-41d4-a716-446655440000', 40, 1.2, 'OUT', 'SAL', 'bdab356d-8caf-4995-9760-f949d6ca6466', true, 1, '2026-03-14 07:50:48');
            

                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('fe3ff67a-7bc7-463b-80ca-78f7d5425bf0', '9cd9986b-89da-48b7-8733-26a2a1225b01', '33333333-3333-3333-3333-333333333333', 'db856803-a63d-5468-9a7c-9039702acca9', '550e8400-e29b-41d4-a716-446655440000', 41, 1.5, 'IN', 'ENT', '35a58e62-6f33-45ca-9ed6-f3b143994418', true, 1, '2026-03-15 06:50:48');
            

                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('29a30373-7b86-4d0b-b3bc-a2b1d43e00f3', '9cd9986b-89da-48b7-8733-26a2a1225b01', '33333333-3333-3333-3333-333333333333', '83acb311-dd79-5f5c-bfe8-dc872aace290', '550e8400-e29b-41d4-a716-446655440000', 23, 1.2, 'OUT', 'SAL', 'b61ec53d-135a-41e2-8e85-34afd8b8d9f0', true, 1, '2026-03-15 06:50:48');
            

                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('f89ef5c7-2e07-478d-a8b9-93e8c42a2a15', '9cd9986b-89da-48b7-8733-26a2a1225b01', '33333333-3333-3333-3333-333333333333', '83acb311-dd79-5f5c-bfe8-dc872aace290', '550e8400-e29b-41d4-a716-446655440000', 60, 1.5, 'IN', 'ENT', 'd7225ab8-719c-464f-939b-3bbbe8105197', true, 1, '2026-03-15 05:50:48');
            

                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('57302155-6b96-4add-9f48-065400b1d79e', '9cd9986b-89da-48b7-8733-26a2a1225b01', '33333333-3333-3333-3333-333333333333', 'db856803-a63d-5468-9a7c-9039702acca9', '550e8400-e29b-41d4-a716-446655440000', 15, 1.2, 'OUT', 'SAL', '281afd22-c921-43b4-aa5a-903d8faeab4e', true, 1, '2026-03-15 05:50:48');
            

                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('6b674ab0-a60e-41e4-96a5-a07b4f4bb2e1', '9cd9986b-89da-48b7-8733-26a2a1225b01', '33333333-3333-3333-3333-333333333333', '83acb311-dd79-5f5c-bfe8-dc872aace290', '550e8400-e29b-41d4-a716-446655440000', 35, 1.5, 'IN', 'ENT', '774742b8-8047-4022-8ded-23dfeb941a7a', true, 1, '2026-03-15 04:50:48');
            

                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('a0e6c229-c01f-49c0-ac46-5e92731aad14', '9cd9986b-89da-48b7-8733-26a2a1225b01', '33333333-3333-3333-3333-333333333333', '83acb311-dd79-5f5c-bfe8-dc872aace290', '550e8400-e29b-41d4-a716-446655440000', 30, 1.2, 'OUT', 'SAL', '65aba929-c412-47f2-abf5-140b6cd8b51a', true, 1, '2026-03-15 04:50:48');
            

                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('1e8db7e8-63eb-4a58-996f-be3096cad252', '9cd9986b-89da-48b7-8733-26a2a1225b01', '33333333-3333-3333-3333-333333333333', '93acb311-dd79-5f5c-bfe8-dc872aace290', '550e8400-e29b-41d4-a716-446655440000', 15, 1.5, 'IN', 'ENT', '55f40b7a-f6de-41e7-9b01-f6487ddc62df', true, 1, '2026-03-15 03:50:48');
            

                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('651bdbfb-2bb7-4a02-aabd-e60beeb6e438', '9cd9986b-89da-48b7-8733-26a2a1225b01', '33333333-3333-3333-3333-333333333333', '93acb311-dd79-5f5c-bfe8-dc872aace290', '550e8400-e29b-41d4-a716-446655440000', 41, 1.2, 'OUT', 'SAL', 'b84475c5-02cc-4753-845c-1f97ea99c41e', true, 1, '2026-03-15 03:50:48');
            

                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('6a9a2cea-26a8-4fbd-b62e-05e66a68b05e', '9cd9986b-89da-48b7-8733-26a2a1225b01', '33333333-3333-3333-3333-333333333333', '73acb311-dd79-5f5c-bfe8-dc872aace290', '550e8400-e29b-41d4-a716-446655440000', 43, 1.5, 'IN', 'ENT', '9d2ea0a6-fb92-4173-a6e5-b867cfa6555d', true, 1, '2026-03-15 02:50:48');
            

                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('023d2975-99f1-4361-bffb-47303d87972f', '9cd9986b-89da-48b7-8733-26a2a1225b01', '33333333-3333-3333-3333-333333333333', '93acb311-dd79-5f5c-bfe8-dc872aace290', '550e8400-e29b-41d4-a716-446655440000', 23, 1.2, 'OUT', 'SAL', 'c649bde2-3a3f-46eb-b438-43e42721d0c2', true, 1, '2026-03-15 02:50:48');
            

                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('a3df6a26-b98f-41bc-880a-113546fdec5d', '9cd9986b-89da-48b7-8733-26a2a1225b01', '33333333-3333-3333-3333-333333333333', '83acb311-dd79-5f5c-bfe8-dc872aace290', '550e8400-e29b-41d4-a716-446655440000', 36, 1.5, 'IN', 'ENT', '5794b5e4-6ce6-4d25-94d3-613a49448372', true, 1, '2026-03-15 01:50:48');
            

                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('df6bdc67-b413-496d-b1cd-8f93c9cae76f', '9cd9986b-89da-48b7-8733-26a2a1225b01', '33333333-3333-3333-3333-333333333333', '83acb311-dd79-5f5c-bfe8-dc872aace290', '550e8400-e29b-41d4-a716-446655440000', 25, 1.2, 'OUT', 'SAL', '96a74df6-7095-43ed-a2f7-0f7600d63625', true, 1, '2026-03-15 01:50:48');
            

                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('c82b58c3-50f0-4e9e-9ea1-31c206a443c4', '9cd9986b-89da-48b7-8733-26a2a1225b01', '33333333-3333-3333-3333-333333333333', '73acb311-dd79-5f5c-bfe8-dc872aace290', '550e8400-e29b-41d4-a716-446655440000', 59, 1.5, 'IN', 'ENT', '068fe00a-a1b7-4f3e-b466-c817c7adbf8f', true, 1, '2026-03-15 00:50:48');
            

                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('d344b106-22ff-4679-af52-e96a4970ffa8', '9cd9986b-89da-48b7-8733-26a2a1225b01', '33333333-3333-3333-3333-333333333333', '93acb311-dd79-5f5c-bfe8-dc872aace290', '550e8400-e29b-41d4-a716-446655440000', 41, 1.2, 'OUT', 'SAL', '0e7a504d-2508-4bf0-bee7-4e5f2f02d1f5', true, 1, '2026-03-15 00:50:48');
            

                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('72ed2982-c901-413d-98f6-72955dcfc757', '9cd9986b-89da-48b7-8733-26a2a1225b01', '33333333-3333-3333-3333-333333333333', '93acb311-dd79-5f5c-bfe8-dc872aace290', '550e8400-e29b-41d4-a716-446655440000', 13, 1.5, 'IN', 'ENT', 'baf3aa8b-e8ee-4187-971c-9ed79dced163', true, 1, '2026-03-14 23:50:48');
            

                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('aa5f54c5-d9ff-4066-b9ee-2f0a5ffcceec', '9cd9986b-89da-48b7-8733-26a2a1225b01', '33333333-3333-3333-3333-333333333333', '73acb311-dd79-5f5c-bfe8-dc872aace290', '550e8400-e29b-41d4-a716-446655440000', 7, 1.2, 'OUT', 'SAL', '20bf20b7-a228-4327-9e4b-f0027571f1b1', true, 1, '2026-03-14 23:50:48');
            

                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('18dd623d-68d3-4eef-abc6-1c7cea60756f', '9cd9986b-89da-48b7-8733-26a2a1225b01', '33333333-3333-3333-3333-333333333333', '73acb311-dd79-5f5c-bfe8-dc872aace290', '550e8400-e29b-41d4-a716-446655440000', 37, 1.5, 'IN', 'ENT', 'bb88f5d1-7888-49a0-bdbf-1a97e4f904f9', true, 1, '2026-03-14 22:50:48');
            

                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('bd8ddde8-6408-4dd7-92a7-4af919ffd674', '9cd9986b-89da-48b7-8733-26a2a1225b01', '33333333-3333-3333-3333-333333333333', '83acb311-dd79-5f5c-bfe8-dc872aace290', '550e8400-e29b-41d4-a716-446655440000', 9, 1.2, 'OUT', 'SAL', 'acafc1c9-cdd2-48bb-94a6-1eecce1f67d6', true, 1, '2026-03-14 22:50:48');
            

                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('4c5906e1-b52b-4ada-b92a-136795127e8f', '9cd9986b-89da-48b7-8733-26a2a1225b01', '33333333-3333-3333-3333-333333333333', '73acb311-dd79-5f5c-bfe8-dc872aace290', '550e8400-e29b-41d4-a716-446655440000', 25, 1.5, 'IN', 'ENT', '287f0ccb-0041-4c6e-82e5-f50a51e89b31', true, 1, '2026-03-14 21:50:48');
            

                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('9aea1602-2be7-4f22-88ca-b03f556302fe', '9cd9986b-89da-48b7-8733-26a2a1225b01', '33333333-3333-3333-3333-333333333333', '93acb311-dd79-5f5c-bfe8-dc872aace290', '550e8400-e29b-41d4-a716-446655440000', 16, 1.2, 'OUT', 'SAL', '2fcd402a-72e9-4a2f-a953-7560bfe11cdd', true, 1, '2026-03-14 21:50:48');
            

                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('287b57a0-eff9-4f48-b6fb-e5524017ee57', '9cd9986b-89da-48b7-8733-26a2a1225b01', '33333333-3333-3333-3333-333333333333', '93acb311-dd79-5f5c-bfe8-dc872aace290', '550e8400-e29b-41d4-a716-446655440000', 37, 1.5, 'IN', 'ENT', '1a5de807-838c-4e12-bd9a-e8232dcd7cc1', true, 1, '2026-03-14 20:50:48');
            

                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('7e3c17f0-3077-44f1-998d-68c1041b2dab', '9cd9986b-89da-48b7-8733-26a2a1225b01', '33333333-3333-3333-3333-333333333333', 'db856803-a63d-5468-9a7c-9039702acca9', '550e8400-e29b-41d4-a716-446655440000', 6, 1.2, 'OUT', 'SAL', 'dc648caf-0842-42a8-82bd-ccf5d67695f0', true, 1, '2026-03-14 20:50:48');
            

                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('cb8ac128-a8b7-4115-a347-c2f6eea49186', '9cd9986b-89da-48b7-8733-26a2a1225b01', '33333333-3333-3333-3333-333333333333', '83acb311-dd79-5f5c-bfe8-dc872aace290', '550e8400-e29b-41d4-a716-446655440000', 28, 1.5, 'IN', 'ENT', '7bf160d6-cefe-492b-9671-18f4a157fa84', true, 1, '2026-03-14 19:50:48');
            

                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('3b26d5d1-470c-4ede-8044-0793dc9bf74c', '9cd9986b-89da-48b7-8733-26a2a1225b01', '33333333-3333-3333-3333-333333333333', '93acb311-dd79-5f5c-bfe8-dc872aace290', '550e8400-e29b-41d4-a716-446655440000', 20, 1.2, 'OUT', 'SAL', '498bc5d3-b468-4b1f-a3b4-7545e1daa7e0', true, 1, '2026-03-14 19:50:48');
            

                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('4a7d027b-89ff-4abf-9d9b-42bebebed81a', '9cd9986b-89da-48b7-8733-26a2a1225b01', '33333333-3333-3333-3333-333333333333', '83acb311-dd79-5f5c-bfe8-dc872aace290', '550e8400-e29b-41d4-a716-446655440000', 20, 1.5, 'IN', 'ENT', '107a37df-95b9-4421-bf9d-32b02ce696ff', true, 1, '2026-03-14 18:50:48');
            

                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('31375860-1eb7-413f-9323-ae94d5ea73a6', '9cd9986b-89da-48b7-8733-26a2a1225b01', '33333333-3333-3333-3333-333333333333', 'db856803-a63d-5468-9a7c-9039702acca9', '550e8400-e29b-41d4-a716-446655440000', 18, 1.2, 'OUT', 'SAL', 'b5c29e08-2f39-4bea-b407-053319737148', true, 1, '2026-03-14 18:50:48');
            

                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('8878fa7e-ce5e-48fa-bc3d-933773133f50', '9cd9986b-89da-48b7-8733-26a2a1225b01', '33333333-3333-3333-3333-333333333333', 'db856803-a63d-5468-9a7c-9039702acca9', '550e8400-e29b-41d4-a716-446655440000', 48, 1.5, 'IN', 'ENT', '652b5ed9-6286-4cc1-9b9b-1a1d2bef16f2', true, 1, '2026-03-14 17:50:48');
            

                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('64849e70-07f0-4510-8ef5-28bd8a7b9085', '9cd9986b-89da-48b7-8733-26a2a1225b01', '33333333-3333-3333-3333-333333333333', 'db856803-a63d-5468-9a7c-9039702acca9', '550e8400-e29b-41d4-a716-446655440000', 8, 1.2, 'OUT', 'SAL', '0b989fc3-3959-4c2e-bd38-02f4f85ca941', true, 1, '2026-03-14 17:50:48');
            

                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('7e9de236-a1c3-49b4-a2eb-e29a25e1bbcb', '9cd9986b-89da-48b7-8733-26a2a1225b01', '33333333-3333-3333-3333-333333333333', '93acb311-dd79-5f5c-bfe8-dc872aace290', '550e8400-e29b-41d4-a716-446655440000', 22, 1.5, 'IN', 'ENT', '3eed057b-530b-4e0a-9347-06c91e562c5f', true, 1, '2026-03-14 16:50:48');
            

                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('1e65b48d-4df4-4051-bda0-4e496cc9428f', '9cd9986b-89da-48b7-8733-26a2a1225b01', '33333333-3333-3333-3333-333333333333', '83acb311-dd79-5f5c-bfe8-dc872aace290', '550e8400-e29b-41d4-a716-446655440000', 30, 1.2, 'OUT', 'SAL', 'f97d46be-dfb7-4b08-83b3-80b8dbc2fe78', true, 1, '2026-03-14 16:50:48');
            

                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('914f3220-9a1a-46fc-9355-9a43156ab7f6', '9cd9986b-89da-48b7-8733-26a2a1225b01', '33333333-3333-3333-3333-333333333333', 'db856803-a63d-5468-9a7c-9039702acca9', '550e8400-e29b-41d4-a716-446655440000', 59, 1.5, 'IN', 'ENT', 'e472e7e7-119a-40c4-884f-c9867b5742eb', true, 1, '2026-03-14 15:50:48');
            

                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('ae21b77f-944d-445d-9574-1dfdb1b04658', '9cd9986b-89da-48b7-8733-26a2a1225b01', '33333333-3333-3333-3333-333333333333', 'db856803-a63d-5468-9a7c-9039702acca9', '550e8400-e29b-41d4-a716-446655440000', 39, 1.2, 'OUT', 'SAL', '91109359-76cf-448d-b492-b975971fe011', true, 1, '2026-03-14 15:50:48');
            

                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('ad4c11c2-b74a-4d61-9b4d-e40f9520e18f', '9cd9986b-89da-48b7-8733-26a2a1225b01', '33333333-3333-3333-3333-333333333333', 'db856803-a63d-5468-9a7c-9039702acca9', '550e8400-e29b-41d4-a716-446655440000', 21, 1.5, 'IN', 'ENT', 'ddfa49cd-83eb-446d-b27d-726dc25cb97e', true, 1, '2026-03-14 14:50:48');
            

                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('32b1b5da-cf73-4bf5-bc65-d40ca86345f3', '9cd9986b-89da-48b7-8733-26a2a1225b01', '33333333-3333-3333-3333-333333333333', '83acb311-dd79-5f5c-bfe8-dc872aace290', '550e8400-e29b-41d4-a716-446655440000', 6, 1.2, 'OUT', 'SAL', '0c0499e7-a9f6-49d2-b2d4-f764d20a4406', true, 1, '2026-03-14 14:50:48');
            

                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('63fe607e-09bc-41d8-980f-97a55289d385', '9cd9986b-89da-48b7-8733-26a2a1225b01', '33333333-3333-3333-3333-333333333333', '83acb311-dd79-5f5c-bfe8-dc872aace290', '550e8400-e29b-41d4-a716-446655440000', 54, 1.5, 'IN', 'ENT', 'c75c5844-08f6-46ab-b509-ed8eab7fc04a', true, 1, '2026-03-14 13:50:48');
            

                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('881595a3-aac2-4fa0-bbdb-0c7e5928a81f', '9cd9986b-89da-48b7-8733-26a2a1225b01', '33333333-3333-3333-3333-333333333333', '73acb311-dd79-5f5c-bfe8-dc872aace290', '550e8400-e29b-41d4-a716-446655440000', 5, 1.2, 'OUT', 'SAL', '5c48c643-9607-41a5-8d8e-de325e2955d9', true, 1, '2026-03-14 13:50:48');
            

                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('6193dac3-4841-427a-a296-f59f170163d8', '9cd9986b-89da-48b7-8733-26a2a1225b01', '33333333-3333-3333-3333-333333333333', '73acb311-dd79-5f5c-bfe8-dc872aace290', '550e8400-e29b-41d4-a716-446655440000', 29, 1.5, 'IN', 'ENT', '143d8fe5-e7cd-4a8c-8bc3-6bbcef526aa6', true, 1, '2026-03-14 12:50:48');
            

                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('b4ee80fd-da7a-4b44-a40d-2699ff2c630c', '9cd9986b-89da-48b7-8733-26a2a1225b01', '33333333-3333-3333-3333-333333333333', 'db856803-a63d-5468-9a7c-9039702acca9', '550e8400-e29b-41d4-a716-446655440000', 38, 1.2, 'OUT', 'SAL', '098f0647-f6cb-4f1b-9d80-4ed70db039b4', true, 1, '2026-03-14 12:50:48');
            

                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('37a0177e-c1a2-4c0e-b123-d394ee7bd915', '9cd9986b-89da-48b7-8733-26a2a1225b01', '33333333-3333-3333-3333-333333333333', '93acb311-dd79-5f5c-bfe8-dc872aace290', '550e8400-e29b-41d4-a716-446655440000', 58, 1.5, 'IN', 'ENT', '1769f2e1-d4cc-4b3a-9b9a-74623354ff33', true, 1, '2026-03-14 11:50:48');
            

                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('d31d6cfc-b62b-4fa0-ba2b-16716267791e', '9cd9986b-89da-48b7-8733-26a2a1225b01', '33333333-3333-3333-3333-333333333333', '93acb311-dd79-5f5c-bfe8-dc872aace290', '550e8400-e29b-41d4-a716-446655440000', 48, 1.2, 'OUT', 'SAL', '9abc49c9-ccda-409d-b481-f20b3fbaaa9c', true, 1, '2026-03-14 11:50:48');
            

                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('d1c8946d-0ec4-4537-9027-f7132a3bb61e', '9cd9986b-89da-48b7-8733-26a2a1225b01', '33333333-3333-3333-3333-333333333333', '73acb311-dd79-5f5c-bfe8-dc872aace290', '550e8400-e29b-41d4-a716-446655440000', 56, 1.5, 'IN', 'ENT', 'a3d35dd1-d4af-438f-9a69-b0f29cf7194e', true, 1, '2026-03-14 10:50:48');
            

                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('21025bea-58b3-4566-9a0b-0ea212aa4c2b', '9cd9986b-89da-48b7-8733-26a2a1225b01', '33333333-3333-3333-3333-333333333333', '73acb311-dd79-5f5c-bfe8-dc872aace290', '550e8400-e29b-41d4-a716-446655440000', 17, 1.2, 'OUT', 'SAL', 'd08ad115-a005-4740-b7bb-f9b0305f6d8b', true, 1, '2026-03-14 10:50:48');
            

                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('f600249b-aff1-4e80-b8d4-4b78c5c96f8f', '9cd9986b-89da-48b7-8733-26a2a1225b01', '33333333-3333-3333-3333-333333333333', '73acb311-dd79-5f5c-bfe8-dc872aace290', '550e8400-e29b-41d4-a716-446655440000', 40, 1.5, 'IN', 'ENT', 'f2100c8b-ca76-49a9-a2b1-bbfa307af3e8', true, 1, '2026-03-14 09:50:48');
            

                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('06662e8d-dcb2-4328-8813-ac68248ac0f6', '9cd9986b-89da-48b7-8733-26a2a1225b01', '33333333-3333-3333-3333-333333333333', '73acb311-dd79-5f5c-bfe8-dc872aace290', '550e8400-e29b-41d4-a716-446655440000', 9, 1.2, 'OUT', 'SAL', '37381d5c-3b6f-4daa-82c5-bc15ba355c27', true, 1, '2026-03-14 09:50:48');
            

                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('4b061691-1531-4502-ab59-2f7438ec017a', '9cd9986b-89da-48b7-8733-26a2a1225b01', '33333333-3333-3333-3333-333333333333', '73acb311-dd79-5f5c-bfe8-dc872aace290', '550e8400-e29b-41d4-a716-446655440000', 27, 1.5, 'IN', 'ENT', 'fe9578fa-1401-408c-8b49-2254c7ffb9bf', true, 1, '2026-03-14 08:50:48');
            

                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('b5148dad-88ae-4c98-8df9-4c59b9784e7f', '9cd9986b-89da-48b7-8733-26a2a1225b01', '33333333-3333-3333-3333-333333333333', '73acb311-dd79-5f5c-bfe8-dc872aace290', '550e8400-e29b-41d4-a716-446655440000', 24, 1.2, 'OUT', 'SAL', '68efee6f-78bb-4396-bf8b-67328cc621be', true, 1, '2026-03-14 08:50:48');
            

                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('7c423f36-5b9d-44c0-a9e2-08bb1ff4854a', '9cd9986b-89da-48b7-8733-26a2a1225b01', '33333333-3333-3333-3333-333333333333', '73acb311-dd79-5f5c-bfe8-dc872aace290', '550e8400-e29b-41d4-a716-446655440000', 59, 1.5, 'IN', 'ENT', '385b364b-3810-43a3-b2c9-85b559c65525', true, 1, '2026-03-14 07:50:48');
            

                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('8a1c2f5b-c09f-41e1-ab3a-f9107f3e5638', '9cd9986b-89da-48b7-8733-26a2a1225b01', '33333333-3333-3333-3333-333333333333', 'db856803-a63d-5468-9a7c-9039702acca9', '550e8400-e29b-41d4-a716-446655440000', 47, 1.2, 'OUT', 'SAL', '676e6f9c-40c8-43d2-91e9-5be2323f906f', true, 1, '2026-03-14 07:50:48');
            
UPDATE inventory_levels SET quantity = 6 WHERE warehouse_id = '536d182d-3447-5788-87d9-e488ae0af797' AND product_id = '73acb311-dd79-5f5c-bfe8-dc872aace290';
UPDATE inventory_levels SET quantity = 5 WHERE warehouse_id = '22222222-2222-2222-2222-222222222222' AND product_id = '73acb311-dd79-5f5c-bfe8-dc872aace290';
UPDATE inventory_levels SET quantity = 3 WHERE warehouse_id = 'bb18f763-3f93-53af-9fb8-ca1c752f3873' AND product_id = '83acb311-dd79-5f5c-bfe8-dc872aace290';
UPDATE inventory_levels SET quantity = 6 WHERE warehouse_id = '33333333-3333-3333-3333-333333333333' AND product_id = '83acb311-dd79-5f5c-bfe8-dc872aace290';