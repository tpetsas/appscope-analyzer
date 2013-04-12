#!/usr/bin/env python

"""
 appscope-analyzer is a command-line tool that parses the Appscope logs
 abd produces per process (PID) or per application (UID) power consumption
 data.

 AppScope project aims to develop a suite of software tools for estimating
 the energy consumption of application running on Android smartphone. For
 more information about the project you can visit the official web site:
 http://css3.yonsei.ac.kr:5612/appscope

"""

from __future__ import with_statement

import os, re, sys, hashlib
from itertools import groupby, imap
from operator import itemgetter
from optparse import OptionParser, OptionGroup

# for the xml parsing
import xml.etree.ElementTree as ET
from operator import itemgetter

# for files listing
import glob

import sys
import logging

# some macros
float_template = "%8.4f"
int_template = "%d"

# Utilities funtions

def _bold(msg):
  """
    _bold(msg)

    arguments:
    msg         -- the message to be in bold

    returns the message in bold

  """
  return u'\033[1m%s\033[0m' % msg

def _sum(seq):
  """
    _sum(seq)

    arguments:
    seq          -- a sequence of numbers (NOT strings) or lists of numbers

   if sequence of numbers is provided returns the result of the Python's
   built-in sum function. If a sequence of lists of numbers is provided
   returns the sum of the resulted zipped list if calling the zip function

  """
  if type(seq[0]) is list:
    return [sum(a) for a in zip(*seq)]
  else:
    return sum(seq)


def _combine_duplicate_time_samples (samples, key='time'):
  """
    _combine_duplicate_time_samples (samples)

    arguments:
    samples              -- a dictionary with the sample lists
    key                  -- the key list to be used for the comparison

    sum up n same sized lists based contained in a dictionary
    based on identical elements of the one given by a dictionary
    key

  """
  # required modules:
  # from itertools import groupby
  # from operator import itemgetter

  # construct a list with all the key names (starting from 'time')
  keys = ['time'] + [key for key in samples.keys() if key!='time']
  # construct a list with all the keys' lists (starting from the one of 'time')
  keys_lists = [ samples['time'] ] + [samples[key] for key in samples.keys() if key!='time']
  groups = groupby(zip(*keys_lists), key=itemgetter(0))
  lists = zip(*[[k] + map(_sum, zip(*g)[1:]) for k, g in groups])
  new_d = dict(zip((keys), lists))
  return new_d



def _new_stats_dict():
  """
    _new_stats_dict function

    creates a new stats dictionary containing 6 lists with
    the following keys: time, cpu, display, gps, wifi, 3g
  """
  return {'time':[],
          'cpu':[],
          'display':[],
          'gps':[],
          'wifi':[],
          '3g':[]
         }

def _new_stats_dict():
  """
    _new_stats_dict function

    creates a new stats dictionary containing 18 lists with
    the following keys: vtime, pid, tgid, uid, cpu_ticks, disp,
    gps, wifi_snd_pkts, wifi_rcv_pkts, 3g_low, 3g_high, calling,
    cpu_en, display_en, gps_en, wifi_en, 3g_en, total_en

  """
  return {'time':[],
          'pid':[],
          'tgid':[],
          'uid':[],
          'cpu_ticks':[],
          'disp':[],
          'gps':[],
          'wifi_snd_pkts':[],
          'wifi_rcv_pkts':[],
          '3g_low':[],
          '3g_high':[],
          'calling':[],
          'cpu_en':[],
          'display_en':[],
          'gps_en':[],
          'wifi_en':[],
          '3g_en':[],
          'total_en':[]
         }

def _max_size (l, title):
  if title == "CPU TICKS":
    cpu_ticks = '|%s|' % ' '.join(map(str, l))
  elif title in ['CPU', 'DISPLAY', 'GPS', 'WIFI', '3G', 'TOTAL']:
    l = [float_template % float(value) for value in l]
  else:
    l = [int_template % value for value in l] 
  comb_list = l+[title]
  return len( "%s" % max(comb_list) )


