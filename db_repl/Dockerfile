FROM postgres:14

ENV POSTGRES_DB=${POSTGRES_DB}
ENV POSTGRES_USER=${POSTGRES_USER}
ENV POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
ENV PGPASSWORD=${PGPASSWORD}

RUN apt-get update && apt-get install -y postgresql-client

RUN mkdir -p /logs
RUN chown postgres:postgres /logs
RUN chmod 700 /logs

RUN mkdir -p /oracle/pg_data/archive/
RUN chown postgres:postgres /oracle/pg_data/archive/
RUN chmod 700 /oracle/pg_data/archive/

RUN chmod -R 700 /var/lib/postgresql/data

USER postgres