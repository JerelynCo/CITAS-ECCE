#!/bin/bash

# Set the HCI Config to PSCAN so that other devices can connect to it
echo "Configuring Bluetooth adapter..."
sudo hciconfig hci0 piscan
echo "Done."

# Run the main program
echo "Running program..."
for i in {0..1};
do
    echo "Iteration $i started."
    sudo python3 main.py;
    echo "Iteration $1 finished."
done;
echo "Program finished. "
