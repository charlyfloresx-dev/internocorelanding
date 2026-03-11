#!/bin/bash
set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
	CREATE DATABASE master_data_db;
	CREATE DATABASE subscription_db;
	CREATE DATABASE inventory_db;
	CREATE DATABASE wms_db;
	CREATE DATABASE tickets_db;
	CREATE DATABASE mes_db;
EOSQL
