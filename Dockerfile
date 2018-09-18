#Grab the alpine image with machinelearning libs 
FROM frolvlad/alpine-python-machinelearning

# Install python and pip
# RUN apk add --no-cache --update alpine-sdk python3 py3-pip bash
RUN apk add --no-cache --update bash 
RUN apk add --no-cache --virtual .build-deps build-base pkgconfig gfortran
RUN apk add --no-cache --update openjdk8-jre python3-dev py3-lxml jpeg-dev zlib-dev
ADD ./requirements.txt /tmp/requirements.txt

# Install dependencies
RUN pip3 install --no-cache-dir -r /tmp/requirements.txt

# Add our code
ADD ./ /opt/webapp/
WORKDIR /opt/webapp

RUN apk del .build-deps

# Run the image as a non-root user
RUN adduser -D myuser
USER myuser

# Run the app
RUN python3 ./nltksetup.py
ENV NEWS_API_KEY="visit https://newsapi.org/ to get API key"

CMD python3 ./newsapi_crawler.py ~/news.csv
