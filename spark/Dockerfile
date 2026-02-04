FROM bitnami/spark:3.5

USER root
# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

WORKDIR /app
COPY processor.py .

# Trigger the download of the jars by running a dummy command or during build if possible, 
# but mostly we rely on --packages at runtime for spark-submit.
# However, sometimes it is better to have them pre-downloaded.

CMD ["spark-submit", \
     "--packages", "org.mongodb.spark:mongo-spark-connector_2.12:3.0.1,org.postgresql:postgresql:42.6.0", \
     "--master", "spark://spark-master:7077", \
     "processor.py"]
