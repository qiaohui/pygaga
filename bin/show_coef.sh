#!/bin/sh

USAGE="Usage: basename $0 [-h] [-i clientid] [-m model] [-p prefix] [-r inputpath]";

INPUTPATH="r"
ID="0"
MODEL="pca"
PREFIX=""
while getopts :hi:m:p:r: OPTION
do
    case ${OPTION} in
        i)ID=${OPTARG}
        ;;
        m)MODEL=${OPTARG}
        ;;
        p)PREFIX=${OPTARG}
        ;;
        r)INPUTPATH=${OPTARG}
        ;;
        h)echo ${USAGE}
        exit 0
        ;;
        ?)echo "WRONG USE WAY " ${USAGE}
        exit 0
        ;;
    esac
done

pname_coef.sh ${INPUTPATH}/${PREFIX}${ID}.${MODEL}.pname.txt ${INPUTPATH}/${PREFIX}${ID}.${MODEL}.coef.txt | sort -k 2,2 -n
