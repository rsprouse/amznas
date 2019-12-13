# Working with the EGG-D800

## General principles

- The EGG-D800 provides an indirect method of measuring airflow.
- The Rothenberg mask provides some resistance to airflow, creating backpressure inside the mask.
- The mask is divided into oral and nasal chambers.
- The greater the airflow into each chamber, the greater the backpressure.
- The EGG-D800 measures the pressure of each chamber.

## Properties of the Rothenberg mask

- Constructed of silicone.
- Soft and flexible to conform to the face.
- Adult and child sizes.
- Multiple vents covered with fine mesh to allow airflow and provide resistance to create backpressure.
- The backpressure created in the masks is low and not noticeable to the speaker.
- The mask itself obviously is noticeable to speakers!
- The audio quality is better for these masks than for hard masks, but muffled.

## Properties of the EGG-D800

- Audio data in the left channel (1).
- LX data in the right channel (2).
- Has two pressure transducers that can be turned on.
- Small, portable.
- Powered by USB bus. Can run on a laptop using battery power.
- USB audio device. Can acquire data with any audio recorder, e.g. Praat, Audacity, `sox` (in the form of `rec`).
  - It is critical to use the correct recording parameters! For this project, this means 2 channels, 16 bits per sample, and 48000 Hz sample rate.
- When transducers are turned on, the pressure signals are interleaved with the audio/lx signals.
- Signals must be de-interleaved after acquisition.
- P1 channel has +/- ports. P2 channel has one port.
- P1 channel is more sensitive than P2.

## Overall workflow

1. Prepare a directory for the acquisition session.
1. Attach the EGG-D800 to the computer.
1. Configure the EGG-D800. Turn on the pressure transducers and set the microphone volume.
1. Record an acquisition. (Start with a test acq, then a zero calibration acq.)
1. View the acquisition to check for trouble conditions.
1. If the acquisition is not usable, delete it and redo it.
1. Repeat the previous two steps until done.

## Specific steps

### Acquisition

1. Make acquisition directory: Use File Explorer or `mkdir {YYYYMMDD}_{subject}`
1. Configure: `eggrec --aero --mic-gain 24`
1. Record: `rec -c 2 -b 16 -r 48000 {YYYYMMDD}_{subject}_{prompt}.{token}.wav`
1. View: `python C:\bin\eggdisp.py {YYYYMMDD}_{subject}_{prompt}.{token}.wav`
1. (Delete): Use File Explorer or `del {YYYYMMDD}_{subject}_{prompt}.{token}.wav`

### Postprocessing

When acquisition session is complete, sparate airflow channels from audio/lx: `python C:\bin\eggsep.py --seek .`

## Making a test recording

- Make a short recording with the consultant and view the result.
- Check for:
  - Quality of audio signal.
  - Quality of oral airflow signal.
  - Quality of nasal airflow signal.
  - Make sure oral and nasal airflow are in the correct channels.
  - Make sure oral and nasal airflow signals are not inverted.

## Troubleshooting

- Inspect the mask prior to use and occasionally during use to ensure the screens have not come out or loose.
- Communicate with subject throughout to ensure the speaker remains comfortable.
- Symptom: No audio or very low amplitude.
  - Cause: The mic is not plugged in to the EGG-D800.
  - Cause: Improper mic placement.
  - Cause: Low mic gain. Re-run `eggrec` with `--mic-gain 24` parameter.
- Symptom: No airflow signals.
  - Cause: EGG-D800 not configured. Re-run the `eggrec` command with the `--aero` parameter
  - Cause: Improper seal. Check mask placement.
  - Cause: Vent screen missing or loose. 
  - Cause: Pressure tubes not connected to mask or EGG-D800.
- Symptom: Weak airflow signal in one channel.
  - Cause: Improper seal. Check mask placement.
  - Cause: Vent screen missing or loose. 
  - Cause: Oral and nasal channels are reversed. The P1 channels is more sensitive than the P2 channel.
- Symptom: Weak airflow signal in both channels.
  - Cause: Improper seal. Check mask placement.
  - Cause: Vent screen missing or loose. 
  - Cause: Speaker does not speak with enough force. Check posture and ask speaker to speak louder.
- Symptom: Airflow signal is inverted.
  - Cause: Pressure tube is connected to the wrong P1 port.
- Symptom: The airflow channels are identical to the audio.
  - Cause: The recording is from the built-in audio device instead of the EGG-D800. Make sure the USB connection between the EGG-D800 and computer is secure at both ends.
  - Cause: EGG-D800 not configured. Re-run the `eggrec` command with the `--aero` parameter.

## Cleaning?

In human subjects protocol?
