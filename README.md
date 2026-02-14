# Python AI – GardenStation

Decision tree and control logic: decides what to do based on recognition results and sends commands to the Arduino.

## Setup

```bash
conda create -p .conda python=3.10
conda activate .conda
conda install scikit-learn  # or pip install -r requirements.txt
```

## Usage

Run the main controller; it reads from the recognition module and writes commands to the serial port (Arduino or simulation).
