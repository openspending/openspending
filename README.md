# OpenSpending

[![Build Status](https://travis-ci.org/openspending/openspending.svg?branch=master)](https://travis-ci.org/openspending/openspending)
[![Issues in Ready](https://badge.waffle.io/openspending/openspending.png?label=ready&title=Ready)](https://waffle.io/openspending/openspending)
[![Gitter](https://img.shields.io/gitter/room/openspending/chat.svg)](https://gitter.im/openspending/chat)
[![Issues](https://img.shields.io/badge/issue-tracker-orange.svg)](https://github.com/openspending/openspending/issues)
[![Docs](https://img.shields.io/badge/docs-latest-blue.svg)](http://docs.openspending.org/en/latest/developers/platform/)

OpenSpending is a project to make government finances easier to explore and understand. It started out as "Where does my money go", a platform to visualize the United Kingdom's state finance, but has been renamed and restructured to allow arbitrary financial data to be loaded and displayed. 

The main use for the software is the site [openspending.org](http://openspending.org) which aims to track government finance around the world.

OpenSpending's code is licensed under the GNU Affero Licence except where otherwise indicated. A copy of this licence is available in the file [LICENSE.txt](LICENSE.txt).

OpenSpending is a microservices platform made up of a number of separate apps, orchestrated with [Docker Compose](https://docs.docker.com/compose/). This repository contains docker-compose files that can be used for production and development. It also acts as a central hub for managing [issues](https://github.com/openspending/openspending/issues) for the entire platform.

### What are these files?

Most applications that make up the OpenSpending platform are maintained in their own repositories, with their own Dockerfiles, built and pushed to the [OpenSpending organisation on Docker Hub](https://hub.docker.com/r/openspending):

- [os-api](https://github.com/openspending/os-api)
- [os-conductor](https://github.com/openspending/os-conductor)
- [os-viewer](https://github.com/openspending/os-viewer)
- [os-explorer](https://github.com/openspending/os-explorer)
- [os-admin](https://github.com/openspending/os-admin)
- [os-packager](https://github.com/openspending/os-packager)
- [os-fdp-adapters](https://github.com/openspending/os-fdp-adapters)

This repository maintains docker-compose files used to help get you started with the platform.

`docker-compose.base.yml`: This is the main docker-compose file for OpenSpending specific services. All installations will use this as the basis for running the platform.

`docker-compose.dev-services.yml`: This defines backing services used by the platform, such as Redis, ElasticSearch, PostgreSQL, and memcached. This file also includes fake-s3 in place of AWS S3, so you don't have to set up an S3 bucket for development. It is not recommended to use this for production.

`docker-compose.local.yml`: Create this file to add additional services, or overrides for the base configuration. It is ignored by git.

`Dockerfiles/*`: Most services are maintained in their own repositories, but a few small custom services used by the platform are maintained here. `os-nginx-frontend` is a basic frontend nginx server and configuration files to define resource locations for the platform. This will be build and run directly by `docker-compose.base.yml`.

### I'm a developer, how can I start working on OpenSpending?

1. Define the environmental variables that applications in the platform need. The easiest way to do this is to create a `.env` file (use `.env.example` as a template).

2. Use `docker-compose up` to start the platform from the `base`, `dev-services`, and optionally `local` compose files:

`$ docker-compose -f docker-compose.base.yml -f docker-compose.dev-services.yml [-f docker-compose.local.yml] up`

3. Open `localhost` in your browser.

### I'm a developer, how can I work on a specific OpenSpending application? Show me an example!

You can use `volumes` to map local files from the host to application files in the docker containers. For example, say you're working on [OS-Conductor](https://github.com/openspending/os-conductor), you'll add an override service to `docker-compose.local.yml` (create this file if necessary).

1. Checkout the os-conductor code from https://github.com/openspending/os-conductor into `~/src/dockerfiles/os-conductor` on your local machine.
2. Add the following to `docker-compose.local.yml`:

```yml
version: "3"

services:
  os-conductor:
    environment:
      # Force python not to use cached bytecode
      PYTHONDONTWRITEBYTECODE:
    # Override CMD and send `--reload` flag for os-conductor's gunicorn server
    command: /startup.sh --reload
    # Map local os-conductor app files to /app in container
    volumes:
      - ~/src/dockerfiles/os-conductor:/app
```

3. Start up the platform with `base`, `dev-services`, and your `local` compose file:

Now you can start working on os-conductor application files in `~/src/dockerfiles/os-conductor` and changes will reload the server in the Docker container.

`$ docker-compose -f docker-compose.base.yml -f docker-compose.dev-services.yml -f docker-compose.local.yml up`

### I have my own backing service I want to use for development

That's fine, just add the relevant resource locator to the .env file. E.g., you're using a third-party ElasticSearch server:

`OS_ELASTICSEARCH_ADDRESS=https://my-elasticsearch-provider.com/my-es-instance:9200`

### I want to run my own instance of OpenSpending in production

Great! Use the `docker-compose.base.yml` file as a base and add resource locators pointing to your backing services for Postgres, ElasticSearch, Redis, memcached, AWS S3 etc to your environment. See the `.env.example` file for the required env vars you'll need to set up.

You'll also need to set up OAuth credentials for OS-Conductor (see https://github.com/openspending/os-conductor#oauth-credentials), and AWS S3 bucket details.

### What happened to the old version of OpenSpending?

You can find the old OpenSpending v2, and the complete history for the codebase to that point, in the [`openspending-monolith` branch](https://github.com/openspending/openspending/tree/openspending-monolith).

