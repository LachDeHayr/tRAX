#!/usr/bin/env python

import pysam
import sys
import argparse
import string
import itertools
from collections import defaultdict
import os.path
import re
import subprocess


def runrscript(*script):
    print >>sys.stderr, "Rscript "+" ".join(script)

    retcode = subprocess.call("Rscript "+" ".join(script), shell=True,  stderr = subprocess.STDOUT)

    if retcode > 0:
        print >>sys.stderr, "R script "+script[0]+" failed"

        
        #sys.exit()
    return retcode
    
    
    
scriptdir = os.path.dirname(os.path.realpath(sys.argv[0]))+"/"


parser = argparse.ArgumentParser(description='Generate fasta file containing mature tRNA sequences.')
parser.add_argument('--runname',required=True,
                   help='run name to be used')
parser.add_argument('--runfile',required=True,
                   help='run file')
parser.add_argument('--firadapter',default ='AGATCGGAAGAGCACACGTC' ,
                   help='subset file')
parser.add_argument('--secadapter',default ='GATCGTCGGACTGTAGAACTC' ,
                   help='subset file')
parser.add_argument('--minlength',default ='15' ,
                   help='minimum length of sequence')
parser.add_argument('--singleend', action="store_true", default=False,

                   help='single-end mode (uses cutadapt)')

args = parser.parse_args()

runname = args.runname
seqprepfile = args.runfile
firadapter = args.firadapter
secadapter =   args.secadapter
minlength = args.minlength
singleendmode = args.singleend

#firadapter = 'AGATCGGAAGAGCACACGTC' 
#secadapter = 'GATCGTCGGACTGTAGAACTC'  



'''
Pairs Processed:	1207400
Pairs Merged:	1171370
Pairs With Adapters:	1190959
Pairs Discarded:	23902
CPU Time Used (Minutes):	2.748833

Total reads processed:                  10,000
Reads with adapters:                     9,926 (99.3%)
Reads that were too short:                  19 (0.2%)
Reads written (passing filters):         9,981 (99.8%)

'''     


rereadtotal = re.compile(r'Pairs Processed:\s+(\d+)')
rereadmerge = re.compile(r'Pairs Merged:\s+(\d+)' )
rereadapter = re.compile(r'Pairs With Adapters:\s+(\d+)')
rereaddiscard = re.compile(r'Pairs Discarded:\s+(\d+)' )     

recutadapttotal = re.compile(r'Total reads processed:\s+([\d\,]+)')
recutadapttrimmed = re.compile(r'Reads with adapters:\s+([\d\,]+)' )
recutadaptshort = re.compile(r'Reads that were too short:\s+([\d\,]+)')
recutadaptwritten = re.compile(r'Reads written (passing filters):\s+([\d\,]+)' )     


samplefiles = dict()
sampleorder = list()
cutadaptorder = list()
for currline in open(seqprepfile):
    
    fields = currline.split()
    if not singleendmode and len(fields) > 2:
        samplefiles[fields[0]] = tuple([fields[1],fields[2]])
        sampleorder.append(fields[0])
    elif singleendmode and len(fields) > 1:
        samplefiles[fields[0]] = tuple([fields[1]])
        cutadaptorder.append(fields[0])



    
totalreads = None
merged = None
discard = None
samplenum = 1
seqprepcounts = defaultdict(lambda: defaultdict(int))
cutadaptcounts = defaultdict(lambda: defaultdict(int))
allsamples = set()

