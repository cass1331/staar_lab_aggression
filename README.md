# staar_lab_aggression

#We’re testing how brief pulses of light alter whether an animal initiates a fight, and how long attacks last.

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


