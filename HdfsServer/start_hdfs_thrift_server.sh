#!/bin/sh

HADOOP_CONF_DIR=/etc/hadoop/conf/

# hadoop config
CLASSPATH=${HADOOP_CONF_DIR}

HADOOP_HOME=/usr/lib/hadoop
for f in ${HADOOP_HOME}/*.jar \
        ${HADOOP_HOME}/lib/*.jar \
        ${HADOOP_HOME}/contrib/thriftfs/*.jar
do
    CLASSPATH=${CLASSPATH}:${f}
done

java -Dcom.sun.management.jmxremote -classpath $CLASSPATH org.apache.hadoop.thriftfs.HadoopThriftServer $*
