#!/bin/sh

USAGE="Usage: basename $0 pname_file model_coef_file";

if [ $# -ne 2 ]
then
    echo $USAGE
    exit 1
fi

awk 'BEGIN{
while (getline<"'"$1"'")
    {
    hash_key["\"input_"$1"\""]=$2
    }
}{
if ($1 in hash_key)
    print hash_key[$1]"\t"$2
}
{
#    for( key in hash_key)
#        print key,hash_key[key]
}' $2
