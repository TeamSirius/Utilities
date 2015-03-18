#!/bin/bash

clear
while true; do
    read -p "What k value would you like to use? [1-9] " k
    case $k in
        [1-9] ) break;;
        * ) echo "Don't be an asshole.";;
    esac
done

while true; do
    read -p "Would you like to use the default output files? [y/n] " yn
    case $yn in
        [yY] ) error_output="test_results/error_output";
            guess_output="test_results/guess_output";
            neighbor_output="test_results/neighbor_output";
            break;;
        [nN] ) read -p "Enter error_output file: " error_output;
            read -p "Enter guess_output file: " guess_output;
            read -p "Enter neighbor_output file: " neighbor_output;
            break;;
        * ) echo "You're killing me.";;
    esac
done

clear
echo "Running python kNN.py -k $k $error_output $guess_output $neighbor_output"
echo

python kNN.py -k $k $error_output $guess_output $neighbor_output

echo

echo "To see errors on map, run:"
echo "python scripts/showguesses.py Static_Files/Halligan_1.png $guess_output"
echo
echo "To see neighbors on map, run:"
echo "python scripts/showneighbors.py $k Static_Files/Halligan_1.png $neighbor_output"
echo
