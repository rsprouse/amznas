#!/usr/bin/env python

# Command line utility for Amazonian Nasality project

import os
import re
import subprocess
import yaml
from pathlib import Path
from datetime import datetime as dt
import scipy.io.wavfile
import wave
from eggdisp import egg_display
import click

from phonlab.utils import dir2df, get_timestamp_now

datadir = os.path.join(os.environ['USERPROFILE'], 'Desktop', 'amznas')

class AmzCfg(object):
    '''A config for the Amazon Nasality project.'''
    def __init__(self, datadir=datadir, ymlname='amznas.yml'):
        super(AmzCfg, self).__init__()
        self.datadir = datadir
        self.cfgfile = os.path.join(datadir, ymlname)
        self._lang = None
        self._researcher = None
        try:
            with open(self.cfgfile, 'r') as fh:
                cfg = yaml.safe_load(fh)
            for fld in ('lang', 'researcher'):
                try:
                    assert(re.match('^[a-zA-Z]{3}$', cfg[fld]))
                    setattr(self, f'_{fld}', cfg[fld])
                except AssertionError:
                    msg = f'''
The '{fld}' value must be a 3-character code.
You must correct the value in {self.cfgfile} before continuing.
'''
                    raise RuntimeError(msg)
                except KeyError:
                    print(f'No config default for {fld}.')
        except FileNotFoundError:
            pass

    def prompt_for_save(self, fld, val):
        msg = f'''
You have changed the configuration to:

lang: {val if fld == 'lang' else self.lang}
researcher: {val if fld == 'researcher' else self.researcher}

Save this configuration for next time? (y/n) 
'''
        r = input(msg).strip().lower()
        if r == 'y':
            return True
        elif r == 'n':
            return False
        else:
            return self.prompt_for_save(fld, val)

    def save(self):
        with open(self.cfgfile, 'w') as fh:
            yaml.dump(
                {'lang': self.lang, 'researcher': self.researcher},
                fh,
                default_flow_style=False
            )

    @property
    def lang(self):
        return self._lang

    @lang.setter
    def lang(self, val):
        try:
            assert(re.match('^[a-zA-Z]{3}$', val))
        except AssertionError:
            msg = 'Lang identifier must be a 3-character ISO code.'
            raise RuntimeError(msg)
        if self._lang != val:
            do_save = self.prompt_for_save('lang', val)
        self._lang = val
        if do_save is True:
            self.save()
            print(f'Saved configuration in {self.cfgfile}.')
        else:
            print('Configuration change not saved.')

    @property
    def researcher(self):
        return self._researcher

    @researcher.setter
    def researcher(self, val):
        try:
            assert(re.match('^[a-zA-Z]{3}$', val))
        except AssertionError:
            msg = 'Researcher identifier must be a 3-character code.'
            raise RuntimeError(msg)
        if self._researcher != val:
            do_save = prompt_for_save('researcher', val)
        self._researcher = val
        if do_save is True:
            self.save()
            print(f'Saved configuration in {self.cfgfile}.')
        else:
            print('Configuration change not saved.')

def validate_ident(ctx, param, value):
    if value is None and param.name in ('researcher', 'lang'):
        try:
            value = cfg[param.name]
        except KeyError:
            raise click.BadParameter(f'must be included as a command parameter or in the config file {cfgfile}.')
    try:
        assert(re.match('^[a-zA-Z]{3}$', value))
    except AssertionError:
        raise click.BadParameter(f'Identifier "{value}" must be exactly three characters')
    return value.lower()

def next_token(sessdir, lang, spkr, researcher, yyyymmdd, item):
    '''Get the number of the next token for a .wav acquisition file, as a str.'''
    token = '0'
    # Note that Windows filesystems are case-insensitive. If the project's
    # transcription system distinguishes phone by case, e.g. s vs. S, then it
    # is not possible to distinguish items that differ only in case of one
    # or more characters. As a result we use re.IGNORECASE when matching
    # filenames, and the token count conflates these items.
    fnpat = re.compile(
        f'^{lang}_{spkr}_{researcher}_{yyyymmdd}_{item}_(?P<token>\d+)\.wav$',
        re.IGNORECASE
    )
    df = dir2df(sessdir, fnpat=fnpat)
    if len(df) > 0:
        df['token'] = df['token'].astype(int)
        token = str(df['token'].max() + 1)
    return token

def get_fpath(sessdir, lang, spkr, researcher, yyyymmdd, item, token=None):
    '''Construct and return filepath for acquisition .wav file.'''
    if token == None or token < 0:
        nexttok = next_token(sessdir, lang, spkr, researcher, yyyymmdd, item)
        token = int(nexttok)-1 if token == None else int(nexttok)+token
    fname = f'{lang}_{spkr}_{researcher}_{yyyymmdd}_{item}_{token}'
    return (
        token,
        os.path.join(sessdir, f'{fname}.wav'),
        os.path.join(sessdir, f'{fname}.ini')
    )

