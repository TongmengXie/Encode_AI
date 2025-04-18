FROM alpine:latest

RUN apk add --no-cache bash

WORKDIR /data

# Create necessary directories
RUN mkdir -p /data/UserInfo_and_Match/survey_results
RUN mkdir -p /data/wandermatch_output/maps
RUN mkdir -p /data/wandermatch_output/blogs

# Keep container running
CMD ["tail", "-f", "/dev/null"] 