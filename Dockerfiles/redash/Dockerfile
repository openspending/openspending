FROM gliderlabs/alpine:3.4

# Packages and dependencies
RUN apk add --update git libpq python bash sudo
RUN apk add --no-cache --virtual=build-dependencies \
    python-dev build-base pwgen libffi-dev ca-certificates \
    wget curl tar mariadb-dev postgresql-dev nodejs postgresql \
    libsasl cyrus-sasl-dev
RUN curl -L https://npmjs.org/install.sh | sh

# CA Certificates
RUN update-ca-certificates

# PIP
RUN wget "https://bootstrap.pypa.io/get-pip.py" -O /dev/stdout | python

# Users creation
RUN adduser -S redash

# Pip requirements for all data source types
RUN python -m pip install -U setuptools supervisor==3.1.2

# Get latest redash
RUN mkdir -p /opt/redash/current
RUN git clone http://github.com/akariv/redash.git  /opt/redash/current
RUN chown -R redash /opt/redash/current

# Setting working directory
WORKDIR /opt/redash/current

ENV REDASH_STATIC_ASSETS_PATH="../rd_ui/dist/"

# Install project specific dependencies
RUN pip install -r requirements.txt
RUN PYMSSQL_BUILD_WITH_BUNDLED_FREETDS=yes pip install -r requirements_all_ds.txt
RUN sudo -u redash -H make deps && \
 rm -rf rd_ui/node_modules /home/redash/.npm /home/redash/.cache

# Setup supervisord
RUN mkdir -p /opt/redash/supervisord && \
    mkdir -p /opt/redash/logs && \
    cp /opt/redash/current/setup/docker/supervisord/supervisord.conf /opt/redash/supervisord/supervisord.conf

# Fix permissions
RUN chown -R redash /opt/redash

# Cleanup
RUN apk del build-dependencies
RUN rm -rf /var/cache/apk/*

# Expose ports
EXPOSE 5000
EXPOSE 9001

# Startup script
CMD  cd /opt/redash/current && touch .env && \
     echo $REDASH_DATABASE_URL && \
     (./bin/run python manage.py database create_tables || true ) && \
     (./bin/run python manage.py ds new -n OpenSpending -t pg -o \
     "{\"user\": \"$OS_DB_USER\", \"host\": \"$OS_DB_HOST\", \"dbname\": \"$OS_DB_NAME\", \"password\": $OS_DB_PWD }") || true && \
     (./bin/run python manage.py users grant_admin adam.kariv@okfn.org ) || true && \
     /usr/bin/supervisord -c /opt/redash/supervisord/supervisord.conf
# RUN apk add --update nodejs
# git fetch && git checkout origin/master && \
#     (cd rd_ui && sudo -u redash node_modules/.bin/gulp ) && \
