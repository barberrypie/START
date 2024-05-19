#!/bin/bash
set -e

# Добавляем настройки в postgresql.conf
echo "listen_addresses = '*'" >> "$PGDATA/postgresql.conf"
echo "port = 5432" >> "$PGDATA/postgresql.conf"
echo "max_connections = 100" >> "$PGDATA/postgresql.conf"
echo "wal_level = replica" >> "$PGDATA/postgresql.conf"
echo "max_wal_senders = 10" >> "$PGDATA/postgresql.conf"
echo "archive_mode = on" >> "$PGDATA/postgresql.conf"
echo "archive_command = 'cp %p /var/lib/postgresql/data/archive/%f'" >> "$PGDATA/postgresql.conf"
echo "log_replication_commands = on" >> "$PGDATA/postgresql.conf"

# Добавляем настройки в pg_hba.conf
echo "host replication all all trust" >> "$PGDATA/pg_hba.conf"
