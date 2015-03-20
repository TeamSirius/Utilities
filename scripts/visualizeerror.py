# Brett Fischler
# March 2015
# Analysis Tool for Errors

import matplotlib.pyplot as plt
import numpy as np
import sys
import math

def showCDF(error_lists):
    """ Displays CDF of Accuracy for Various k-NN Distance Metrics """
    index = 0
    max_bucket = int(max([math.ceil(max(errors) + 2) for errors in error_lists]))
    colors = ['r', 'g', 'b']
    shapes = ['^', 'o', 'd']
    labels = ['Euclidean Distance', 'Jaccard Coefficient', 'Combined']
    for (index, errors) in enumerate(error_lists):
        counts = [0 for i in range(max_bucket)]
        for e in errors:
            for i in range(int(math.ceil(e)), max_bucket):
                counts[i] += 1
        counts = [float(c) / len(errors) for c in counts]
        x = np.array(range(len(counts)))
        y = np.array(counts)
        while len(x) < len(y):
            x.append(1)
        color = colors[index]
        shape = shapes[index]
        label = labels[index]
        x = [e for (i, e) in enumerate(x) if i % 2 == 0]
        y = [e for (i, e) in enumerate(y) if i % 2 == 0]
        plt.plot(x, y, str(color) + str(shape) + '-', label=label)
    plt.grid(b=True, which='major', color='c', linestyle='--')
    plt.ylabel('Cumulative Distribution Function')
    plt.xlabel('Accuracy (m)')
    plt.title('CDF of Localization Accuracy for Various k-NN Distance Metrics')
    plt.legend(loc=4)
    plt.show()

def getErrors(errorfile):
    """ Reads errors from given file and stores them in list """
    f = open(errorfile)
    errors = [[]]
    index = 0
    for line in f.readlines():
        if line != '\n':
            errors[index].append(float(line))
        else:
            index += 1
            errors.append([])
    return errors


def main():
    """ Gets list of errors and displays graph of CDFs """
    if len(sys.argv) != 2:
        sys.stderr.write("Usage: python visualizeerror.py errorfile\n")
        sys.exit(1)
    error_lists = getErrors(sys.argv[1])
    showCDF(error_lists)

if __name__ == '__main__':
    main()