minsize = 15
outputfiles = list()
for currsample in samplefiles.iterkeys():
    if not singleendmode:
        #seqprepcommmand = program+' -x '+bowtiedb+' -k '+str(maxmaps)+' --very-sensitive --ignore-quals --np 5 --reorder -p '+str(numcores)+' -U '+unpaired
        seqprepcommmand = 'SeqPrep -L '+str(minsize)+ ' -A '+firadapter+' -B '+secadapter +' -f '+samplefiles[currsample][0]+'  -r '+samplefiles[currsample][1]+' -1 '+currsample+'_left.fastq.gz     -2 '+currsample+'_right.fastq.gz   -s '+currsample+'_merge.fastq.gz'  
        outputfiles.append(currsample+'_merge.fastq.gz')
        #print >>sys.stderr, bowtiecommand
        #bowtiecommand = bowtiecommand + ' | '+scriptdir+'choosemappings.py '+trnafile+' | samtools sort - '+outfile
        
        seqpreprun = None
        seqpreprun = subprocess.Popen(seqprepcommmand, shell = True, stderr = subprocess.PIPE)
        
        output = seqpreprun.communicate()
        errinfo = output[1]
        
        
        for line in errinfo.split("\n"):
        
            
            totalmatch = rereadtotal.match(line)
            mergematch = rereadmerge.match(line)
            discardmatch = rereaddiscard.match(line)
            if totalmatch:
                totalreads = int(totalmatch.group(1).replace(",",""))
            elif mergematch: 
                merged = int(mergematch.group(1).replace(",",""))
            elif discardmatch:
                discard = int(discardmatch.group(1).replace(",",""))
        
        seqprepcounts[currsample]["merged"] = merged
        seqprepcounts[currsample]["unmerged"] = totalreads - (merged + discard)
        seqprepcounts[currsample]["discarded"] = discard

    else:
        #seqprepcommmand = program+' -x '+bowtiedb+' -k '+str(maxmaps)+' --very-sensitive --ignore-quals --np 5 --reorder -p '+str(numcores)+' -U '+unpaired
        #cutadapt -m 15 --adapter='TGGAATTCTCGGGTGCCAAGG'  Testicular_sperm/Fraction4/Fraction4_S2_L002_R1_001.fastq.gz                           | gzip -c > trimmed/Fraction4_S2_L002_R1_001_TRIM.fastq.gz                      

        cutadaptcommand = 'cutadapt -m '+str(minsize)+ ' --adapter='+firadapter+' '+samplefiles[currsample][0]  +' | gzip -c >'+ currsample+'_trimmed.fastq.gz'
        outputfiles.append(currsample+'_trimmed.fastq.gz')
        #print >>sys.stderr, bowtiecommand
        #bowtiecommand = bowtiecommand + ' | '+scriptdir+'choosemappings.py '+trnafile+' | samtools sort - '+outfile
        
        cutadaptrun = None
        cutadaptrun = subprocess.Popen(cutadaptcommand, shell = True, stderr = subprocess.PIPE)
        
        output = cutadaptrun.communicate()
        errinfo = output[1]
        
        
        for line in errinfo.split("\n"):
            totalmatch = recutadapttotal.match(line)
            trimmatch = recutadapttrimmed.match(line) 
            discardmatch = recutadaptshort.match(line) 
            writtenmatch = recutadaptwritten.match(line) 
            

            if totalmatch:
                totalreads = int(totalmatch.group(1).replace(",",""))
            elif trimmatch: 
                trimmed = int(trimmatch.group(1).replace(",",""))
            elif discardmatch:
                discard = int(discardmatch.group(1).replace(",",""))
            elif writtenmatch:
                written = int(writtenmatch.group(1).replace(",",""))

        cutadaptcounts[currsample]["trimmed"] = trimmed
        cutadaptcounts[currsample]["untrimmed"] = totalreads - (trimmed + discard)
        cutadaptcounts[currsample]["discarded"] = discard
            

#print >>sys.stderr, cutadaptcounts
if not singleendmode:
    samplefile = open(runname+"_sp.txt", "w")
    logplefile = open(runname+"_log.txt", "w")
    print >>samplefile,"\t".join(sampleorder)
    for currtype in ["merged","unmerged","discarded"]:
        print >>samplefile,currtype+"\t"+"\t".join(str(seqprepcounts[currsample][currtype]) for currsample in sampleorder)
        
    samplefile.close()
    print >>logfile ,"samplefile: "+seqprepfile
    print >>logfile ,"first adapter: "+ firadapter
    print >>logfile ,"second adapter: "+ secadapter
    print >>logfile ,"output files: "+ ",".join(outputfiles)
    print >>logfile ," ".join(sys.argv)


    logfile.close()    
    runrscript(scriptdir+"/featuretypesreal.R",runname+"_sp.txt",runname+"_sp.pdf")
else:
    samplefile = open(runname+"_ca.txt", "w")
    logfile = open(runname+"_log.txt", "w")
    print >>samplefile,"\t".join(cutadaptorder)
    for currtype in ["trimmed","untrimmed","discarded"]:
        print >>samplefile,currtype+"\t"+"\t".join(str(cutadaptcounts[currsample][currtype]) for currsample in cutadaptorder)
        
    samplefile.close()
    print >>logfile ,"samplefile: "+seqprepfile
    print >>logfile ,"adapter: "+ firadapter
    print >>logfile ,"output files: "+ ",".join(outputfiles)
    print >>logfile ," ".join(sys.argv)

    logfile.close()
    runrscript(scriptdir+"/featuretypesreal.R",runname+"_ca.txt",runname+"_ca.pdf")




