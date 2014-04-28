#!/usr/bin/env ruby

require 'optparse'

$clientid = "0"
$prefix = ""
$inputpath = "r/"
$modelname = "pca"
OptionParser.new do |o|
  o.on('-r INPUTPATH') { |inputpath| $inputpath = inputpath }
  o.on('-p PREFIX') { |prefix| $prefix = prefix }
  o.on('-i CLIENTID') { |id| $clientid = id }
  o.on('-m MODELNAME') { |modelname| $modelname = modelname }
  o.on('-h') { puts o; exit }
  o.parse!
end

pname_filename = File.join($inputpath, "%s%s.%s.pname.txt" % [$prefix, $clientid, $modelname])
data_filename = File.join($inputpath, "%s%s.%s.data.txt" % [$prefix, $clientid, $modelname])

pname = Hash[*File.open(pname_filename).readlines.map{|x| x.strip.split}.map{|i,j| ["input_%d" % (i.to_i-1), j]}.flatten]

datafile = File.open(data_filename)
header = datafile.readline.split(" ").map{|x| pname[x] or x}

#puts File.open(data_filename).readlines[2..-1].map{|x| x.strip.gsub(/"/,"").split.each_with_index.map{|k,i| "%s:%s"%[header[i],k] if k.to_i>0 or header[i]=='result'}.select{|x| x}.join(" ")}.join("\n")
datafile.each do |x|
    puts x.strip.gsub(/"/,"").split.each_with_index.map{|k,i| "%s:%s"%[header[i],k] if k.to_i>0 or header[i]=='result'}.select{|x| x}.join(" ") 
end