class LogStats:
  """
    LogStats (class)
    
    A structure that holds information about the usage and power
    of an app extracted from the AppScope logs
  """

  def __init__(self, sourcedir, verbose, quiet, pid, uid, app, grep):
    """
      Constructor of LogStats objects

      Creates a new LogStats object
    """

    # initiate the data structures
    self.stats = _new_stats_dict()

    self.sourcedir = sourcedir
    self.verbose = verbose
    self.quiet = quiet
    self.pid = pid
    self.uid = uid
    self.app = app
    self.grep = grep
 

  def _get_pids (self):
    """
      _get_pids

      parse usage (raw) logs and returns a list with all
      the available PIDs followed by their UIDs

    """
    # try to read the usage (raw) file
    # make a sorted lists with all the usage (raw) and power log files
    raw_files = sorted(glob.glob('%s/[0-9]*/raw/[0-9]*' % self.sourcedir))
    pid_dict = dict()
    for raw_fn in raw_files:
      with open(raw_fn) as raw_f:
        raw_lines = raw_f.readlines()[1:]
        for r_line in raw_lines:
          # extract information from the usage log
          r_line = r_line.strip()
          # get the first column
          PID, TGID, UID, rest = r_line.split(" ", 3)
          # insert PID, UID mapping in the dictionary
          if not pid_dict.has_key(PID):
            pid_dict[PID] = UID
    return pid_dict



  def _parse_packages_xml (self):
    """
      _parse_packages_xml

      parse packages.xml file and returns a list of tuples
      with the monitored UIDs and the corresponding package
      names of those apps

    """
    # try to read the packages.xml file
    pxml_path = "%s/packages.xml" % self.sourcedir
    try:
      xmltext = open(pxml_path).read()
    except IOError, e:
      print "\nNo packages.xml file found in %s.\nChange the source directory (%s -h for more information)\n" % (pxml_path, sys.argv[0])
      sys.exit(1)

    root = ET.fromstring(xmltext)

    # Top-level elements
    root.findall(".")

    # packages elements
    packages = root.findall("./package")

    # list of tuples
    app_list = []

    for package in packages:
      pkg_name = package.get('name')
      uid = package.get('userId')
      if not uid:
        uid = package.get('sharedUserId')
      app_list.append( (uid, pkg_name)  )

    return app_list

  def print_line(self, line):
    """
      print_line(line)
      
      searche for the grep pattern if set in the
      line and print it. Otherwise, print the line

      arguments:
      line           -- the line to pe printed

    """
    try:
      # if grep otpion is enable, search for the
      # given pattern in the line
      if self.grep:
        # only if pattern is found, print the line
        if self.grep.lower() in line.lower():
          print line
      # if no grep option given, just print the line 
      else:
        print line
      if sys.stdout: sys.stdout.flush()
    except IOError:
      sys.exit(0)



  def print_apps_list (self):
    """
      print_apps_list

      print out a nicely formatted list of the monitored
      apps (packages, UIDs, PIDs)

    """
    app_list = self._parse_packages_xml()
    app_dict = dict(app_list)
    # explicitly add the system UID
    app_dict['0']='system'

    uids, names = zip(*app_list)
    # find max size of pacjage names
    max_name = len( "%s" % max(names, key=len) )
    # find the max size of uids 
    max_uid = len( "%s" % max(uids) )
    # find the max size of pids
    pids = self._get_pids()
    max_pid = len("%s" % max(pids))
    pids_sorted = sorted(int(pid) for pid in pids.keys())
    data = list()
    for pid in pids_sorted:
      pid = str(pid)
      # PID to UID mapping
      uid = pids[pid]
      if uid == '0' and not self.verbose:
        continue
      # UID to app package name mapping
      try:
        app = app_dict[uid]
      except KeyError, e:
        app = '?'
      data.append((pid, uid, app))

    # template for print formatting based on the max fields' values
    # non quite mode: print pid, uid and app package name
    if not self.quiet:
      template = "{0:%d}\t{1:%d}\t{2:%d}" % (max_pid, max_uid, max_name)
      print template.format("PID", "UID", "APP PACKAGE")
      for app in data:
        pid, uid, pname = app
        output_line =  template.format(pid, uid, pname)
        self.print_line(output_line)
    else: # quiet mode: print only uid and app package name
      template = "{0:%d}\t{1:%d}" % (max_uid, max_name)
      print template.format("UID", "APP PACKAGE")
      for app in data:
        pid, uid, pname = app
        output_line = template.format(uid, pname)
        self.print_line(output_line)


  def check_app_input(self):
    """
      check_app_input

      Checks if the provided arguments (pid, uid, app package name)
      are valid

    """
    # parse xml file and construct a list of the monitored apps
    app_list = self._parse_packages_xml()

    # create dict with package name->UID (reverse) mapping
    app_dict = {}
    for uid, name in app_list:
      app_dict[name] = uid
    # create a dict with all the PIDs and the corresponding
    # UIDs
    pid_dict = self._get_pids()

    if self.pid:
      try:
        self.uid = pid_dict[self.pid]
      except:
        print "\n PID: %s not found in AppScope log files.\n\n" % self.pid
        sys.exit(1)
      uid_to_app = dict((uid, name) for name, uid in app_dict.iteritems())
      try:
        self.app = uid_to_app[self.uid]
      except:
        # TODO: check this case!
        self.app = '?'
    elif self.uid:
      if not self.uid in app_dict.values():
        print "\n UID: %s not found in AppScope log files.\n\n" % self.uid
        sys.exit(1)
      # set only app package name, skip PID
      # to show power at application level
      try:
        uid_to_app = dict((uid, name) for name, uid in app_dict.iteritems())
      except:
        print "\n UID: %s not found in AppScope log files.\n\n" % self.uid
        sys.exit(1)
      self.app = uid_to_app[self.uid]

    elif self.app:
      # set only UID from app package name
      # to show power at application level
      try:
        self.uid = app_dict[self.app]
      except:
        print "\n App package name: %s not found in AppScope log files.\n\n" % self.app
        sys.exit(1)
      print self.pid, self.uid, self.app




  def print_stats(self):
    """
      print_stats

     print the statistics dicitonary formatted and at the
     chosen level

    """
    # iterate the sorted list of timestamps
    timestamps = sorted(self.stats['time'])
    first = timestamps[0]
    last = timestamps[len(timestamps)-1]

    max_time = _max_size( self.stats['time'], 'TIME')
    max_pid = _max_size( self.stats['pid'], 'PID' )
    max_tgid = _max_size( self.stats['tgid'], 'TGID' )
    max_uid = _max_size( self.stats['uid'], 'UID' )
    cpu_ticks_str = ['|%s|'  % ' '.join( map(str, elem) ) for elem in self.stats['cpu_ticks']]
    max_cpu_ticks = _max_size( cpu_ticks_str, 'CPU TICKS' )
    max_disp = _max_size( self.stats['disp'], 'DISPLAY (US)' )
    max_gps = _max_size( self.stats['gps'], 'GPS (US)' )
    max_wifi_snd_pkts = _max_size( self.stats['wifi_snd_pkts'], 'WIFI SND PKTS' )
    max_wifi_rcv_pkts = _max_size( self.stats['wifi_rcv_pkts'], 'WIFI RCV PKTS' )
    max_g3_low = _max_size( self.stats['3g_low'], '3G LOW' )
    max_g3_high = _max_size( self.stats['3g_high'], '3G HIGH' )
    max_calling = _max_size( self.stats['calling'], 'CALLING' )
    max_cpu_en = _max_size( self.stats['cpu_en'], 'CPU' )
    max_display_en = _max_size( self.stats['display_en'], 'DISPLAY' )
    max_gps_en = _max_size( self.stats['gps_en'], 'GPS')
    max_wifi_en = _max_size( self.stats['wifi_en'], 'WIFI' )
    max_g3_en = _max_size( self.stats['3g_en'], '3G' )
    max_total_en = _max_size( self.stats['total_en'], 'TOTAL' )

    if not self.quiet and not self.verbose:
      template = "{0:%d}\t{1:%d}\t{2:%d}\t{3:%d}\t{4:%d}\t{5:%d}\t{6:%d}" % (\
      max_time, max_cpu_en, max_display_en, max_gps_en, max_wifi_en, max_g3_en, max_total_en)
      print template.format('TIME', 'CPU', 'DISPLAY', 'GPS', 'WIFI', '3G', 'TOTAL')
    elif self.quiet:
      template = "{0:%d}\t{1:%d}" % (max_time, max_total_en)
      print template.format('TIME', 'TOTAL POWER CONSUMPTION')
    elif self.verbose:
      template = "{0:%d}\t{1:%d}\t{2:%d}\t{3:%d}\t{4:%d}\t{5:%d}\t{6:%d}\t{7:%d}\t{8:%d}\t{9:%d}\t{10:%d}\t{11:%d}\t{12:%d}\t{13:%d}\t{14:%d}" % (\
      max_time, max_cpu_ticks, max_disp, max_gps, max_wifi_snd_pkts, max_wifi_rcv_pkts,\
      max_g3_low, max_g3_high, max_calling, \
      max_cpu_en, max_display_en, max_gps_en, max_wifi_en, max_g3_en, max_total_en)
      print template.format('TIME', 'CPU TICKS', 'DISPLAY (US)', 'GPS (US)', 'WIFI SND PKTS', \
      'WIFI RCV PKTS', '3G LOW', '3G HIGH', 'CALLING', \
      'CPU', 'DISPLAY', 'GPS', 'WIFI', '3G', 'TOTAL')
     



    for index in range( len(self.stats['time']) ):
      # extract values
      time = int_template % self.stats['time'][index]
      pid = int_template % self.stats['pid'][index]
      tgid = int_template % self.stats['tgid'][index]
      uid =  int_template % self.stats['uid'][index]
      cpu_ticks = self.stats['cpu_ticks'][index]
      cpu_ticks = '|%s|' % ' '.join(map(str, cpu_ticks))
      disp = int_template % self.stats['disp'][index]
      gps = int_template % self.stats['gps'][index]
      wifi_snd_pkts = int_template % self.stats['wifi_snd_pkts'][index]
      wifi_rcv_pkts = int_template % self.stats['wifi_rcv_pkts'][index]
      g3_low = int_template % self.stats['3g_low'][index]
      g3_high = int_template % self.stats['3g_high'][index]
      calling = int_template % self.stats['calling'][index]
      cpu_en = float_template % self.stats['cpu_en'][index]
      display_en = float_template % self.stats['display_en'][index]
      gps_en = float_template % self.stats['gps_en'][index]
      wifi_en = float_template % self.stats['wifi_en'][index]
      g3_en = float_template % self.stats['3g_en'][index]
      total_en = float_template % self.stats['total_en'][index]


      if not self.quiet and not self.verbose:
        line = template.format(time, cpu_en, display_en, gps_en, wifi_en, g3_en, total_en)
        self.print_line(line)
      elif self.quiet:
        line = template.format(time, total_en)
        self.print_line(line)
      elif self.verbose: 
        line = template.format(time, cpu_ticks, disp, gps, wifi_snd_pkts, wifi_rcv_pkts, \
        g3_low, g3_high, calling, cpu_en, display_en, gps_en, wifi_en, g3_en, total_en)
        self.print_line(line)





  def print_results (self):
    """
      print_results

      print out a nicely formatted list with power and
      usage results found by parsing the AppScope log
      files

    """
    # check if the input arguments for app specification
    # are the expected ones
    self.check_app_input()
 
    # make a sorted lists with all the usage (raw) and power log files
    raw_files = glob.glob('%s/[0-9]*/raw/[0-9]*' % self.sourcedir)
    power_files = glob.glob('%s/[0-9]*/power/[0-9]*.log' % self.sourcedir)
    #raw_files.sort()
    raw_files = sorted(raw_files, key=lambda x: int(x.rsplit('/', 1)[1]))
    power_files = sorted(power_files, key=lambda x: int(x.rsplit('/', 1)[1].split('.log')[0]))

    # iterate the two files  simultaneously
    for raw_fn, power_fn in zip(raw_files, power_files):
      with open(raw_fn) as raw_f, open(power_fn) as power_f:
        raw_lines = raw_f.readlines()[1:]
        lines_size = len(raw_lines)
        #power_lines = power_f.readlines()[0:lines_size]
        power_lines = power_f.readlines()[0:-1]

        for r_line, p_line in zip(raw_lines, power_lines):
          second = int(raw_fn.rsplit('/',1)[1])
          # extract information from the usage log
          r_line = r_line.strip()
          raw_values = r_line.split(" ", 11)
          # remove the last element from the list
          del raw_values[-1]
          ##raw_values = [int(value) for value in raw_values]
          PID, TGID, UID, CPU_TICKS_REST = r_line.split(" ", 3)
          
          # get CPU ticks per different frequencies
          cpu_ticks_freq = CPU_TICKS_REST.split(" ", 12)
          REST = cpu_ticks_freq.pop()
          disp, gps, wifi_snd_pkts, wifi_rcv_pkts, g3_low,\
          g3_high, calling = REST.split()
          # extract information from the power log
          p_line = p_line.strip()
          values = p_line.split()
          # transform all values to floating points
          values = [float(value.strip()) for value in values]
          CPU_en, DISP_en, GPS_en, WIFI_en, G3_en = values
          # if we want the results at process level
          if self.pid:
            # if the pid read from the file is different from the one provided
            # in the console skip this entry
            if str(PID) != self.pid: continue
          # if we want the results at application level
          elif self.uid:
            # if the uid read from the file is different from the one provided
            # in the console skip this entry
            if str(UID) != self.uid: continue
          # compute the total energy
          total_en = float(CPU_en) + float(DISP_en) + float(GPS_en) + float(WIFI_en) + float(G3_en)
          self.stats['time'].append(int(second))
          self.stats['pid'].append(int(PID))
          self.stats['tgid'].append(int(TGID))
          self.stats['uid'].append(int(UID))
					# tranform the cpu ticks to a list of integers
          cpu_ticks_freq = map(int, cpu_ticks_freq)
          self.stats['cpu_ticks'].append(cpu_ticks_freq)
          self.stats['disp'].append(int(disp))
          self.stats['gps'].append(int(gps))
          self.stats['wifi_snd_pkts'].append(int(wifi_snd_pkts))
          self.stats['wifi_rcv_pkts'].append(int(wifi_rcv_pkts))
          self.stats['3g_low'].append(int(g3_low))
          self.stats['3g_high'].append(int(g3_high))
          self.stats['calling'].append(int(calling))
          self.stats['cpu_en'].append(CPU_en)
          self.stats['display_en'].append(DISP_en)
          self.stats['gps_en'].append(GPS_en)
          self.stats['wifi_en'].append(WIFI_en)
          self.stats['3g_en'].append(G3_en)
          self.stats['total_en'].append(total_en)
    # combine samples with the same timestamp
    self.stats = _combine_duplicate_time_samples (self.stats, key='time')
    # print the statistics formatted
    self.print_stats()


