# run_20hz_pulse_train.py

from pulse_pal import PulsePalObject, PulsePalError
import time

# --- Parameters You Can Change ---
SERIAL_PORT = 'COM4'                # Your Pulse Pal's port name
CHANNEL = 1
PULSE_VOLTAGE = 5.0                 # The voltage of the "ON" pulse
PULSE_FREQUENCY_HZ = 20             # The frequency of the pulsing in Hertz
TRAIN_DURATION_SECONDS = 60         # How long the entire pulse train should last
DELAY_SECONDS = 10                  # The initial delay before the pulsing starts
DUTY_CYCLE = 0.5                    # 0.5 = 50% on, 50% off. 0.2 = 20% on, 80% off.
# ---------------------------------

# --- Calculate timing from parameters ---
# We don't program frequency directly, but rather the duration of the pulse
# and the interval between pulses.
period = 1.0 / PULSE_FREQUENCY_HZ  # Duration of one full ON/OFF cycle
pulse_on_duration = period * DUTY_CYCLE
pulse_off_duration = period * (1.0 - DUTY_CYCLE)
# ----------------------------------------

print("--- 20Hz Pulse Train Experiment ---")

try:
    # 1. Connect to the Pulse Pal
    print(f"Connecting to Pulse Pal on {SERIAL_PORT}...")
    myPulsePal = PulsePalObject(SERIAL_PORT)
    print("Connection successful.")

    # 2. Configure the pulse parameters for the specified channel
    print(f"Configuring Channel {CHANNEL} for a {PULSE_FREQUENCY_HZ}Hz pulse train...")
    
    # Set the resting voltage to 0V (the voltage when pulses are off)
    myPulsePal.programOutputChannelParam('restingVoltage', channel=CHANNEL, value=0)
    
    # Set the pulse train to start after the delay
    myPulsePal.programOutputChannelParam('pulseTrainDelay', channel=CHANNEL, value=DELAY_SECONDS)
    
    # We will use a monophasic pulse (isBiphasic = 0)
    myPulsePal.programOutputChannelParam('isBiphasic', channel=CHANNEL, value=0)
    
    # Set the voltage of the "ON" part of the pulse
    myPulsePal.programOutputChannelParam('phase1Voltage', channel=CHANNEL, value=PULSE_VOLTAGE)
    
    # Set the duration of the "ON" part of the pulse
    myPulsePal.programOutputChannelParam('phase1Duration', channel=CHANNEL, value=pulse_on_duration)
    
    # IMPORTANT: Set the interval between pulses (the "OFF" time)
    myPulsePal.programOutputChannelParam('interPulseInterval', channel=CHANNEL, value=pulse_off_duration)

    # Set the total duration for the entire train of pulses
    myPulsePal.programOutputChannelParam('pulseTrainDuration', channel=CHANNEL, value=TRAIN_DURATION_SECONDS)
    
    print("Configuration complete.")
    print(f"  - Frequency: {PULSE_FREQUENCY_HZ} Hz")
    print(f"  - On-Time per pulse: {pulse_on_duration*1000:.1f} ms")
    print(f"  - Off-Time per pulse: {pulse_off_duration*1000:.1f} ms")
    print(f"  - Total Train Duration: {TRAIN_DURATION_SECONDS} s (after {DELAY_SECONDS}s delay)")
    
    # 3. Trigger the channel
    print("\nTriggering the pulse train now. It will start after the delay.")
    
    trigger_args = {f'channel{i}': 1 if i == CHANNEL else 0 for i in range(1, 5)}
    myPulsePal.triggerOutputChannels(**trigger_args)
    
    # 4. Wait for the experiment to finish and give feedback
    total_time = DELAY_SECONDS + TRAIN_DURATION_SECONDS
    print(f"Pulse train initiated. It will run for a total of {total_time} seconds.")
    print("You can close this script now; the Pulse Pal will complete the train on its own.")
    print("Waiting here for demonstration purposes...")
    time.sleep(total_time + 2) # Wait for it to finish plus a little extra
    
    print("\nExperiment finished.")

except PulsePalError as e:
    print(f"\nERROR: A Pulse Pal error occurred: {e}")
except Exception as e:
    print(f"\nERROR: A general error occurred: {e}")