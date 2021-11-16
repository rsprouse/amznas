#!/usr/bin/env python

# Command line utility for Amazonian Nasality project

# TODO: check --lx param
# TODO: try to prevent lx recording when not requested

try:
    import os
    import re
    import glob
    import subprocess
    import yaml
    import numpy as np
    from pathlib import Path
    from datetime import datetime as dt
    import scipy.io.wavfile
    import wave
    from eggdisp import egg_display
    import click
    from phonlab.utils import dir2df, get_timestamp_now
except:
    print()
    print('Could not import required modules.')
    print('Try to load them with:')
    print('    conda activate amznas')
    print()
    exit(0)

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

def next_token(sessdir, lang, spkr, researcher, tstamp, item):
    '''Get the number of the next token for a .wav acquisition file, as a str.'''
    date = tstamp.split('T')[0]
    token = '0'
    # 1. Windows filesystems are case-insensitive. If the project's
    # transcription system distinguishes phone by case, e.g. s vs. S, then it
    # is not possible to distinguish items that differ only in case of one
    # or more characters. As a result we use re.IGNORECASE when matching
    # filenames, and the token count conflates these items.
    #
    # 2. Only the date portion of the timestamp is important
    # for determining the token number, and the time portion is ignored.
    fnpat = re.compile(
        f'^{lang}_{spkr}_{researcher}_{date}[^_]*_{item}_(?P<token>\d+)\.wav$',
        re.IGNORECASE
    )
    df = dir2df(sessdir, fnpat=fnpat)
    if len(df) > 0:
        token = df['token'].astype(int).max() + 1
    return str(token)

def get_fpath(sessdir, lang, spkr, researcher, tstamp, item, token=None):
    '''Construct and return filepath for acquisition .wav file.'''
    if token == None or token < 0:
        nexttok = next_token(sessdir, lang, spkr, researcher, tstamp, item)
        token = int(nexttok) if token == None else int(nexttok)+token
    fname = f'{lang}_{spkr}_{researcher}_{tstamp}_{item}_{token}'
    return (
        token,
        os.path.join(sessdir, f'{fname}.wav'),
        os.path.join(sessdir, f'{fname}.ini')
    )

def find_wav(sessdir, lang, spkr, researcher, date, item, token):
    '''Find existing acquisition .wav file.'''
    fre = f'{lang}_{spkr}_{researcher}_{date}T??????_{item}_{token}.wav'
    return glob.glob(os.path.join(sessdir, fre))

