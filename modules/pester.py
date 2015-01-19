#!/usr/bin/python3
"""
pester.py - Pester module
Author - mandarj
"""

import os, sqlite3
from datetime import datetime

def setup(self):
    fn = self.nick + '-' + self.config.host + '.pester.db'
    self.pester_db = os.path.join(os.path.expanduser('~/.phenny'), fn)
    self.pester_conn = sqlite3.connect(self.pester_db)

    c = self.pester_conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS to_pester (pesteree TEXT, pesterer TEXT, reason TEXT, dismissed TEXT, last_pestered TEXT, created TEXT);''')


def start_pester(phenny, input):
    start_pester.conn = sqlite3.connect(phenny.pester_db)
    c = start_pester.conn.cursor()

    c.execute('''SELECT * FROM to_pester WHERE pesteree=? AND pesterer=?''', [input.group(2), input.nick])
    if c.fetchall() == []:
        current_time = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        c.execute('''INSERT INTO to_pester VALUES(?,?,?,?,?,?);''', [input.group(2), input.nick, input.group(3), current_time, "", current_time])
        start_pester.conn.commit()
        msg = input.nick + ": I will start pestering " + input.group(2) + " " + input.group(3)
        phenny.say(msg)
    else:
        phenny.say(input.nick + ': You are already pestering ' + input.group(2))
        
    start_pester.conn.commit()
    start_pester.conn.close()
start_pester.conn = None
start_pester.rule = ('$nick', ['pester'], r'(\S+) (.*)')


def pester(phenny, input):
    pester.conn = sqlite3.connect(phenny.pester_db)
    c = pester.conn.cursor()

    pesterees = []
    c.execute('''SELECT pesteree FROM to_pester''')
    for name in c.fetchall():
        pesterees.append(name[0])

    if input.nick in pesterees:
        reasons = []
        c.execute('''SELECT reason FROM to_pester WHERE pesteree=?''',
                [input.nick])
        for reason in c.fetchall():
            reasons.append(reason[0])
            
        for reason in reasons:
            pesterers = []
            c.execute('''SELECT pesterer FROM to_pester WHERE pesteree=? AND reason=?''', (input.nick, reason))
            for name in c.fetchall():
                pesterers.append(name[0])
            
            for pesterer in pesterers:
                c.execute('''SELECT dismissed FROM to_pester WHERE pesteree=? AND pesterer=? AND reason=?''', (input.nick, pesterer, reason))
                last_dismissed = c.fetchall()[0][0]
                current_time = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
                c.execute('''SELECT created FROM to_pester WHERE pesteree=? AND pesterer=? AND reason=?''', (input.nick, pesterer, reason))
                created_str = c.fetchall()[0][0]
                if last_dismissed == "":
                    c.execute('''SELECT last_pestered FROM to_pester WHERE pesteree=? AND pesterer=? AND reason=?''', (input.nick, pesterer, reason))
                    last_pester_str = c.fetchall()[0][0]
                    try:
                        last_pestered = datetime.strptime(last_pester_str, "%Y-%m-%d %H:%M:%S")
                    except ValueError:
                        pass
                    delta = last_pestered - datetime.utcnow()
                    difference = delta.total_seconds() / 60 # in minutes
                    if abs(difference) > phenny.config.minutes_to_pester:
                        msg = input.nick + ': (' + created_str + ') ' + pesterer + ' pesters you ' + reason
                        phenny.say(msg)
                        c.execute('''UPDATE to_pester SET last_pestered=? WHERE pesteree=? AND pesterer=? AND reason=?''',
                                (current_time, input.nick, pesterer, reason))
                        pester.conn.commit()
                else:
                    dismissed = datetime.strptime(last_dismissed, "%Y-%m-%d %H:%M:%S")
                    delta = dismissed - datetime.utcnow()
                    difference = delta.total_seconds() / 60 # in minutes
                    if abs(difference) > phenny.config.pester_after_dismiss:
                        msg = input.nick + ': (' + created_str + ') ' + pesterer + ' pesters you ' + reason
                        phenny.say(msg)
                        c.execute('''UPDATE to_pester SET last_pestered=? WHERE pesteree=? AND pesterer=? AND reason=?''',
                                (current_time, input.nick, pesterer, reason))
                        c.execute('''UPDATE to_pester SET dismissed=? WHERE pesteree=? AND pesterer=? AND reason=?''', ("", input.nick, pesterer, reason))
                        pester.conn.commit()
    else:
        pass
pester.rule = r'(.*)'

def pesters(phenny, input):
    pesters.conn = sqlite3.connect(phenny.pester_db)
    c = pesters.conn.cursor()
    if input.group(1) == 'snooze':
        current_time = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        if c.execute('''SELECT * FROM to_pester WHERE pesteree=? AND pesterer=?''', [input.nick, input.group(2)]).fetchall() == []:
            phenny.say(input.nick + ': You are not being pestered by ' + input.group(2))
        else:
            c.execute('''UPDATE to_pester SET dismissed=? WHERE pesteree=? AND pesterer=?''', [current_time, input.nick, input.group(2)])
            phenny.say(input.nick + ': Pester snoozed. Pester will recur in ' + str(phenny.config.pester_after_dismiss) + ' minutes.')
        
    elif input.group(1) == 'dismiss':
        if c.execute('''SELECT * FROM to_pester WHERE pesteree=? AND pesterer=?''', [input.group(2), input.nick]).fetchall() == []:
            phenny.say(input.nick + ': You are not pestering ' + input.group(2))
        else:
            c.execute('''DELETE FROM to_pester WHERE pesteree=? AND pesterer=?''', [input.group(2), input.nick])
            phenny.say(input.nick + ': Stopped pestering ' + input.group(2))
            
    pesters.conn.commit()
pesters.rule = r'[.]pesters (snooze|dismiss) (\S+)'

def admin_stop(phenny, input):
    admin_stop.conn = sqlite3.connect(phenny.pester_db)
    c = admin_stop.conn.cursor()
    if input.nick in phenny.config.admins:
        if c.execute('''SELECT * FROM to_pester WHERE pesteree=? AND pesterer=?''', (input.group(2), input.group(1))).fetchall == []:
            phenny.say(input.nick + ': ' + input.group(1) + ' is not pestering ' + input.group(2))
        else:
            c.execute('''DELETE FROM to_pester WHERE pesteree=? AND pesterer=?''', (input.group(2), input.group(1)))
            phenny.say(input.nick + ': ' + input.group(1) + ' is no longer pestering ' + input.group(2))
            admin_stop.conn.commit()
    else:
        phenny.say('You need to be admin to perform this function.')
admin_stop.rule = r'[.]pesters stop (\S+) to (\S+)'
