# run_staggered_channels.py

from pulse_pal import PulsePalObject, PulsePalError
import time

# --- Parameters You Can Change ---
SERIAL_PORT = 'COM4'                # Your Pulse Pal's port name

# --- Channel 1 Parameters (20Hz Pulse Train with Delay) ---
CHANNEL_1 = 1
PULSE_VOLTAGE_CH1 = 5.0
PULSE_FREQUENCY_HZ_CH1 = 20
DUTY_CYCLE_CH1 = 0.5
TRAIN_DURATION_SECONDS_CH1 = 60
DELAY_SECONDS_CH1 = 10              # Delay for Channel 1

# --- Channel 2 Parameters (Continuous Signal, No Delay) ---
CHANNEL_2 = 2
VOLTAGE_CH2 = 5.32
TRAIN_DURATION_SECONDS_CH2 = 60
DELAY_SECONDS_CH2 = 0               # No delay for Channel 2
# --------------------------------------------------

# --- Calculate timing for Channel 1 ---
period_ch1 = 1.0 / PULSE_FREQUENCY_HZ_CH1
pulse_on_duration_ch1 = period_ch1 * DUTY_CYCLE_CH1
pulse_off_duration_ch1 = period_ch1 * (1.0 - DUTY_CYCLE_CH1)
# --------------------------------------

print("--- Staggered Two-Channel Experiment ---")

try:
    # 1. Connect to the Pulse Pal
    print(f"Connecting to Pulse Pal on {SERIAL_PORT}...")
    myPulsePal = PulsePalObject(SERIAL_PORT)
    print("Connection successful.")

    # --- Configure Channel 1: 20Hz Pulse Train ---
    print(f"\nConfiguring Channel {CHANNEL_1} for a {PULSE_FREQUENCY_HZ_CH1}Hz pulse train with a {DELAY_SECONDS_CH1}s delay...")
    myPulsePal.programOutputChannelParam('restingVoltage', channel=CHANNEL_1, value=0)
    myPulsePal.programOutputChannelParam('pulseTrainDelay', channel=CHANNEL_1, value=DELAY_SECONDS_CH1)
    myPulsePal.programOutputChannelParam('isBiphasic', channel=CHANNEL_1, value=0)
    myPulsePal.programOutputChannelParam('phase1Voltage', channel=CHANNEL_1, value=PULSE_VOLTAGE_CH1)
    myPulsePal.programOutputChannelParam('phase1Duration', channel=CHANNEL_1, value=pulse_on_duration_ch1)
    myPulsePal.programOutputChannelParam('interPulseInterval', channel=CHANNEL_1, value=pulse_off_duration_ch1)
    myPulsePal.programOutputChannelParam('pulseTrainDuration', channel=CHANNEL_1, value=TRAIN_DURATION_SECONDS_CH1)
    print("Channel 1 configuration complete.")

    # --- Configure Channel 2: Continuous Voltage ---
    print(f"\nConfiguring Channel {CHANNEL_2} for a continuous {VOLTAGE_CH2}V signal with no delay...")
    myPulsePal.programOutputChannelParam('restingVoltage', channel=CHANNEL_2, value=0)
    myPulsePal.programOutputChannelParam('pulseTrainDelay', channel=CHANNEL_2, value=DELAY_SECONDS_CH2) # Set to 0
    myPulsePal.programOutputChannelParam('isBiphasic', channel=CHANNEL_2, value=0)
    myPulsePal.programOutputChannelParam('phase1Voltage', channel=CHANNEL_2, value=VOLTAGE_CH2)
    myPulsePal.programOutputChannelParam('phase1Duration', channel=CHANNEL_2, value=TRAIN_DURATION_SECONDS_CH2)
    myPulsePal.programOutputChannelParam('pulseTrainDuration', channel=CHANNEL_2, value=TRAIN_DURATION_SECONDS_CH2)
    print("Channel 2 configuration complete.")

    # 3. Trigger BOTH channels simultaneously
    print("\nTriggering both channels now.")
    print(f" -> Channel {CHANNEL_2} will start immediately and run for {TRAIN_DURATION_SECONDS_CH2}s.")
    print(f" -> Channel {CHANNEL_1} will start after {DELAY_SECONDS_CH1}s and then run for {TRAIN_DURATION_SECONDS_CH1}s.")
    myPulsePal.triggerOutputChannels(channel1=1, channel2=1, channel3=0, channel4=0)

    # 4. Wait for the ENTIRE experiment to finish
    finish_time_ch1 = DELAY_SECONDS_CH1 + TRAIN_DURATION_SECONDS_CH1
    finish_time_ch2 = DELAY_SECONDS_CH2 + TRAIN_DURATION_SECONDS_CH2
    total_experiment_time = max(finish_time_ch1, finish_time_ch2)
    
    print(f"\nProtocols initiated. The entire experiment will last for {total_experiment_time} seconds.")
    print("You can close this script now; the Pulse Pal will complete the protocols on its own.")
    print("Waiting here for demonstration purposes...")
    time.sleep(total_experiment_time + 2)

    print("\nExperiment finished.")

except PulsePalError as e:
    print(f"\nERROR: A Pulse Pal error occurred: {e}")
except Exception as e:
    print(f"\nERROR: A general error occurred: {e}")