class MyParser(OptionParser):
  def format_description(self, formatter):
    return self.description

def _build_parser():
    """Return a parser for the command-line interface."""
    #print "\n~ AppScope Analyzer ~\n"
    description="""%s is a command-line tool that parses the Appscope logs
and produces per process (PID) or per application (UID) power consumption
information

Author: %s (http://www.thanasispetsas.com)
""" % (_bold("appscope-analyzer"), _bold("Thanasis Petsas"))

    usage = "Usage: %prog [-f FILENAME] [-t DIR] [-u UID] [-p PID] [options]"
    parser = MyParser(usage=usage, description=description)

    actions = OptionGroup(parser, "Actions")
    actions.add_option("-l", "--list",
                       action="store_true", dest='list', default=False,
                       help="list all the package names, UIDs and PIDs of the monitored apps")
    actions.add_option("-a", "--app", dest="app", default="",
                       help="select this app package name to show the results", metavar="APP")
    actions.add_option("-u", "--uid", dest="uid", default="",
                       help="select this app UID to show the results", metavar="UID")
    actions.add_option("-p", "--pid", dest="pid", default="",
                       help="select this process PID to show the results", metavar="PID")
    parser.add_option_group(actions)

    config = OptionGroup(parser, "Configuration Options")
    config.add_option("-s", "--source-dir", dest="sourcedir", default="./",
                      help="the directory containing the packages.xml file", metavar="DIR")
    # TODO: add option for storing the output to a file
    # config.add_option("-f", "--filename", dest="filename", default="appscope.dat",
    #                  help="the filename to store the results", metavar="FILENAME")
    parser.add_option_group(config)

    output = OptionGroup(parser, "Output Options")
    output.add_option("-g", "--grep", dest="grep", default='',
                      help="print only tasks that contain WORD", metavar="WORD")
    # TODO: add option for choosing the statistics output for showing either usage or power results etc.
    # output.add_option("-m", "--mode", dest="mode", default="power",
    #                   help="determine mode: 'power' for power statistics output, 'usage' for usage statistics output, 'all' for both. By default 'power' mode is used", metavar="MODE")
    # TODO: add option to selecte the level of the output: per-process or per-app output
    # output.add_option("-L", "--level", dest="level", default="per-app",
    #                   help="determine level: 'per-proc' for per process output, 'per-app' for per application output. By defailr 'per-app' mode is used", metavar="LEVEL")
    # TODO: add option to produce power statistics only for a specific component (e.g. CPU)
    # output.add_option("-c", "--component", dest="component", default='all',
    #                  help="print power results only for a specific component", metavar="COMP")
    output.add_option("-v", "--verbose",
                      action="store_true", dest="verbose", default=False,
                      help="print more detailed output to the screen")
    output.add_option("-q", "--quiet",
                      action="store_true", dest="quiet", default=False,
                      help="print a laconic output to the screen")
    parser.add_option_group(output)

    return parser

def main():
  """Run the command-line interface."""
  parser = _build_parser()
  (options, args) = parser.parse_args()

  p = LogStats(sourcedir=options.sourcedir, verbose=options.verbose,
                   quiet=options.quiet, pid=options.pid, uid=options.uid,
                   app=options.app, grep=options.grep)
  if options.list:
    # list all the monitored apps
    p.print_apps_list()
  elif options.pid or options.uid or options.app:
    # show results for the selected UID
    p.print_results()
  else:
    parser.print_help()


if __name__ == '__main__':
    main()
