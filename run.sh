#!/bin/bash

function main()
{
    num_nodes=$1
    dir="/home/pedro/Documents/UNI/CD/Projeto/projecto-semestral-102536_102778"
    daemon=""
    client=""

    for ((i=0; i<num_nodes; i++)); do
    {
        daemon="python3 daemon.py --folder ../node$i"
        gnome-terminal --working-directory=$dir --command="$daemon" 

        echo "Deamon $i started"
    
        client="python3 client.py --host localhost --port $((5000+i))"
        gnome-terminal --working-directory=$dir --command="$client" 

        echo "Client $i started"
    }
    done
}

main $@