def get_ini(lx, spkr, item, token, utt):
    '''Return string rep of ini file.'''
    lxstr = '011' if lx is True else '0'
    return f'''
[Device]
ChannelSelection = 00111001
Lx = {lxstr}
SampleRate = 120000
MICGAIN = 4
LXGAIN = 2
NXGAIN = 4
NXPREAMP = 0

[Subject]
ID = {spkr}
Surname = 
Firstname = 
UtteranceID = {item}_{token}
Utterance = {utt}
'''

def run_acq(fpath, inifile, seconds):
    '''Run an acquisition.'''
    args = [
        os.path.normpath('C:/Users/lingguest/Downloads/Recorder1/Recorder.exe'),
        '-ini', inifile,
        '-of', fpath
    ]
    msg = 'Acquiring. Press Ctrl-C to stop.'
    if seconds is not None:
        args.extend(['-tm', seconds])
        msg = f'Acquiring for {seconds} seconds.'
    try:
        subprocess.run(args)
    except KeyboardInterrupt:
        pass

def wav_display(wav, chan, cutoff, lporder):
    (rate, data) = scipy.io.wavfile.read(wav)
    r = egg_display(
        data,
        rate,
        chan=chan,
        del_btn=None,
        title=wav,
        cutoff=cutoff,
        order=lporder,
        acqfile=wav
    )
    #print(f'egg_display returned "{r}"')

@click.group()
def cli():
    pass

@cli.command()
@click.option('--spkr', callback=validate_ident, help='Three-letter speaker identifier')
@click.option('--lang', callback=validate_ident, help='Three-letter language identifier (ISO 639-3)')
@click.option('--researcher', callback=validate_ident, help='Three-letter researcher (linguist) identifier')
@click.option('--item', help='Representation of the stimulus item')
@click.option('--utt', required=False, default='', help='Utterance metadata (optional)')
@click.option('--seconds', required=False, default='', help='Acquisition duration (optional)')
@click.option('--lx', is_flag=True, help='Turn on LX (EGG) channel')
@click.option('--no-disp', is_flag=True, help='Skip display after acquisition')
@click.option('--cutoff', required=False, default=50, help='Lowpass filter cutoff in Hz (optional; default 50)')
@click.option('--lporder', required=False, default=3, help='Lowpass filter order (optional; default 3)')
def acq(spkr, lang, researcher, item, utt, seconds, lx, no_disp, cutoff, lporder):
    today = dt.strftime(dt.today(), '%Y%m%d')
    sessdir = os.path.join(datadir, lang, spkr, today)
    Path(sessdir).mkdir(parents=True, exist_ok=True)
    token, fpath, inifile = get_fpath(
        sessdir, lang, spkr, researcher, today, item, token=None
    )
    ini = get_ini(lx, spkr, item, token, utt)
    with open(inifile, 'w') as out:
        out.write(ini)
    run_acq(fpath, inifile, seconds)
    chan = ['audio', 'orfl', None, 'nsfl']
    if lx is True:
        chan[2] = 'lx'
    if no_disp is False:
        wav_display(fpath, chan=chan, cutoff=cutoff, lporder=lporder)
    #print(f'Touched {fpath}')
    #print(f'inifile: {inifile}')
    #print(f'spkr: {spkr}')
    #print(f'lang: {lang}')
    #print(f'researcher: {researcher}')
    #print(f'item: {item}')
    #print(f'lx: {lx}')
    #print(f'no-disp: {no_disp}')
    #print(f'today: {today}')

@cli.command()
@click.option('--wavfile', required=False, default=None, help="Input wav file")
@click.option('--spkr', callback=validate_ident, help='Three-letter speaker identifier')
@click.option('--lang', callback=validate_ident, help='Three-letter language identifier (ISO 639-3)')
@click.option('--researcher', callback=validate_ident, help='Three-letter researcher (linguist) identifier')
@click.option('--item', help='Representation of the stimulus item')
@click.option('--date', required=False, default='today', help="YYYYMMDD session date")
@click.option('--token', type=int, required=False, default=None, help="Token identifier")
@click.option('--cutoff', required=False, default=50, help='Lowpass filter cutoff in Hz (optional; default 50)')
@click.option('--lporder', required=False, default=3, help='Lowpass filter order (optional; default 3)')
def disp(wavfile, spkr, lang, researcher, item, date, token, cutoff, lporder):
    '''
    Display an eggd800 wavfile recording. If given, --wav parameter
    identifies the .wav file to display. Otherwise, the name is constructed
    from the other parameters in a way that matches the acq() parameters.

    The --token parameter can be used to specify the token identifier.
    Use -1 to display the last token of a given --item.
    '''
    if wavfile is None:
        if date == 'today':
            date = dt.strftime(dt.today(), '%Y%m%d')
        sessdir = os.path.join(datadir, lang, spkr, date)
        token, wavfile, inifile = get_fpath(
            sessdir, lang, spkr, researcher, date, item, token=token
        )
    chan = ['audio', 'orfl', None, 'nsfl']
    if wave.open(wavfile).getnchannels() == 4:
        chan[2] = 'lx'
    wav_display(wavfile, chan=chan, cutoff=cutoff, lporder=lporder)

if __name__ == '__main__':
    cli()
