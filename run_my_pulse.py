# run_my_pulse.py

from pulse_pal import PulsePalObject, PulsePalError
import time

# --- Parameters You Can Change ---
SERIAL_PORT = 'COM4'  # IMPORTANT: Change this to your Pulse Pal's port name!
CHANNEL = 1
DELAY_SECONDS = 10
PULSE_VOLTAGE = 5.00
PULSE_DURATION_SECONDS = 60
# ---------------------------------

print("--- Single Pulse Experiment ---")

try:
    # 1. Connect to the Pulse Pal
    print(f"Connecting to Pulse Pal on {SERIAL_PORT}...")
    myPulsePal = PulsePalObject(SERIAL_PORT)
    print("Connection successful.")

    # 2. Configure the pulse parameters for the specified channel
    print(f"Configuring Channel {CHANNEL} for a single pulse...")
    
    # Set the resting voltage to 0V (the voltage before and after the pulse)
    myPulsePal.programOutputChannelParam('restingVoltage', channel=CHANNEL, value=0)
    
    # Set the pulse train to start after a 10-second delay
    myPulsePal.programOutputChannelParam('pulseTrainDelay', channel=CHANNEL, value=DELAY_SECONDS)
    
    # We will use a monophasic pulse (isBiphasic = 0)
    myPulsePal.programOutputChannelParam('isBiphasic', channel=CHANNEL, value=0)
    
    # Set the voltage of the pulse to 5.32V
    myPulsePal.programOutputChannelParam('phase1Voltage', channel=CHANNEL, value=PULSE_VOLTAGE)
    
    # Set the duration of that single pulse to 60 seconds
    myPulsePal.programOutputChannelParam('phase1Duration', channel=CHANNEL, value=PULSE_DURATION_SECONDS)
    
    # CRITICAL: Set the total duration of the train to match the pulse duration.
    # This ensures only one pulse is delivered.
    myPulsePal.programOutputChannelParam('pulseTrainDuration', channel=CHANNEL, value=PULSE_DURATION_SECONDS)
    
    print("Configuration complete.")
    print(f"  - Delay: {DELAY_SECONDS}s")
    print(f"  - Voltage: {PULSE_VOLTAGE}V")
    print(f"  - Duration: {PULSE_DURATION_SECONDS}s")
    
    # 3. Trigger the channel
    print("\nTriggering the pulse now. The pulse will start after the delay.")
    
    # Create a trigger mapping for the channels
    trigger_args = {f'channel{i}': 1 if i == CHANNEL else 0 for i in range(1, 5)}
    myPulsePal.triggerOutputChannels(**trigger_args)
    
    # 4. Wait for the experiment to finish and give feedback
    total_time = DELAY_SECONDS + PULSE_DURATION_SECONDS
    print(f"Pulse train initiated. It will run for a total of {total_time} seconds.")
    print("You can close this script now, the Pulse Pal will complete the pulse on its own.")
    print("Waiting here for demonstration purposes...")
    time.sleep(total_time + 2) # Wait for it to finish plus a little extra
    
    print("\nExperiment finished.")

except PulsePalError as e:
    print(f"\nERROR: A Pulse Pal error occurred: {e}")
except Exception as e:
    print(f"\nERROR: A general error occurred: {e}")