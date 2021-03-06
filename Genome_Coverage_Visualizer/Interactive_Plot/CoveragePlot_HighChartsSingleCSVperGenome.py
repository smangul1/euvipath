# python CoveragePlot.py Read_FullList.sam GenomeInformation.txt 100000 1 30
import argparse
import sys
import os
import numpy as np
import matplotlib.pyplot as plt
from errno import EEXIST
from os import makedirs,path
import textwrap as tw
import getopt
import tempfile


# handle user arguments
def parseargs():    
	parser = argparse.ArgumentParser(description='Compute abundance estimations for species in a sample.')
	parser.add_argument('bwa', help='Output of BWA after processing, extraction, and sorting. Required.')
	parser.add_argument('IDs', help='Genome List: Name and length extracted from genome database (.fa). Required.')
	parser.add_argument('WS', help='Plot Window Size. Required.')
	parser.add_argument('CAT', help='Read Category Number: Enter one of the following numbers: (1) Unique Reads, (2) MultiMapped reads within genome, (3) MultiMapped reads across genomes. Required.')
	parser.add_argument('CPD', help='Coverage Plot Directory. Required.')
	parser.add_argument('CVGTHR', help='Coverage Threshold %. Required.')
	args = parser.parse_args()
	return args

args = parseargs()
if os.path.getsize(str(args.bwa)) > 0:
	infile = open(args.bwa, 'r')
			
	window_size = int(args.WS)
	LineNo = 1
	previous_genome = ""
	UniqueReads=0
	mypath=""
	Read_CAT = int(args.CAT) #1 or 2 or 3
	if Read_CAT==1:
		rcat='Unique reads #='
		fcat='MiCoP_FinalCSVs'
	elif Read_CAT==2:
		rcat='MultiMapped reads (within-genome) #='
		fcat='MiCoP_FinalCSVs'
	elif Read_CAT==3:
		rcat='MultiMapped reads (across-genome) #='
		fcat='MiCoP_FinalCSVs'

	if(str(args.CPD)[len(args.CPD)-1]=='/'):
		mypath= str(args.CPD)+fcat+'/'
	else:
		mypath= str(args.CPD)+'/'+fcat+'/'	

	try:
		makedirs(mypath)
	except OSError as exc:
		if exc.errno == EEXIST and path.isdir(mypath):
			pass
		else: raise

	if Read_CAT==1:
		CSVGenomeList = mypath+'Mapped_Genome_List.txt'
		GL = open(CSVGenomeList, 'w')

	for line in infile:
		splits = line.strip().split('\t')
		#header = str(splits[2].strip())
		location_start = int(splits[3].strip())	
		current_genome = str(splits[2].strip())
		UniqueReads=UniqueReads+1

		if LineNo ==1:
			previous_genome = current_genome
			LineNo = LineNo + 1	
			# Extract the genome information from the database file
			with open(args.IDs, 'r') as f:
				for line2 in f:
					if current_genome in line2:
						splits2 = line2.strip().split('|')
						header = splits2[0].strip()
						split3 = str(splits2[2]).strip().split('=')
						location_max = int(split3[1])
						location_list = [0] * (location_max+1) # we added 1 as we want our mapping range to start from 1-location_max and not 0-location_max
						break
		if str(current_genome) == str(previous_genome): # clustering the reads based on genomes
			for list_no in range(location_start , location_start+int(len(str(splits[9].strip())))):
				if list_no <= location_max:
					location_list[list_no] = location_list[list_no] + 1	
				#else:
				#	sys.stdout.write(str(list_no) +' max: '+ str(location_max)+' genome: '+ str(current_genome)+'\n')
					#raise Exception("POS is out of range: mapping position is larger than the genome size")	
		else:
			
			# #create the coverage file per genome
			val = 0
			window_start = 1
			window_end = 1
			radii = list()
			left_windows = list()
			right_windows = list()
			coverage=0
			for list_no in range(1 , location_max+1):
				if int(location_list[list_no])>0:
					coverage=coverage+1
				val += int(location_list[list_no])
				window_end += 1
				if list_no % window_size == 0:
					left_windows.append(int(window_start))
					right_windows.append(int(window_end-1))
					radii.append(float(float(val) / float(window_size)))
					#sys.stdout.write("%s\t%d\t%d\t%f\n" % (header, window_start, window_end-1, val / float(window_size)))
					window_start = window_end
					val = 0
			if window_end>window_start: # in case last window is less than window size
				left_windows.append(int(window_start))
				right_windows.append(int(window_end-1))
				radii.append(float(float(val) / float(window_end - window_start)))
			header = header.split('=')[1]
			##################################
			# Write the data
			outputFile = mypath+str(header)+'.csv'
			# Generate coverage file only if unique coverage is more than 30%
			if ((Read_CAT==1) and (float(float(float(coverage)/float(location_max))*100.0)>=float(args.CVGTHR))):
				MappedGenome='<option value="'+str(header)+'">' +'('+ str('%.2f%%' % float(float(float(coverage)/float(location_max))*100.0))+') '+str(header)+'</option>'+'\n'
				GL.write(MappedGenome)
				##
				f = open(outputFile, 'w')
				DataName=str(infile).split('/')
				ChartTitle=str(DataName[len(DataName)-1].split('_')[0])+' mapped to '+header+'\n'
				f.write(ChartTitle)
				ChartSubtitle=rcat+str(' %s' % '{:,d}'.format(int(int(UniqueReads)-1)))+' -- '+'Coverage = '+str('{:,d}'.format(coverage))+'bp out of '+str('{:,d}'.format(location_max))+'bp' +' ('+ str('%.2f%%' % float(float(float(coverage)/float(location_max))*100.0))+')'+' -- '+'Window Size='+ '{:,d}'.format(window_size)+'\n'
				f.write(ChartSubtitle)
				ColumnsTitle='Position bp'+','+'Unique'+','+'MultiMapped Within'+','+'MultiMapped Across'+'\n'
				f.write(ColumnsTitle)
				
				for list_no in range(0 , len(left_windows)):
					if list_no==(len(left_windows)-1):
						if radii[list_no]==0:
							ss=str(left_windows[list_no])+','+'null'+','+'null'+','+'null'
						else:
							ss=str(left_windows[list_no])+','+str(radii[list_no])+','+'null'+','+'null'				
					else:
						if int(radii[list_no])==0:
							ss=str(left_windows[list_no])+','+'null'+','+'null'+','+'null'+'\n'
						else:
							ss=str(left_windows[list_no])+','+str(radii[list_no])+','+'null'+','+'null'+'\n'
					f.write(ss)
				f.close()
			# Ignore MMwithin and MMacross if there is no Unique coverage at all for this genome
			elif os.path.exists(outputFile)==1 and Read_CAT!=1: 
				#Create temporary file read/write
				t = tempfile.NamedTemporaryFile(mode="r+")
				#Open input file read-only
				i = open(outputFile, 'r')
				#Copy input file to temporary file, modifying as we go
				for line in i:
					t.write(line.rstrip()+"\n")
				i.close() #Close input file
				t.seek(0) #Rewind temporary file to beginning
				o = open(outputFile, "w")  #Reopen input file writable
				#Overwriting original file with temporary file contents     
				LineIndex=0
				NewLine=''
				for line in t:
					if LineIndex==0:
						o.write(line)
					elif LineIndex==1:
						ChartSubtitle=line.rstrip()+'<br>'+rcat+str(' %s' % '{:,d}'.format(int(int(UniqueReads)-1)))+' -- '+'Coverage='+str('{:,d}'.format(coverage))+'bp out of '+str('{:,d}'.format(location_max))+'bp' +' ('+ str('%.2f%%' % float(float(float(coverage)/float(location_max))*100.0)+')')+' -- '+'Window Size='+ '{:,d}'.format(window_size)+'\n'
						o.write(ChartSubtitle)
					elif LineIndex==2:
						o.write(line)
					else:
						if Read_CAT==2:
							if radii[LineIndex-3]==0:
								NewLine = line
							else:
								LineTokens=line.rstrip().split(',')
								NewLine = LineTokens[0]+','+LineTokens[1]+','+str(radii[LineIndex-3])+','+'null'+'\n'
						elif Read_CAT==3:
							LineTokens=line.rstrip().split(',')
							NewLine = LineTokens[0]+','+LineTokens[1]+','+LineTokens[2]+','+str(radii[LineIndex-3])+'\n'
							
						o.write(NewLine)
					LineIndex=LineIndex+1
				t.close() #Close temporary file, will cause it to be deleted
				o.close()
			
			#-----------------------------------------------------------------------------
			#-----------------------------------------------------------------------------
			#move to next genome
			UniqueReads=1
			LineNo = 2
			previous_genome = current_genome
			# Extract the genome information from the database file
			with open(args.IDs, 'r') as f:
				for line2 in f:
					if current_genome in line2:
						splits2 = line2.strip().split('|')
						header = splits2[0].strip()
						split3 = str(splits2[2]).strip().split('=')
						location_max = int(split3[1])
						location_list = [0] * (location_max+1) # we added 1 as we want our mapping range to start from 1-location_max and not 0-location_max
						break
			# as we already read one line so we repeat the code below to not lose it
			for list_no in range(location_start , location_start+int(len(str(splits[9].strip())))):
				if list_no <= location_max:
					location_list[list_no] = location_list[list_no] + 1	
				#else:
				#	sys.stdout.write(str(list_no) +' max: '+ str(location_max)+' genome: '+ str(current_genome)+'\n')
					#raise Exception("POS is out of range: mapping position is larger than the genome size")	


	#This is to plot the last genome in the .sam file
	#-----------------------------------------------------------------------------
	#-----------------------------------------------------------------------------
	#-----------------------------------------------------------------------------
	# #create the coverage file per genome
	val = 0
	window_start = 1
	window_end = 1
	radii = list()
	left_windows = list()
	right_windows = list()
	coverage=0
	for list_no in range(window_start , location_max+1):
		if int(location_list[list_no])>0:
			coverage=coverage+1
		val += int(location_list[list_no])
		window_end += 1
		if list_no % window_size == 0:
			left_windows.append(int(window_start))
			right_windows.append(int(window_end-1))
			radii.append(float(float(val) / float(window_size)))
			#sys.stdout.write("%s\t%d\t%d\t%f\n" % (header, window_start, window_end-1, val / float(window_size)))
			window_start = window_end
			val = 0
	if window_end>window_start: # in case last window is less than window size
		left_windows.append(int(window_start))
		right_windows.append(int(window_end-1))
		radii.append(float(float(val) / float(window_end - window_start)))
	header = header.split('=')[1]
	##################################
	# Write the data
	outputFile = mypath+str(header)+'.csv'
	# Generate coverage file only if unique coverage is more than 30%
	if ((Read_CAT==1) and (float(float(float(coverage)/float(location_max))*100.0)>=float(args.CVGTHR))):
		MappedGenome='<option value="'+str(header)+'">' +'('+ str('%.2f%%' % float(float(float(coverage)/float(location_max))*100.0))+') '+str(header)+'</option>'+'\n'
		GL.write(MappedGenome)
		##
		f = open(outputFile, 'w')
		DataName=str(infile).split('/')
		ChartTitle=str(DataName[len(DataName)-1].split('_')[0])+' mapped to '+header+'\n'
		f.write(ChartTitle)
		ChartSubtitle=rcat+str(' %s' % '{:,d}'.format(int(int(UniqueReads)-1)))+' -- '+'Coverage = '+str('{:,d}'.format(coverage))+'bp out of '+str('{:,d}'.format(location_max))+'bp' +' ('+ str('%.2f%%' % float(float(float(coverage)/float(location_max))*100.0))+')'+' -- '+'Window Size='+ '{:,d}'.format(window_size)+'\n'
		f.write(ChartSubtitle)
		ColumnsTitle='Position bp'+','+'Unique'+','+'MultiMapped Within'+','+'MultiMapped Across'+'\n'
		f.write(ColumnsTitle)
		
		for list_no in range(0 , len(left_windows)):
			if list_no==(len(left_windows)-1):
				if radii[list_no]==0:
					ss=str(left_windows[list_no])+','+'null'+','+'null'+','+'null'
				else:
					ss=str(left_windows[list_no])+','+str(radii[list_no])+','+'null'+','+'null'				
			else:
				if int(radii[list_no])==0:
					ss=str(left_windows[list_no])+','+'null'+','+'null'+','+'null'+'\n'
				else:
					ss=str(left_windows[list_no])+','+str(radii[list_no])+','+'null'+','+'null'+'\n'
			f.write(ss)
		f.close()
	# Ignore MMwithin and MMacross if there is no Unique coverage at all for this genome
	elif os.path.exists(outputFile)==1 and Read_CAT!=1: 
		#Create temporary file read/write
		t = tempfile.NamedTemporaryFile(mode="r+")
		#Open input file read-only
		i = open(outputFile, 'r')
		#Copy input file to temporary file, modifying as we go
		for line in i:
			t.write(line.rstrip()+"\n")
		i.close() #Close input file
		t.seek(0) #Rewind temporary file to beginning
		o = open(outputFile, "w")  #Reopen input file writable
		#Overwriting original file with temporary file contents     
		LineIndex=0
		NewLine=''
		for line in t:
			if LineIndex==0:
				o.write(line)
			elif LineIndex==1:
				ChartSubtitle=line.rstrip()+'<br>'+rcat+str(' %s' % '{:,d}'.format(int(int(UniqueReads)-1)))+' -- '+'Coverage='+str('{:,d}'.format(coverage))+'bp out of '+str('{:,d}'.format(location_max))+'bp' +' ('+ str('%.2f%%' % float(float(float(coverage)/float(location_max))*100.0)+')')+' -- '+'Window Size='+ '{:,d}'.format(window_size)+'\n'
				o.write(ChartSubtitle)
			elif LineIndex==2:
				o.write(line)
			else:
				if Read_CAT==2:
					if radii[LineIndex-3]==0:
						NewLine = line
					else:
						LineTokens=line.rstrip().split(',')
						NewLine = LineTokens[0]+','+LineTokens[1]+','+str(radii[LineIndex-3])+','+'null'+'\n'
				elif Read_CAT==3:
					LineTokens=line.rstrip().split(',')
					NewLine = LineTokens[0]+','+LineTokens[1]+','+LineTokens[2]+','+str(radii[LineIndex-3])+'\n'
					
				o.write(NewLine)
			LineIndex=LineIndex+1
		t.close() #Close temporary file, will cause it to be deleted
		o.close()
	

	infile.close()
	if Read_CAT==1:
		GL.close()