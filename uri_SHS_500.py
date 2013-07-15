#!/usr/bin/env python
"""
Binary task of cover song identification using the Millions Song Dataset 
and the Second Hand Song dataset.

References:
Bertin-Mahieux, T., & Ellis, D. P. W. (2012). Large-Scale Cover Song 
Recognition Using The 2D Fourier Transform Magnitude. In Proc. of the 13th 
International Society for Music Information Retrieval Conference (pp. 241-246).
Porto, Portugal.

Humphrey, E. J., Nieto, O., & Bello, J. P. (2013). Data Driven and 
Discriminative Projections for Large-Scale Cover Song Identification. 
In Proc. of the 14th International Society for Music Information Retrieval 
Conference. Curitiba, Brazil.

Author: Thierry Bertin-Mahieux (tb2332@columbia.edu)
Modified by: Oriol Nieto (oriol@nyu.edu)
"""

import argparse
import cPickle
import numpy as np
import os
import sys
import time

# local stuff
import pca
import hdf5_getters as GETTERS
import dan_tools
import utils

# Params, for Thierry's ISMIR paper
WIN = 75
PWR = 1.96

logger = utils.configure_logger()

def extract_feats(filename, feats, track_ids, lda=None):
    """
    Finds the filename inside track_id and returns its correspondent features
    from feats
    """

    try:
        feat = feats[track_ids.index(filename)]
        if lda != None:
            feat = lda[0].transform(feat)
        feat = dan_tools.chromnorm(feat.reshape(feat.shape[0], 1)).squeeze()
        return feat
    except:
        return None


def extract_feats_orig(filename):
    """
    Return a one dimensional vector for the data in the
    given file
    It uses 2D-FFT, etc
    """
    # get btchroma
    feats = dan_tools.msd_beatchroma(filename)
    if feats is None:
        return None
    # apply pwr
    feats = dan_tools.chrompwr(feats, PWR)
    # extract fft
    feats = dan_tools.btchroma_to_fftmat(feats, WIN)
    if feats is None:
        return None
    # take median
    feats = np.median(feats, axis=1)
    # normalize
    feats = dan_tools.chromnorm(feats.reshape(feats.shape[0], 1))
    # done
    return feats.flatten()


def read_query_file(queriesf):
    """
    Read queries, return triplets (query/good/bad)
    """
    queries = []
    triplet = []
    f = open(queriesf, 'r')
    for line in f.xreadlines():
        if line == '' or line.strip() == '':
            continue
        if line[0] == '#':
            continue
        if line[0] == '%':
            assert len(triplet) == 0 or len(triplet) == 3
            if len(triplet) > 0:
                queries.append(triplet)
                triplet = []
            continue
        tid = line.strip()
        assert len(tid) == 18 and tid[:2] == 'TR'
        triplet.append(tid)
    assert len(triplet) == 3
    queries.append(triplet)
    f.close()
    logger.info('Found %d queries from file %s' % (len(queries), queriesf))
    return queries


def main():
    # Args parser
    parser = argparse.ArgumentParser(description=
                "Evaluates the 500 binary queries from the SHS data set")
    parser.add_argument("list500queries", action="store",
                        help="usual queries from our cover papers")
    parser.add_argument("-f", action="store", dest="features",
                        help="cPickle file containing the features.")
    parser.add_argument("-lda", action="store", dest="lda", default=None,
                        help="cPickle file containing the LDA transform.")
    # Parse
    args = parser.parse_args()

    # Track time
    start_time = time.time()

    maindir = "MSD"
    queriesf = args.list500queries
    shsf = "SHS/shs_dataset_train.txt"
    lda = args.lda

    # sanity cheks
    assert os.path.isdir(maindir)
    assert os.path.isfile(queriesf)
    assert os.path.isfile(shsf)

    # read queries
    queries = read_query_file(queriesf)

    # read clique ids and track ids
    cliques, all_tracks = utils.read_shs_file(shsf)
    track_ids = all_tracks.keys()
    clique_ids = np.asarray(utils.compute_clique_idxs(track_ids, cliques))
    logger.info("Track ids and clique ids read")

    # read track ids
    #feats = utils.load_pickle(args.features)

    if lda != None:
        lda = utils.load_pickle(args.lda)

    # to keep stats
    cnt = 0
    cnt_good = 0

    # iterate over queries!
    for triplet in queries:
        # get features
        #triplet_feats = map(lambda f: extract_feats(f, feats, track_ids, lda), 
        #                    triplet)
        filenames = map(lambda tid: utils.path_from_tid(maindir, tid), triplet)
        triplet_feats = map(lambda f: extract_feats_orig(f), filenames)
        if None in triplet_feats:
            continue
        # did we get it right?
        res1 = triplet_feats[0] - triplet_feats[1]
        res1 = np.sum(res1 * res1)
        res2 = triplet_feats[0] - triplet_feats[2]
        res2 = np.sum(res2 * res2)
        if res1 < res2:
            cnt_good += 1
        else:
            pass
        # cnt
        cnt += 1
        if cnt >= 500:
            break
        # verbose
        if cnt % 50 == 0:
            logger.info(' --- after %d queries, accuracy: %.3f' % \
                            (cnt, 100. * cnt_good / cnt))
    # done
    logger.info('After %d queries, accuracy: %.4f' % (cnt,
                                                100. * cnt_good / cnt))
    logger.info('Done! Took %.2f seconds' % (time.time() - start_time))

if __name__ == '__main__':
    main()
