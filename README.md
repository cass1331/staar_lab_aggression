
# staar_lab_aggression

## We’re testing how brief pulses of light alter whether an animal initiates a fight, and how long attacks last.

### Files to note:

## `ArCOM.py`

Read/write for Arduino

## `pulse_pal.py`

Define interactions for PulsePal

## `run_on_demand_20hz.py`

Define interactions for PulsePal and get trigger timestamps logged (PC only)

## `run_on_demand_20hz_timed.py`

Define interactions for PulsePal and get trigger timestamps logged, also controls camera/image acquistion
and logs camera timestamp for each frame. 

## `CameraTimeToPCTime`

Example/included code from Spinnaker, edited for our purposes.

# Specifications

Light conditions
- We’ll use one LED (one PulsePal port).
- Blue light: 20 Hz stimulation (to release 5HT in the MEA). (ChR2)
- Red light: Pulses of 2 s ON / 0.5 s OFF (to briefly inhibit 5HT in the MEA). (NphR)
- These parameters should be easy to adjust later if needed.

Pulse set structure
- Each pulse set should last 10 seconds total (this matches the average attack duration).
- Pulse sets should be triggered with a simple command that can be repeated throughout the session.
- No cooldown or forced pauses between sets.

Timestamps & logging
- Each time a pulse set is triggered, the code should save a timestamp (start time) to a text file.
- The file should be saved automatically to a specified filepath at the end of the recording session.

Trial logic
- On 50% of triggers, the LED should not actually turn on. This will serve as our control to test if the manipulation worked.

Potential challenge
- The hardest part may be matching the saved trigger timestamps with the behavioral videos. If Avis embeds a timestamp/clock in the videos, that could be a good way to sync with the CSV outputs. Or maybe a strategy where we trigger the camera and the python script that triggers the led and saves the text file at the same time. Please go whatever direction you think would be best!

## Things implemented
- Configuring/playing pulses
- Timestamp logging
- Randomly turning on/off LED
- User-controlled number of trials (button GUI)
- Synced timestamps (I think this should work correctly now)
- Works with PulsePal 
- User input trial success (on terminal/command line since it's not really worth to to thread GUIs). Not pretty but functional.
- Actual camera trigger works (only with Spinnaker 4.2/PySpin installed from wheels for whatever reason)
- Writing to video via script
- Getting camera timestamps

## Things that should be functional but I need to test and make sure
- Setting number of frames from user input
- Stop and save button
- Displaying video while camera is streaming

## Things to do
- There are also cosmetic improvements to make it more user-friendly, but they are low priority.

## Small notes, dependencies
- Install PySpin first. This is tricky because there's a PyPi package online called *pyspin* which is not the right package. PySpin actually comes preinstalled with Spinnaker SDK IIRC and you have to install the correct one for your computer with pip from wheels.
- However, since I can't find it on the lab computer/old version of Spinnaker, it turns out you can install it with `pip install spinnaker-python`. (This may or may not work with these scripts.)
- Also requires pyserial (installed w Conda or pip), opencv, etc

## Big Note!

Apparently, only one 'application' can control the camera at once. To have the script retrieve the camera timestamps, configure the camera settings in SpinView, close SpinView, and then run the script (run_red_blue_pulse_timed.py), which will take care of everything, including image acquistion, with some very barebones GUIs.


