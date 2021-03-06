"""
Converts data to the OpenNMT data format.
"""
import argparse
import json
import gzip
import os

import numpy as np
np.random.seed(42)
import random
random.seed(42)

from sklearn.utils import resample

from utils import doc2sentences

parser = argparse.ArgumentParser()
parser.add_argument('in_dir')
parser.add_argument('out_dir')
parser.add_argument('--single_tokens', help="Split data into single tokens instead of sentences", action="store_true")
parser.add_argument('--tesseract', help="Use tesseract output as the input", action="store_true")
parser.add_argument('--max_size', help='Maximum number of examples per data split', default=None, type=int)
args = parser.parse_args()

for filename in ['train.json.gz', 'devel.json.gz', 'test.json.gz']:
    data = json.load(gzip.open(os.path.join(args.in_dir, filename), 'rt'))
    gold_sentences = []
    ocr_sentences = []
    for document in data:
        if args.tesseract:
            gold, ocr = doc2sentences(document, args.single_tokens, 2)
        else:
            gold, ocr = doc2sentences(document, args.single_tokens)
        gold_sentences += gold
        ocr_sentences += ocr
    
    # import pdb; pdb.set_trace()
    gold_max_len = max([len(s) for s in gold_sentences])
    ocr_max_len = max([len(s) for s in ocr_sentences])
    
    print('Maximum sentence lengths for %s set in characters: %s / %s (gold/ocr)' % (filename.split('.')[0], gold_max_len, ocr_max_len))
    
    if args.max_size:
        print('Limiting number of examples to %s' % args.max_size)
        gold_sentences, ocr_sentences = resample(gold_sentences, ocr_sentences, replace=False, n_samples=min(args.max_size, len(gold_sentences)))

    # OpenNMT assumes tokens separated with whitespace as the input,
    # but we are using it as a character level model.
    # Thus we want to replace the original whitespaces with an underscore
    # and separate individual characters with whitespace
    # OpenNMT will exclude examples with an empty input so we add <BEG> token for each sentence.
    open_nmt_input = ['<BEG> ' + ' '.join(sentence.replace(' ', '_')) + '\n' for sentence in ocr_sentences]
    open_nmt_output = ['<BEG> ' + ' '.join(sentence.replace(' ', '_')) + '\n' for sentence in gold_sentences]
    
    if not os.path.exists(args.out_dir):
        os.makedirs(args.out_dir)
    
    split = filename.split('.')[0]
    
    oinput_file = open(os.path.join(args.out_dir, 'open_nmt_%s_input.txt' % split), 'wt')
    oinput_file.writelines(open_nmt_input)
    
    ooutput_file = open(os.path.join(args.out_dir, 'open_nmt_%s_output.txt' % split), 'wt')
    ooutput_file.writelines(open_nmt_output)

