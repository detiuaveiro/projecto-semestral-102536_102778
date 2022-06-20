#!/bin/bash

function main()
{
    num_nodes=$1
    dir="/home/pedro/Documents/UNI/CD/Projeto/projecto-semestral-102536_102778"
    daemon=""
    client=""

    for ((i=0; i<num_nodes; i++)); do
    {
        sleep 0.2

        daemon="python3 daemon.py --folder ../nodes/node$i"
        konsole --new-tab --noclose --workdir $dir -e "$daemon" &

        echo "Deamon $i started"

        sleep 0.2
    
        client="python3 client.py --host localhost --port $((5000+i))"
        konsole --new-tab --noclose --workdir $dir -e "$client" &

        echo "Client $i started"
    }
    done
}

main $@