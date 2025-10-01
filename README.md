# AnomalyDSL — Diploma Thesis Project

This repository contains the implementation of **AnomalyDSL**, a Domain-Specific Language (DSL) 
for anomaly detection pipelines in streaming data.  

It was developed as part of my Diploma Thesis at the **School of Electrical & Computer Engineering, Aristotle University of Thessaloniki**.


## Features

- **Grammar definition** in [TextX](https://textx.github.io/textX/) (`src/anomaly.tx`).
- **Automatic code generation** using [Jinja2](https://jinja.palletsprojects.com/) (`src/generate_pipeline.py`).
- **Streaming anomaly detection** with [River](https://riverml.xyz/) as well as **custom detectors** .
- **Integration with MQTT** brokers and **Redis** for real-time anomaly detection pipelines.
- **Evaluation block** supporting Accuracy, Precision, Recall, F1-score, and ROC AUC metrics.
- Example `.anomaly` specification file and the corresponding **generated Python pipeline** are provided 
  to demonstrate the full workflow.

## Installation

### Prerequisites
- Python **3.9 – 3.12** (tested on Python 3.12.3)

### Steps

1. **Clone the repository**
   ```bash
   git clone https://github.com/<username>/anomaly_dsl.git
   cd anomaly_dsl
   ```

2. **Install dependencies**
   - Minimal setup (DSL + streaming + core River models):
     ```bash
     pip install -r requirements-core.txt
     ```
   - Full setup (includes TensorFlow/Keras for custom deep learning models):
     ```bash
     pip install -r requirements-full.txt
     ```

## Usage

The user writes a DSL specification in the file `example.anomaly`.  
From this specification, the final executable Python pipeline is generated automatically.  
The process involves three steps:

1. **Validate the DSL specification (optional)**
   ```bash
   python validate_dsl.py
   
2. **Generate the Python pipeline from the DSL file**
   ```bash
   python generate_pipeline.py
   
3. **Run the generated pipeline**
   ```bash
   python anomaly_pipeline.py

With this process, the generated pipeline connects to the specified MQTT broker and waits for incoming values from the data stream.  
These values are processed in real time, and anomaly detection is performed automatically according to the DSL configuration.

## Testing the Pipeline

To test the generated pipeline, you can open a new terminal window and publish values to the broker topic.  

- In the `publishers/` folder, different publisher scripts are provided:
  - **HiveMQ publisher** (requires username/password authentication)
  - **Flespi publisher** (requires API token authentication)
  - **Localhost publisher** (no authentication, uses a local MQTT broker)

Each user can adapt the publisher according to their broker credentials.  

For the example setup in this repository, we use a **local MQTT broker**.  
You can run the publisher as follows:

```bash
python publishers/localhost_sender.py
```

This will stream values (e.g., from `data.csv`) to the topic defined in the DSL.  
The generated pipeline (running in another terminal) will consume these values and perform anomaly detection in real time.

The repository includes the well-known **Machine Temperature** dataset from the Numenta Anomaly Benchmark (NAB),  
placed directly alongside the publisher scripts.  
This dataset is commonly used for evaluating anomaly detection systems.  

If you want to test with different data, you can simply remove the existing `data.csv` file  
and replace it with your own dataset (keeping the same CSV format).


Once the publisher is running, the pipeline will operate in **real time**:  
- Incoming stream values are processed continuously.  
- Anomaly **scores** are calculated for each value.  
- **Alerts** are generated whenever anomalies are detected and published to the configured MQTT topic.  

These outputs can then be further utilized depending on the use case:  
- Published back into additional MQTT topics for downstream applications.  
- Stored in a **Redis database** for persistence, monitoring dashboards, or later analysis.  
- Written to local **files** (CSV) for logging and offline evaluation.

In this example, the pipeline subscribes to the raw sensor stream (`machine/temperature`) and performs anomaly detection in real time.  
The detected anomaly **scores** and **alerts** are then:  
- Stored in a local **Redis database** for fast access and monitoring.  
- Saved into local **files** (e.g., `alerts.csv`, `scores.json`) for logging and offline evaluation.

Since the dataset used here (NAB Machine Temperature) includes ground-truth labels,  
the DSL configuration also specifies an **Evaluation block**.  
This allows the system to compare predictions against the labels and calculate metrics such as Accuracy, Precision, Recall, F1, and ROC AUC.

When the anomaly detection process is running, you can stop it at any time with **`Ctrl + C`**.  
The system will then prompt you.If you confirm with **`y`**, the evaluation phase will be executed.  
The collected predictions and the ground-truth labels are compared,  
and the chosen metrics are printed in the terminal.


# Examples

Additional example DSL files are provided in the `examples/` folder.  
Users can experiment with the DSL by creating their own specifications,  
combining different components according to their needs.  

Following the same logic as in `example.anomaly`, a user may:  
- Select a different **broker** (e.g., HiveMQ, Flespi, or local MQTT).  
- Replace the default dataset with their own **data** and, if available, corresponding **labels**.  
- Configure various pipelines to work on different anomaly detection scenarios.

By editing the `example.anomaly` file, users can define different pipelines.  
This is the only DSL file that the code reads during execution,  
so any changes (e.g., broker, dataset, labels, detectors) should be made directly in this file  
before running the validation, generation, and execution steps.

## Custom Models

Custom detectors can be added in the `models/` folder.  
Each custom model must inherit from the base `AnomalyDetector` class and implement one of the following methods, depending on the mode:

- **Batch mode** → implement `handleBatch(values)`  
- **Online mode** → implement `handle_one(x)`

In both cases, the method should return:
- **score(s)** → a numerical anomaly score for each input  
- **flag(s)** → 1 if the input is considered an anomaly, 0 otherwise  

The detector is then declared in the DSL (`example.anomaly`) depending on its type:

- **Online mode** → declared simply by its name, without extra arguments.  
- **Batch mode** → declared with the batch size parameter, since this is required for processing data in chunks.  

All other hyperparameters are defined inside the custom detector’s code implementation.

By default, the `models/CUSTOM_MODEL.py` file already contains an example implementation:  
an **LSTM-based anomaly detection model** in batch mode.  

Additionally, two other lightweight examples are provided:  
- **simple_batch** → anomaly detection in batch mode (processes values in groups),  
  performing a simple threshold-based anomaly check.  
- **simple_one** → anomaly detection in online mode (processes values one by one),  
  also performing a simple threshold-based anomaly check.  

If you want to run your own detector as a custom model:  
1. Go to the `models/` folder.  
2. Copy the implementation of your model (e.g., `simple_batch.py`) into the file `CUSTOM_MODEL.py`.  
   - The `CUSTOM_MODEL.py` file serves as the entry point for any custom detector you want to test.
3. In the DSL (`example.anomaly`), declare the CUSTOM detector accordingly.

This way, the code generator will automatically include the detector defined inside `CUSTOM_MODEL.py` in the final pipeline.




