# amznas
Files and scripts for Amazonian Nasality project

## Installation

(64-bit Windows only)

1. Open an Anaconda Prompt from the Start Menu.
1. Clone the repository: `git clone https://github.com/rsprouse/amznas`
1. Prepare the `amznas` Anaconda environment:
    * For first time creation: `conda env create -f amznas\environment.yml`
    * To update an existing environment: `conda env update -f amznas\environment.yml --prune`

Also, `Recorder.exe` from laryngograph.com must be copied to the `C:\bin` directory.

## Running the `amznas` acquisition utility

1. Open an Anaconda Prompt from the Start Menu.
1. Activate the `amznas` environment: `conda activate amznas`
1. Make an acquisition:
    * Unlimited duration: `python amznas\amznas.py acq --researcher XXX --lang YYY --spkr ZZZ --item ITEM`
    * Specified duration in seconds: `python amznas\amznas.py acq --researcher XXX --lang YYY --spkr ZZZ --seconds 5 --item ITEM`
    * (For Marina and Thiago, who have the older EGG-D800 device, add the parameter `--dev_version 1`)

## Data

Recordings are stored in session folders under `C:\Users\lingguest\Desktop\amznas`. Session folders are created under the relative path `ISO\SPK\YYYYMMDD`, where:
* `ISO` is the language ISO code
* `SPK` is the speaker initials
* `YYYYMMDD` is the date of the acquisition.

Within the session folders, filenames are of the form `ISO_SPK_YOU_YYYYMMDDTHHHMMSS_ITEM_TOKEN`, where:
* `ISO` and `SPK` are the same as in the path
* `YOU` is the researcher (you)
* `YYYYMMDDTHHMMSS` is the date and timestamp of the acquisition
* `ITEM` identifies the content of the acquisition
* `TOKEN` is the instance of the `ITEM` in the session. Tokens are numbered automatically, starting at `0`.

The Windows filesystem is not case-sensitive, so `ITEM` values that differ only in case are treated as identical when token numbers are calculated. Keep that in mind if your transcription system is case-sensitive.

## Troubleshooting

If you get a `ModuleNotFoundError`, there is a good chance that you did not start an Anaconda Prompt or did not activate the `amznas` environment. Try repeating the steps in the 'Running the `amznas` acquisition utility' section.

If you get `Error: No such option: <option>`:
1. Check to see if the option name was mistyped.
1. Check to see whether you included a valid subcommand name (usually `acq`) to the script, e.g. `python amznas\amznas.py acq ...`.
