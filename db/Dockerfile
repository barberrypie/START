FROM postgres:14

ENV POSTGRES_DB=${POSTGRES_DB}
ENV POSTGRES_USER=${POSTGRES_USER}
ENV POSTGRES_PASSWORD=${POSTGRES_PASSWORD}

COPY init.sql /docker-entrypoint-initdb.d/

RUN echo "logging_collector = on" >> /usr/share/postgresql/postgresql.conf.sample && \
    echo "log_directory = '/logs'" >> /usr/share/postgresql/postgresql.conf.sample && \
    echo "log_filename = 'postgresql.log'" >> /usr/share/postgresql/postgresql.conf.sample && \
    echo "listen_addresses = '*'" >> /usr/share/postgresql/postgresql.conf.sample && \
    echo "port = 5432" >> /usr/share/postgresql/postgresql.conf.sample && \
    echo "max_connections = 100" >> /usr/share/postgresql/postgresql.conf.sample && \
    echo "wal_level = replica" >> /usr/share/postgresql/postgresql.conf.sample && \
    echo "max_wal_senders = 10" >> /usr/share/postgresql/postgresql.conf.sample && \
    echo "archive_mode = on" >> /usr/share/postgresql/postgresql.conf.sample && \
    echo "archive_command = 'cp %p /oracle/pg_data/archive/%f'" >> /usr/share/postgresql/postgresql.conf.sample && \
    echo "log_replication_commands = on" >> /usr/share/postgresql/postgresql.conf.sample
RUN mkdir -p /logs
RUN chown postgres:postgres /logs
RUN chmod 700 /logs

RUN mkdir -p /oracle/pg_data/archive/
RUN chown postgres:postgres /oracle/pg_data/archive/
RUN chmod 700 /oracle/pg_data/archive/

USER postgres
CMD ["postgres", "-c", "config_file=/usr/share/postgresql/postgresql.conf.sample"]
