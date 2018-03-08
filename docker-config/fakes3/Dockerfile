FROM alpine:latest

RUN apk --update add \
    git \
    ruby \
    ruby-dev \
    ruby-rdoc \
    ruby-irb \
    ruby-json \
    ruby-rake

RUN git clone https://github.com/jubos/fake-s3.git app
# Checkout the version with the cors options
RUN cd app git checkout 994f7ff8875a4fbab51530995b8ad6b82d622f39
RUN cd app && gem build fakes3.gemspec
RUN gem install app/fakes3-1.2.1.gem


RUN mkdir -p /fakes3_root
ENTRYPOINT ["/usr/bin/fakes3"]
# Add CORS preflight headers
CMD ["-r",  "/fakes3_root", "-p",  "4567", "--corspreflightallowheaders", "Accept, Content-Type, Authorization, Content-Length, ETag, X-CSRF-Token, Content-Disposition, Content-MD5"]

EXPOSE 4567
