# OpenSpending

OpenSpending is a project to make government finances easier to explore
and understand. It started out as "Where does my money go", a platform
to visualize the United Kingdom's state finance, but has been renamed
and restructured to allow arbitrary financial data to be loaded and
displayed. The main use for the software is the site openspending.org
which aims to track government finance around the world.

## Licensing

OpenSpending's code is licensed under the GNU Affero Licence except where
otherwise indicated. A copy of this licence is available in the file
LICENSE.txt

**You can find OpenSpending V2, and the complete history for the codebase to that point, in the [`openspending-monolith` branch](https://github.com/openspending/openspending/tree/openspending-monolith).**

## Local Development and Deployment

OpenSpending's architecture is composed from several, separate services.

In order to simplify set-up and provisioning of these services, we use the *Docker* infrastructure, creating individual "containers" for every piece of the puzzle. The complete set of containers can be provisioned and started using `docker-compose`. You can find the configuration for these containers in the `docker-config` folder.

### Setting up the development environment

 - We start by making sure we have `docker-machine` and `docker-compose` installed on our local machine. For OSX and Windows users, these can be installed using the *Docker Toolbox* - a utility package available from Docker's website.
 - Make sure that:
     - You're using Docker version 1.9 or newer (`docker -v`) and docker-compose version 1.5.2 or newer (`docker-compose -v`)
     - You have a `default` machine installed - the toolbox installation should create one automatically (you can verify this by using the `docker-machine ls` command).
     - You're working against the `default` machine by loadin its settings to the shell: `eval $(docker-machine env default)`.
     - The `default` machine is started: `docker-machine start default`
 - Check the IP address for the `default` machine: `docker-machine ip default`
 - Edit the `/etc/hosts` file on your machine and add the following entries:
   ```
192.168.99.100  api.openspending.dev
192.168.99.100  packager.openspending.dev
192.168.99.100  conductor.openspending.dev
   ```
   You should replace `192.168.99.100` with the actual IP address of machine which you found in the previous step.
   (see [this discussion](http://superuser.com/questions/525688/whats-the-windows-equivalent-of-etc-hosts) for Windows machines)
 - Clone this repo into a directory in your local machine: `git clone https://github.com/openspending/openspending`
 - Run `repos/clone_all.sh` - this will create local copies for all OpenSpending related code bases.
 - Now go into the `docker-config` folder, and start the docker containers: `./docker-start-dev.sh`
 - Wait for all containers to finish build and start. If there are any errors, just restart the process (we'll iron them out later on)
 - Open your browser at `http://packager.openspending.dev/` - you should be able to see OS-Packager web UI.

### Editing the code

You can modify the code under `repos/` and rerun `./docker-start-dev.sh` to see the changes take place.

### Deploying to the server

  - First off you need to have access to the server via `ssh`.
  - Make sure you have the following environment variables defined:
    - `OS_DB_HOST` - the OpenSpending DB host name
    - `OS_DB_PWD` - the OpenSpending DB connection password
    - `OS_API_ENGINE` - the OpenSpending DB connection string
    - `API_KEY_WHITELIST` - Allowed API keys in the conductor
    - `OPENSPENDING_ACCESS_KEY_ID`, `OPENSPENDING_SECRET_ACCESS_KEY` and `OPENSPENDING_STORAGE_BUCKET_NAME` - S3 Bucket info

  - Run `./forward-ports.sh` to create a connection to the server and tunnel some of your local ports to it
  - If you don't have it yet, create the `oslocal` docker machine:
    `docker-machine create -d generic --generic-ip-address 127.0.0.1 --generic-ssh-port 2222 --generic-ssh-user <YOUR-USERNAME> oslocal`
  - Load the settings of this machine to the shell: `eval $(docker-machine env oslocal)`.
  - Build the containers from scratch to make sure you're deploying the latest code `docker-compose -f production.yml build --no-cache`
  - Start the docker containers on the remote server via `./docker-start-prod.sh`
