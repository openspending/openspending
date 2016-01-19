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

### Setting up the environment

 - We start by making sure we have `docker-machine` and `docker-compose` installed on our local machine. For OSX and Windows users, these can be installed using the *Docker Toolbox* - a utility package available from Docker's website.
 - Make sure you have a `default` machine installed - the toolbox installation should create one automatically (you can verify this by using the `docker-machine ls` command). Load its settings to the shell: `eval $(docker-machine env default)`.
 - Make sure the `default` machine is started: `docker-machine start default`
 - Check the IP address for the `default` machine: `docker-machine ip default`
 - Clone this repo and go into the `docker-config` folder
 - Now, we prepare the environment variables necessary. Edit the `secret-sample.sh` file and fill in the correct values for these values (in the near future we plan to simplify this step)
   ```
# You should know the correct values for these variables
declare -x API_KEY_WHITELIST=
declare -x OPENSPENDING_ACCESS_KEY_ID=
declare -x OPENSPENDING_SECRET_ACCESS_KEY=
declare -x OPENSPENDING_STORAGE_BUCKET_NAME=

declare -x OS_API_ENGINE=<connection string to an available DB instance (e.g. postgresql://guest@192.168.99.1/os)>
declare -x OS_EXTERNAL_ADDRESS=<Use the IP address from before>
   ```
 - Load these environment variables to the shell: `source secret-sample.sh`
 - Start the docker containers: `./docker-start.sh` and wait for all containers to finish build and start. If there are any errors, just restart the process (we'll iron them out later on)
 - Open your browser at `http://$OS_EXTERNAL_ADDRESS/` - you should be able to see OS-Packager.

### Deploying to the server

  - First off you need to have access to the server via `ssh`.
  - Make sure you have the following environment variables defined:
    - `OS_DB_HOST` - the OpenSpending DB host name
    - `OS_DB_PWD` - the OpenSpending DB connection password
  - Run `./forward-ports.sh` to create a connection to the server and tunnel some of your local ports to it
  - If you don't have it yet, create the `oslocal` docker machine:
    `docker-machine create -d generic --generic-ip-address 127.0.0.1 --generic-ssh-port 2222 --generic-ssh-user <YOUR-USERNAME> oslocal`
  - Load the settings of this machine to the shell: `eval $(docker-machine env oslocal)`.
  - As before, load the required environment variables to the shell. Make sure you update `OS_API_ENGINE` and `OS_EXTERNAL_ADDRESS` to their correct values.
  - Start the docker containers: `./docker-start.sh` to start deployment to the server

### Development Cycle

**TBD**
