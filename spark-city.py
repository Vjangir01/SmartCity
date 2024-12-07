from pyspark.sql import SparkSession, DataFrame
from pyspark.sql.functions import  from_json, col
from pyspark.sql.types import StructType, StructField, StringType, TimestampType, DoubleType, IntegerType
from config import configuration

def main():
    spark = SparkSession.builder.appName("SmartCityStreaming")\
    .config("spark.jars.packages",
            "org.apache.spark:spark-core_2.13:3.5.3,"
            "org.apache.hadoop:hadoop-aws:3.3.6,"
            "com.amazonaws:aws-java-sdk:1.11.469")\
    .config("spark.hadoop.fs.s3a.impl", "org.apche.hadoop.fs.s3a.S3AFileSystem")\
    .config("spark.hadoop.fs.s3a.access.key", configuration.get('AWS_ACCESS_KEY'))\
    .config("spark.hadoop.fs.s3a.secret.key", configuration.get('AWS_SECRET_KEY'))\
    .config("spark.hadoop.fs.s3a.aws.credentials.provider",
            'org.apache.hadoop.fs.s3a.SimpleAWSCredentialsProvider')\
    .getOrCreate()

    # Adjust the log level to minimize the console output on executors
    spark.sparkContext.setLogLevel('WARN')

    # vehicle schema
    vehicleSchema = StructType([
        StructField("id",StringType(),True),
        StructField("deviceID",StringType(),True),
        StructField("timestamp",TimestampType(),True),
        StructField("location",StringType(),True),
        StructField("speed",DoubleType(),True),
        StructField("direction",StringType(),True),
        StructField("make",StringType(),True),
        StructField("year",IntegerType(),True),
        StructField("fuelType",StringType(),True),
    ])
    # gps schema
    gpsSchema = StructType([
        StructField("id",StringType(),True),
        StructField("deviceID",StringType(),True),
        StructField("timestamp",TimestampType(),True),
        StructField("speed",DoubleType(),True),
        StructField("direction",StringType(),True),
        StructField("vehicleType",StringType(),True),

    ])

    # Traffic Schema
    trafficSchema = StructType([
        StructField("id", StringType(), True),
        StructField("deviceID", StringType(), True),
        StructField("cameraId", StringType(), True),
        StructField("location", StringType(), True),
        StructField("timestamp", TimestampType(), True),
        StructField("snapshot", StringType(), True),

    ])
    # weather Schema
    weatherSchema = StructType([
        StructField("id", StringType(),True),
        StructField("deviceID", StringType(),True),
        StructField("location", StringType(),True),
        StructField("temperature", DoubleType(),True),
        StructField("weatherCondition", StringType(),True),
        StructField("precipitation", DoubleType(),True),
        StructField("windSpeed", DoubleType(),True),
        StructField("humidity", IntegerType(),True),
        StructField("airQualityIndex", DoubleType(),True),
    ])

    # emergencySchema
    emergencySchema = StructType([
        StructField("id", StringType(),True),
        StructField("deviceID", StringType(),True),
        StructField("incidentId", StringType(),True),
        StructField("type", StringType(),True),
        StructField("timestamp", TimestampType(),True),
        StructField("location", StringType(),True),
        StructField("status", StringType(),True),
        StructField("description", StringType(),True),

    ])

    def read_kafka_topic(topic, schema):
        return (spark.readStream
                .format('kafka')
                .option('kafka.bootstrap.servers', 'broker:29092')
                .option('subscribe', topic)
                .option('startingOffsets', 'earliest')
                .load()
                .selectExpr('CAST(value AS STRING)')
                .select(from_json(col('value'),schema).alias('data'))
                .select('data.*')
                .withWatermark('timestamp', '2 minutes')
                )

    def streamWriter(input: DataFrame, checkpointFolder, output ):
        return (input.writeStream
                .format('parquet')
                .option('checkpointLocation', checkpointFolder)
                .option('path', output)
                .outputMode('append')
                .start())


    vehicleDF = read_kafka_topic('vehicle_data', vehicleSchema).alias('vehicle')
    gpsDF = read_kafka_topic('gps_data', gpsSchema).alias('gps')
    trafficDF = read_kafka_topic('traffic_data', trafficSchema).alias('traffic')
    weatherDF = read_kafka_topic('weather_data', weatherSchema).alias('weather')
    emergencyDF = read_kafka_topic('emergency_data', emergencySchema).alias('emergency')

    # join all the DFs with id and timestamp
    #join


    query1 = streamWriter(vehicleDF, 's3a://spark-streaming-data/checkpoint/vehicle_data12',
                 's3a://spark-streaming-data/data/vehicle_data')
    query2 = streamWriter(gpsDF, 's3a://spark-streaming-data/checkpoint/gps_data12',
                 's3a://spark-streaming-data/data/gps_data')
    query3 = streamWriter(trafficDF, 's3a://spark-streaming-data/checkpoint/traffic_data12',
                 's3a://spark-streaming-data/data/traffic_data')
    query4 = streamWriter(weatherDF, 's3a://spark-streaming-data/checkpoint/weather_data12',
                 's3a://spark-streaming-data/data/weather_data')
    query5 = streamWriter(emergencyDF, 's3a://spark-streaming-data/checkpoint/emergency_data12',
                 's3a://spark-streaming-data/data/emergency_data')

    query5.awaitTermination()

if __name__ == "__main__":
    main()

