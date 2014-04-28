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

function WriteLog()
{
    fntmp_date=`date`
    fnMSG=$1
    fnLOG=$2
    if [ "$fnLOG" != "" -a ! -f ${fnLOG} ]
    then
        mkdir -p `dirname ${fnLOG}`
        touch ${fnLOG}
    fi

    echo "[$fntmp_date] $fnMSG" >> $fnLOG
}

DATE=`date +%s`
CUR_DIR=`pwd`
PREDICT_LIST="${INPUTPATH}/${PREFIX}${ID}.${MODEL}.validation.txt"
PROG_PATH="`pwd`"
LOG_FILE="${CUR_DIR}/log/train_compare_`date +%Y-%m-%d`.log"

#1 stat data for auc eval
PREDICT_DATA_LIST=""
for PREDICT_DATA in ${PREDICT_LIST}
do
    cat ${PREDICT_DATA} |awk -F"," '{printf "%f\t%f\n",$2,$1}' > "${PREDICT_DATA}.roc"
    PREDICT_DATA_LIST="${PREDICT_DATA_LIST} ${PREDICT_DATA}.roc"
done

ROC_INPUT=`echo ${PREDICT_DATA_LIST} |sed "s/ /,/g"`
ROC_OUTPUT="${INPUTPATH}/${PREFIX}${ID}.${MODEL}.roc"

#2 roc eval
if [ ! -z ${ROC_INPUT} ]
then
    plotroc.py --inputfile=${ROC_INPUT} --outputfile=${ROC_OUTPUT} --type=roc
fi

#3 predict - bayes (sub) eval
ROC_OUTPUT="${INPUTPATH}/${PREFIX}${ID}.${MODEL}.sub"
if [ ! -z ${ROC_INPUT} ]
then
    plotroc.py --inputfile=${ROC_INPUT} --outputfile=${ROC_OUTPUT} --type=sub
fi

for PREDICT_DATA in ${PREDICT_LIST}
do
    rm -f ${PREDICT_DATA}.roc
done

WriteLog "[NOTICE] ====================END=================" "${LOG_FILE}"
