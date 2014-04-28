from __future__ import with_statement
import collections
import gflags
import itertools
import multiprocessing

FLAGS = gflags.FLAGS

gflags.DEFINE_boolean('parallel', False, "Run in parallel mode", short_name = 'p')
gflags.DEFINE_integer("max_cpu", multiprocessing.cpu_count() / 2 or 1,
                      "Global limitation of CPU to run python in parallel.")

class SimpleMapReduce(object):

    def __init__(self, map_func, reduce_func, num_workers = None):
        """
        map_func

          Function to map inputs to intermediate data. Takes as argument one input value and
          returns a tuple with the key and a value to be reduced.

        reduce_func
          Function to reduce partitioned version of intermediate data to final output. Takes
          as argument a key as produced by map_func and a sequence of the values associated
          with that key.

        num_workers
          The number of workers to create in the pool. Defaults to 1/2 of the number of CPUs
          available on the current host.
        """
        self.map_func = map_func
        self.reduce_func = reduce_func
        self.pool = multiprocessing.Pool(num_workers or FLAGS.max_cpu)

    def partition(self, mapped_values):
        """Organize the mapped values by their key.
        Returns an unsorted sequence of tuples with a key and a sequence of values.
        """
        partitioned_data = collections.defaultdict(list)
        for key, value in mapped_values:
            partitioned_data[key].append(value)
        return partitioned_data.items()

    def __call__(self, inputs, chunksize=1):
        """Process the inputs through the map and reduce functions given.

        inputs
          An iterable containing the input data to be processed.

        chunksize=1
          The portion of the input data to hand to each worker.  This
          can be used to tune performance during the mapping phase.
        """
        map_responses = self.pool.map(self.map_func, inputs, chunksize=chunksize)
        partitioned_data = self.partition(itertools.chain(*map_responses))
        reduced_values = self.pool.map(self.reduce_func, partitioned_data)
        return reduced_values

def identity(x):
    return x

######################### test section #####################################
import string

def file_to_words(filename):
    """Read a file and return a sequence of (word, occurances) values.
    """
    STOP_WORDS = set([
        'a', 'an', 'and', 'are', 'as', 'be', 'for', 'if', 'in',
        'is', 'it', 'of', 'or', 'py', 'rst', 'the', 'to', 'with',
        ])
    TR = string.maketrans(string.punctuation, ' ' * len(string.punctuation))

    print multiprocessing.current_process().name, 'reading', filename
    output = []

    with open(filename, 'rt') as f:
        for line in f:
            if line.lstrip().startswith('..'): # Skip rst comment lines
                continue
            line = line.translate(TR) # Strip punctuation
            for word in line.split():
                word = word.lower()
                if word.isalpha() and word not in STOP_WORDS:
                    output.append( (word, 1) )
    print "m", output
    return output


def count_words(item):
    """Convert the partitioned data for a word to a
    tuple containing the word and the number of occurances.
    """
    print "r", item
    word, occurances = item
    return (word, sum(occurances))

def test():

    import operator
    import glob

    input_files = glob.glob('*.py')

    mapper = SimpleMapReduce(file_to_words, count_words)
    word_counts = mapper(input_files)
    word_counts.sort(key=operator.itemgetter(1))
    word_counts.reverse()

    print '\nTOP 20 WORDS BY FREQUENCY\n'
    top20 = word_counts[:20]
    longest = max(len(word) for word, count in top20)
    for word, count in top20:
        print '%-*s: %5s' % (longest+1, word, count)

if __name__ == "__main__":
    test()
