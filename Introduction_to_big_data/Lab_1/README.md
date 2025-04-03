## Word Count using Hadoop

This project implements a **distributed word count** system using Hadoop with Python

It also includes **Java code to verify MAC address** using `CheckMAC.java` for verification purposes in the lab.

---

### File Structure

```
22120071
|--- 22120071
| |--- docs
| | |--- Report.pdf 
| | |--- 22120071_verfication.txt
| |
| |--- src
| | |--- WordCount
| | | |--- | results.txt
| | | |--- | word_count.py
| | |--- CheckMAC.java
| |--- README
```

---

### Requirements

- Hadoop installed and configured (`HADOOP_HOME` must be set)
- HDFS is running (`start-dfs.sh` and `start-yarn.sh`)
- Python 3.x

---

### How to Run

#### 1. Install library
```bash
pip install mrjob
```

#### 2. Upload the input file to HDFS
```bash
hdfs dfs -mkdir -p /hcmus
hdfs dfs -put words.txt /hcmus/words.txt
```

#### 3. Run the Hadoop job
```bash
python letter_count.py -r hadoop hdfs:///hcmus/words.txt -o hdfs:///hcmus/wordcount_output
```

If `wordcount_output` already exists:
```bash
hdfs dfs -rm -r /hcmus/wordcount_output
```

---

#### 4. Download the output file from HDFS
```bash
hdfs dfs -getmerge /hcmus/wordcount_output results.txt
```
#### 5. Show result
```bash
cat results.txt
```
---

### Output Format

The result is stored in `results.txt` with **TSV (Tab-Separated Values)** format:

```
word1    count
word2    count
...
```

You can open it in a text editor or import it into Excel (choose “Tab” as delimiter).

---

### MAC Address Verification (Java)

We use `CheckMAC.java` to print all network interfaces that the JVM can detect.

#### 1. Compile
```bash
javac CheckMAC.java
```

#### 2. Run
```bash
java CheckMAC
```

This outputs all available network interfaces.  
The correct one will be used inside the `.jar` file which used to generate `22120071_verification.txt`.

---

### 👨‍🏫 Group information
- **Group members**

    | Name                  | Student ID |
    |-----------------------|------------|
    | Phan Bá Đức           | 22120071   |
    | Đặng Duy Lân          | 22120182   |
    | Nguyễn Quốc Thịnh     | 22120347   |
    | Trần Đắc Thịnh        | 22120348   |

- **Course:** Big Data Laboratory  
- **Instructor:** `Dr.Nguyen Ngoc Thao` and `Huynh Lam Hai Đang`
