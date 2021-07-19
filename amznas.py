#!/usr/bin/env python

# Command line utility for Amazonian Nasality project

import os
import re
import subprocess
import yaml
from pathlib import Path
from datetime import datetime as dt
import click

from phonlab.utils import dir2df, get_timestamp_now

datadir = os.path.join(os.environ['HOME'], 'Desktop', 'amznas')

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
    print(f'fnpat: {fnpat}')
    print(f'df:\n{df}')
    if len(df) > 0:
        df['token'] = df['token'].astype(int)
        token = str(df['token'].max() + 1)
    return token

def get_fpath(sessdir, lang, spkr, researcher, yyyymmdd, item):
    '''Construct and return filepath for acquisition .wav file.'''
    token = next_token(sessdir, lang, spkr, researcher, yyyymmdd, item)
    fname = f'{lang}_{spkr}_{researcher}_{yyyymmdd}_{item}_{token}'
    return (os.path.join(sessdir, f'{fname}.wav'), os.path.join(sessdir, f'{fname}.ini'))

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

def run_acq(fpath, inifile):
    '''Run an acquisition.'''
    args = [
        'recorder.exe',
        '-ini', inifile,
        '-of', fpath
    ]
    msg = 'Acquiring. Press Ctrl-C to stop.'
    if seconds is not None:
        args.extend(['-tm', seconds])
        msg = f'Acquiring for {seconds} seconds.'
    print(args)
    print(msg)
    # TODO: remove dummy command
    Path(fpath).touch()
    #subprocess.run(args)

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
def acq(spkr, lang, researcher, item, utt, seconds, lx, no_disp):
    today = dt.strftime(dt.today(), '%Y%m%d')
    sessdir = os.path.join(datadir, lang, spkr, today)
    Path(sessdir).mkdir(parents=True, exist_ok=True)
    fpath, inifile = get_fpath(sessdir, lang, spkr, researcher, today, item)
    ini = get_init(lx, spkr, item, token, utt)
    with open(inifile, 'w') as out:
        out.write(ini)
    run_acq(fpath, inifile)
    # TODO: display acq
    print(f'Touched {fpath}')
    print(f'inifile: {inifile}')
    print(f'spkr: {spkr}')
    print(f'lang: {lang}')
    print(f'researcher: {researcher}')
    print(f'item: {item}')
    print(f'lx: {lx}')
    print(f'no-disp: {no_disp}')
    print(f'today: {today}')

@cli.command()
@click.option('--spkr', callback=validate_ident, help='Three-letter speaker identifier')
@click.option('--lang', callback=validate_ident, help='Three-letter language identifier (ISO 639-3)')
@click.option('--researcher', callback=validate_ident, help='Three-letter researcher (linguist) identifier')
@click.option('--date', help="YYYYMMDD session date")
#@click.option('--token', type=click.Int, help="Token identifier")
@click.option('--item', help='Representation of the stimulus item')
def disp(spkr, lang, researcher, item):
    print('displaying last')

if __name__ == '__main__':
    cli()
