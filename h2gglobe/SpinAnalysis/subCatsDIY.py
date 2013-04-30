#!/usr/bin/env python
import sys
import os
import StringIO
import ConfigParser

from optparse import OptionParser

parser = OptionParser()
parser.add_option("-n","--njobs",dest="njobs",type="int",)
parser.add_option("-t","--toysperjob",dest="toyspj",type="int")
parser.add_option("-f","--datfile",dest="datfile",type="string")
parser.add_option("-q","--queue",dest="queue",type="string")
parser.add_option("--minCats",dest="minCats",type="int")
parser.add_option("--maxCats",dest="maxCats",type="int")
parser.add_option("-d","--directory",dest="directory",type="string",default=".")
parser.add_option("--dryRun",dest="dryRun",action="store_true",default=False)
parser.add_option("--clean",dest="clean",action="store_true",default=False)
(options,args) = parser.parse_args()

home='$CMSSW_BASE/src/h2gglobe/SpinAnalysis'
startDir = os.getenv("PWD")
#os.environ['PWD']

ini_str = '[root]\n' + open(options.datfile, 'r').read()
ini_fp = StringIO.StringIO(ini_str)
config = ConfigParser.RawConfigParser()
config.readfp(ini_fp)

for j in range(options.minCats,options.maxCats+1):
  #print j
  dir=startDir+'/%s/%dCategories'%(options.directory,j)
  os.system('mkdir -p %s'%dir)

  datfile='%s/%dCats_%s'%(dir,j,options.datfile)
  f = open('%s'%(datfile),'w')
  f.write("treefile=%s\n"%config.get('root', 'treefile'))
  f.write("wsfile=%s/Workspace.root\n"%(dir))
  f.write("isMassFac=%d\n"%config.getint('root', 'isMassFac'))
  f.write("globePDFs=%d\n"%config.getint('root', 'globePDFs'))
  f.write("fullSMproc=%d\n"%config.getint('root', 'fullSMproc'))
  f.write("useSMpowheg=%d\n"%config.getint('root', 'useSMpowheg'))
  f.write("useSpin2LP=%d\n"%config.getint('root', 'useSpin2LP'))
  f.write("nBDTCats=%d\n"%config.getint('root', 'nBDTCats'))
  f.write("nSpinCats=%d\n"%j)
  if(config.has_option('root', 'correlateCosThetaCategories')):
    f.write("correlateCosThetaCategories=%d\n"%config.getint('root', 'correlateCosThetaCategories'))
  if(config.has_option('root', 'useBackgroundMC')):
    f.write("useBackgroundMC=%d\n"%config.getint('root', 'useBackgroundMC'))
  f.close()

  os.chdir(dir)
  processCommand = "%s/bin/diyBuildWorkspace %s"%(home, datfile)
  #print processCommand
  os.system(processCommand)
  os.chdir(startDir)

  os.system('cp %s/bin/diySeparation %s/'%(os.getcwd(),dir))

  for i in range(1,options.njobs+1):
    jobdir = "%s/job%d"%(dir,i)
    os.system("mkdir -p %s"%jobdir)
    os.system("rm -f %s/*.sh.fail"%jobdir)
    os.system("rm -f %s/*.sh.done"%jobdir)
    os.system("rm -f %s/*.sh.log"%jobdir)
    os.system("rm -f %s/*.sh.run"%jobdir)

  f = open('%s/%d_Cats.sh'%(dir,j),'w')
  f.write('#!/bin/bash\n')
  f.write('cd %s/job$LSB_JOBINDEX\n'%(dir))
  f.write('touch sub$LSB_JOBINDEX.sh.run\n')
  f.write('eval `scramv1 runtime -sh`\n')
  subline = '../diySeparation %s %d'%(datfile,options.toyspj)
  f.write('if ( %s )\n'%subline)
  f.write('\tthen touch sub$LSB_JOBINDEX.sh.done\n')
  f.write('\telse touch sub$LSB_JOBINDEX.sh.fail\n')
  f.write('fi\n')
  f.write('rm -f sub$LSB_JOBINDEX.sh.run\n')
  os.system('chmod +x %s'%f.name)

  os.chdir(dir)
  jobListName = "%dCategories[1-%d]"%(j,options.njobs)
  logFile = "%s/job%%I/sub%%I.sh.log"%(os.getcwd())
  processCommand = 'bsub -J "%s" -q %s -o "%s" %d_Cats.sh'%(jobListName,options.queue,logFile,j)
  if not options.dryRun: os.system(processCommand)
  else: print processCommand
  os.chdir(startDir)
