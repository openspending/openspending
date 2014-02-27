FROM orchardup/python:2.7
MAINTAINER The OpenSpending Contributors

# Install required headers
RUN apt-get update -qq
RUN apt-get install -y python-dev libpq-dev libxml2-dev libxslt1-dev

# Install OpenSpending requirements
RUN mkdir /src
WORKDIR /src
ADD requirements.txt /src/
RUN pip install -r requirements.txt

# Install OpenSpending itself from the current directory
ADD . /src/
RUN pip install -e .

# Expose the web port
EXPOSE 5000

# Run development server by default
ENV PYTHONUNBUFFERED 1
CMD ["contrib/docker/envexec", "paster", "serve", "--reload", "contrib/docker/development.ini"]
