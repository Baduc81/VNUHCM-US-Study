---
title: Introduction to Big Data - Lab 02

---

# Introduction to Big Data - Lab 02

### Prerequisite

- A machine that is running a 64-bit Linux distribution (Debian, Ubuntu, Fedora,...) or a virtual machine (VirtualBox, WMWare, WSL, ...) that is running a 64-bit Linux distribution.
- HDFS installed and is currently running.
- Packages like `python3`, `python3-pip`, and `wget` are also needed.

### Installation Guide
⚠ Please follow all of the steps before running the `.ipynb` file.

In your **current folder**

- Download Java SE 8 (JDK8)
    - Download the official (archived) tarball from Oracle using `wget`
        ```bash!
        wget https://download.java.net/openjdk/jdk8u44/ri/openjdk-8u44-linux-x64.tar.gz
        ```
    - Extract the tarball using the command
        ```bash!
        tar -xf openjdk-8u44-linux-x64.tar.gz
        ```
    Or you can download Java SE 8 using your distribution's package manager (i.e., `apt install openjdk-8-jdk-headless` on Ubuntu,  requires `sudo` privilege).
- Download Apache Spark 3.5.5
    - Download the official tarball from Apache using `wget`
        ```bash!
        wget https://downloads.apache.org/spark/spark-3.5.5/spark-3.5.5-bin-hadoop3.tgz
        ```
    - Extract the tarball using the command
        ```bash!
        tar -xf spark-3.5.5-bin-hadoop3.tgz
        ```
- Download the `pyshark` package using `pip`
    ```bash!
    pip install pyshark
    ```

Your current directory should look like this

```
📁 /
│
├── 📁 spark-3.5.5-bin-hadoop3/       ◄─── SPARK_HOME → used by PySpark
│     └── bin/spark-class             ◄─── Launched by PySpark JVM gateway
│
├── 📁 java-se-8u44-ri/               ◄─── JAVA_HOME → needed for PySpark's Java backend
│     └── bin/java                    ◄─── Java runtime used by Spark
│
├── 📄 spark-3.5.5-bin-hadoop3.tgz    ◄─── tarball originally extracted to create `spark-3.5.5-bin-hadoop3/`
├── 📄 openjdk-8u44-linux-x64.tar.gz  ◄─── tarball originally extracted to create `java-se-8u44-ri/`
│
├── 📄 shapes.parquet                 ◄─── your input data for Spark
│
├── 📄 Lab02_Ex01.ipynb
├── 📄 Lab02_Ex02.ipynb
└── 📄 Lab02_Ex03.ipynb

```

### Notes for Running Task 2.2 and Task 2.3

- Set `HDFS_URI` constant
    - Check for your `HDFS NameNode` service port with the command
        ```bash!
        cat $HADOOP_HOME/etc/hadoop/core-site.xml
        ```
    - Check the the value in the `value` sub-tag, which should look like this: `hdfs://localhost:<port_number>`.
    - Copy the value and assign it to the `HDFS_URI` constant (in the first code cell of the Notebook file).   
- If you have installed JDK 8 using the distribution's package manager, you don't need to use the `os.environ["JAVA_HOME"]` config (also in the first code cell of the Notebook file).