def get_ini(lx, spkr, item, token, utt, dev_version):
    '''Return string rep of ini file.'''
    chansel = '00001111' if dev_version == '1' else '00111001'
    lxstr = '011' if lx is True else '0'
    return f'''
[Device]
ChannelSelection = {chansel}
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
        os.path.normpath('C:/bin/Recorder.exe'),
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

def stash_chanmeans(wav, chan, token, sessdir, lang, spkr, researcher, today):
    '''
    Store channel means in a yaml file in the session directory.
    '''
    yamlfile = os.path.join(
        sessdir,
        f'{lang}_{spkr}_{today}_session.yaml'
    )
    try:
        with open(yamlfile, 'r') as fh:
            sessmd = yaml.safe_load(fh)
    except FileNotFoundError:
        sessmd = {
            'session': {
                'spkr': spkr,
                'lang': lang,
            },
            'acq': []
        }
    (rate, data) = scipy.io.wavfile.read(wav)
    cmeans = data.mean(axis=0)
    chanmeans = []
    for cidx, c in enumerate(chan):
        label = 'no_label' if c is None or c == '' else c
        chanmeans.append({
                'idx': cidx,
                'type': label,
                # If we don't cast to float yaml.dump exports the value
                # as a numpy object instead of a simple float.
                'mean': float(cmeans[cidx]),
                'status': 'automean'
            })
    sessmd['acq'].append({
        'item': '_zero_',
        'token': token,
        'researcher': researcher,
        'fname': os.path.basename(wav),
        'channels': chanmeans
    })
    with open(yamlfile, 'w') as fh:
        yaml.dump(sessmd, fh, sort_keys=False)

def load_sess_yaml(sessdir, lang, spkr, today):
    '''
    Load session metadata from yaml file.
    '''
    yamlfile = os.path.join(
        sessdir,
        f'{lang}_{spkr}_{today}_session.yaml'
    )
    try:
        with open(yamlfile, 'r') as fh:
            sessmd = yaml.safe_load(fh)
    except FileNotFoundError:
        sessmd = {
            'session': {
                'spkr': spkr,
                'lang': lang,
            },
            'acq': []
        }
    return sessmd

def wav_display(wav, chan, cutoff, lporder, chanmeans):
    (rate, data) = scipy.io.wavfile.read(wav)
    if len(chanmeans) == data.shape[1]:
        data -= np.array(chanmeans).astype(data.dtype)
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
@click.option('--autozero', required=False, default='0', type=int, help='Remove mean from display using _zero_ token # (optional)')
@click.option('--lx', is_flag=True, help='Turn on LX (EGG) channel')
@click.option('--no-disp', is_flag=True, help='Skip display after acquisition')
@click.option('--cutoff', required=False, default=50, help='Lowpass filter cutoff in Hz (optional; default 50)')
@click.option('--lporder', required=False, default=3, help='Lowpass filter order (optional; default 3)')
@click.option('--dev-version', required=False, default='2', help='EGG-D800 device version (optional; default 2)')
def acq(spkr, lang, researcher, item, utt, seconds, autozero, lx, no_disp, cutoff, lporder, dev_version):
    '''
    Make a recording.
    '''
    today = dt.today()
    todaystamp = dt.strftime(today, '%Y%m%d')
    tstamp = dt.strftime(today, '%Y%m%dT%H%M%S')
    sessdir = os.path.join(datadir, lang, spkr, todaystamp)
    Path(sessdir).mkdir(parents=True, exist_ok=True)
    token, fpath, inifile = get_fpath(
        sessdir, lang, spkr, researcher, tstamp, item, token=None
    )
    ini = get_ini(lx, spkr, item, token, utt, dev_version)
    with open(inifile, 'w') as out:
        out.write(ini)
    run_acq(fpath, inifile, seconds)
    chan = ['audio', 'orfl', None, 'nsfl']
    if lx is True:
        chan[2] = 'lx'
    if item == '_zero_':
        stash_chanmeans(
            fpath,
            chan=chan,
            token=token,
            sessdir=sessdir,
            lang=lang,
            spkr=spkr,
            researcher=researcher,
            today=todaystamp
        )
    if no_disp is False:
        if autozero >= 0 and item != '_zero_':
            sessmd = load_sess_yaml(
                sessdir, lang=lang, spkr=spkr, today=todaystamp
            )
            chanmeans = []
            for a in sessmd['acq']:
                if a['item'] == '_zero_' and a['token'] == autozero:
                    chanmeans = np.zeros(len(a['channels']))
                    for c in a['channels']:
                        if c['type'] in ('orfl', 'nsfl'):
                            chanmeans[c['idx']] = c['mean']
                    break
            if len(chanmeans) == 0:
                print(f"Didn't find _zero_ token {autozero} for the current session!")
        else:
            chanmeans = [] # No adjustment
        wav_display(
            fpath,
            chan=chan,
            cutoff=cutoff,
            lporder=lporder,
            chanmeans=chanmeans
        )

@cli.command()
@click.option('--wavfile', required=False, default=None, help="Input .wav file")
@click.option('--spkr', callback=validate_ident, help='Three-letter speaker identifier')
@click.option('--lang', callback=validate_ident, help='Three-letter language identifier (ISO 639-3)')
@click.option('--researcher', callback=validate_ident, help='Three-letter researcher (linguist) identifier')
@click.option('--item', help='Representation of the stimulus item')
@click.option('--date', required=False, default='today', help="YYYYMMDD session date")
@click.option('--token', type=int, required=False, default=-1, help="Token identifier (optional; defaults to last token)")
@click.option('--autozero', required=False, default='0', type=int, help='Remove mean from display using _zero_ token (optional)')
@click.option('--cutoff', required=False, default=50, help='Lowpass filter cutoff in Hz (optional; default 50)')
@click.option('--lporder', required=False, default=3, help='Lowpass filter order (optional; default 3)')
def disp(wavfile, spkr, lang, researcher, item, date, token, autozero, cutoff,
    lporder):
    '''
    Display an eggd800 wavfile recording. If given, the --wavfile parameter
    identifies the .wav file to display. Otherwise, the name is constructed
    from the other parameters in a way that matches the acq() parameters.

    The --token parameter is used to specify the token identifier.
    Use negative values to count tokens in reverse: -1 for last token,
    -2 for second-to-last, and so on.

    The --autozero parameter is used to specify which _zero_ token from the
    acquisition session to use for calculating the channel means. Use the
    value -1 to indicate that the display should not be adjusted by the
    channel means.
    '''
    if wavfile is None:
        if date == 'today':
            date = dt.strftime(dt.today(), '%Y%m%d')
        sessdir = os.path.join(datadir, lang, spkr, date)
        tokgl = '*' if token < 1 else token
        wavfiles = find_wav(sessdir, lang, spkr, researcher, date, item, tokgl)
        if len(wavfiles) == 0:
            print('Could not find a matching .wav file.')
            exit(0)
        elif len(wavfiles) > 1 and tokgl == '*':
            try:
                wavfile = wavfiles[token]
            except IndexError:
                print(f'Could not find matching file with token index {token}.')
                exit(0)
        elif len(wavfiles) > 1:
            print('Multiple matching files found. Use the --wavfile param and '
                  'specify one of:\n')
            print('\n'.join(wavfiles))
            exit(0)
        else:
            wavfile = wavfiles[0]
    chan = ['audio', 'orfl', None, 'nsfl']
    if wave.open(wavfile).getnchannels() == 4:
        chan[2] = 'lx'
    if autozero >= 0:
        sessmd = load_sess_yaml(sessdir, lang=lang, spkr=spkr, today=date)
        chanmeans = []
        for a in sessmd['acq']:
            if a['item'] == '_zero_' and a['token'] == autozero:
                chanmeans = np.zeros(len(a['channels']))
                for c in a['channels']:
                    if c['type'] in ('orfl', 'nsfl'):
                        chanmeans[c['idx']] = c['mean']
                break
        if len(chanmeans) == 0:
            print(f"Didn't find _zero_ token {autozero} for the session!")
    else:
        chanmeans = [] # No adjustment
    wav_display(
        wavfile,
        chan=chan,
        cutoff=cutoff,
        lporder=lporder,
        chanmeans=chanmeans
    )

if __name__ == '__main__':
    cli()
