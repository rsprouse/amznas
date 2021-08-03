# amznas
Files and scripts for Amazonian Nasality project

## Installation

(Windows only)

1. Open an Anaconda Prompt from the Start Menu.
1. Clone the repository: `git clone https://github.com/rsprouse/amznas`
1. Prepare the `amznas` Anaconda environment:
   a. For first time creation: `conda env create -f amznas\environment.yml`
   a. Update an existing environment: `conda env update -f amznas\environment.yml --prune`

Also, `Recorder.exe` from laryngograph.com must be copied to the `C:\Users\lingguest\bin` directory.

## Running the `amznas` acquisition utility

1. Open an Anaconda Prompt from the Start Menu.
1. Activate the `amznas` environment: `conda activate amznas`
1. Make an acquisition: `python amznas\amznas.py --researcher XXX --lang YYY --spkr ZZZ --item ITEM`

## Data

Recordings are stored in session folders under `C:\Users\lingguest\Desktop\amznas`. Session folders are created under the relative path `ISO\SPK\YYYYMMDD`, where `ISO` is the language ISO code, `SPK` is the speaker initials, and `YYYYMMDD` is the date of the acquisition.

Within the session folders, filenames are of the form `ISO_SPK_YOU_YYYYMMDDTHHHMMSS_ITEM_TOKEN`, where `ISO` and `SPK` are the same as in the path, `YYYYMMDDTHHMMSS` is the date and timestamp of the acquisition, `ITEM` identifies the content of the acquisition, and `TOKEN` is the instance of the `ITEM` in the session. Tokens are numbered automatically, starting at `0`.

The Windows filesystem is not case-sensitive, so `ITEM` values that differ only in case are treated as identical when token numbers are calculated. Keep that in mind if your transcription system is case-sensitive.
