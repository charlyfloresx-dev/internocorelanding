#!/bin/bash
set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
	CREATE DATABASE master_data_db;
	CREATE DATABASE subscription_db;
	CREATE DATABASE inventory_db;
	CREATE DATABASE wms_db;
	CREATE DATABASE tickets_db;
	CREATE DATABASE mes_db;
	CREATE DATABASE currency_db;
	CREATE DATABASE hr_db;
	CREATE DATABASE viatra_db;
	CREATE DATABASE kiosk_db;
	CREATE DATABASE asset_manager_db;
EOSQL
