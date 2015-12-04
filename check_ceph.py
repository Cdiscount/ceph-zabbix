#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import argparse
import simplejson
import os
import time
import psutil
import re
from subprocess import Popen, PIPE
import os.path

def positive_int(value):
    try:
        ivalue = int(value)
        if ivalue < 0:
            raise argparse.ArgumentTypeError('%s needs to be an integer > 0' % value)
        return ivalue
    except:
        raise argparse.ArgumentTypeError('%s needs to be an integer > 0' % value)

def main():
    parser = argparse.ArgumentParser(description='Ceph monitoring')
    parser.add_argument('-c', '--cache', dest='cache', help='enable cache (in seconds)', type=positive_int, default=0)

    subparsers = parser.add_subparsers(help='sub-command help')

    discover_parser = subparsers.add_parser('discover', help='discover help')
    discover_parser.set_defaults(which='discover')

    monitor_parser = subparsers.add_parser('monitor', help='monitor help')
    monitor_parser.add_argument('-i', '--id', dest='id', help='id', type=str, required=True)
    monitor_parser.add_argument('-s', '--section', dest='section', help='section', type=str, required=True)
    monitor_parser.add_argument('-k', '--key', dest='key', help='key', type=str, required=True)
    monitor_parser.set_defaults(which='monitor')

    args = parser.parse_args()

    try:
        run = False
        lock_file = '/tmp/%s.lock' % (os.path.basename(sys.argv[0]).replace('.py', ''))
        if args.which == 'discover':
            fname = '/tmp/%s_%s.json' % (os.path.basename(sys.argv[0]).replace('.py', ''), args.which)
        else:
            fname = '/tmp/%s_%s_%s.json' % (os.path.basename(sys.argv[0]).replace('.py', ''), args.which, args.id)
        data = {}
        
        if not os.path.isfile(fname) or (int(time.time()) - os.stat(fname)[9]) >= args.cache or args.cache == 0:
            if not os.path.isfile(lock_file):
                f = open(lock_file, 'w')
                f.write('1')
                f.close()
                run = True
            else:
                return
        
        if run:
            if args.which == 'discover':
                data['data'] = []
                for proc in psutil.process_iter():
                    pinfo = proc.as_dict(attrs=['pid', 'name'])
                    if re.match('ceph-.*', pinfo['name']):
                        for c in proc.connections(kind="unix"):
                            m = re.match('.*/ceph-(?P<id>.*).asok', c.laddr)
                            if m:
                                data['data'].append({'{#CEPHID}': m.group('id')})
                if args.cache > 0:
                    j = simplejson.dumps(data)
                    f = open(fname, 'w')
                    f.write(j)
                    f.close()
            else:
                cmd=['ceph', '--admin-daemon', '/var/run/ceph/ceph-%s.asok' % args.id, 'perfcounters_dump']
                p=Popen(cmd, stdout=PIPE, stderr=PIPE)
                (output, err) = p.communicate()
                data = simplejson.loads(output)
                
                if args.cache > 0:
                    j = simplejson.dumps(data)
                    f = open(fname, 'w')
                    f.write(j)
                    f.close()
            os.unlink(lock_file)
        else:
            f = open(fname, 'r')
            data = simplejson.loads(f.read())
            f.close()
            
        # actually print the data
        if args.which == 'discover':
            print simplejson.dumps(data)
        else:
            print data[args.section][args.key]
    except:
        if os.path.isfile(lock_file):
            os.unlink(lock_file)
        print 'KO: %s' % (sys.exc_info()[1])
            
if __name__ == '__main__':
    main()
