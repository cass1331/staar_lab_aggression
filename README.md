
# staar_lab_aggression

## We’re testing how brief pulses of light alter whether an animal initiates a fight, and how long attacks last.

## ArCOM.py

Read/write for Arduino

## `pulse_pal.py`

Define interactions for PulsePal

## `run_red_blue_pulse.py`

Define interactions for PulsePal and get trigger timestamps logged

## `run_red_blue_pulse_timed.py``

Define interactions for PulsePal and get trigger timestamps logged, also controls camera/image acquistion
and logs camera timestamp for each frame

## `CameraTimeToPCTime`

Example/included code from Spinnaker


Light conditions
- We’ll use one LED (one PulsePal port).
- Blue light: 20 Hz stimulation (to release 5HT in the MEA).
- Red light: Pulses of 2 s ON / 0.5 s OFF (to briefly inhibit 5HT in the MEA).
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
- Playing multiple trials automatically
- User-controlled number of trials (button GUI)
- Synced timestamps (I think this should work correctly now)

## Things to do
- Configure stop button in case we need to end a trial early
- Control number of total frames/time from GUI
- Run with PulsePal connected to check that it actually works

## Small notes
- Install PySpin first. This is tricky because there's a PyPi called *pyspin* which is not the right package. PySpin actually comes preinstalled with Spinnaker IIRC and you have to install the correct one for your computer with pip from wheels.
- 

## Big Note!

Apparently, only one 'application' can control the camera at once. To have the script retrieve the camera 
timestamps, configure the camera settings in SpinView, close SpinView, and then run the script (run_red_blue_pulse_timed.py), which will take care of everything, including image acquistion.


