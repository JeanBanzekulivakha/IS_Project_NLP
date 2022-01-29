import math

import numpy
import utils

#import charm


class DCI:
    def __init__(self, db_source, word2id, id2word, minsup, num_of_trans):
        self.db_source = db_source
        self.itemSetsDict = dict()
        self.word2id = word2id
        self.id2word = id2word
        self.minsup_persent = minsup
        self.minsup_relative = int(math.ceil(self.minsup_persent * num_of_trans))
        self.db_algorithm = dict()
    def getItemSetDict(self):
        return self.itemSetsDict
    def prepare_data_for_algorithm(self):
        nTId = 0
        maxItemId = 0
        for transaction in self.db_source:
            nTId += 1
            for value in transaction:
                if value in self.db_algorithm and self.db_algorithm[value] is not None:
                    self.db_algorithm[value].append(nTId)
                else:
                    self.db_algorithm[value] = [nTId]
                if value > maxItemId:
                    maxItemId = value

        return maxItemId

    def get_post_set(self, maxItemId):
        postSet = []
        for i in range(1, maxItemId + 1):
            try:
                tidSet = self.db_algorithm[i]
            except:
                continue
            if tidSet is not None and len(tidSet) >= self.minsup_relative:
                postSet.append(i)
        return numpy.array(postSet)

    def is_duplicate(self, newGenTIds, preset):
        for i in preset:
            if set(newGenTIds).issubset(set(self.db_algorithm[i])):
                return True
        return False

    def intersection(self, tIdSet1, tIdSet2):
        return list(set(tIdSet1) & set(tIdSet2))

    def is_smaller_by_support(self, a, b):
        sizeA = len(self.db_algorithm[a])
        sizeB = len(self.db_algorithm[b])
        if sizeA != sizeB:
            return sizeA < sizeB
        else:
            return a < b

    def get_sorted_post_set(self, postSet):
        for i in range(len(postSet)):
            minimum = i
            for j in range(i + 1, len(postSet)):
                if self.is_smaller_by_support(postSet[minimum], postSet[j]):
                    minimum = j
            postSet[minimum], postSet[i] = postSet[i], postSet[minimum]
        return numpy.flip(postSet)

    def getSupport(self, item):
        return len(self.db_algorithm[item])

    def dci_closed(self, isFirstTime, closedSet, closedSetTIds, postSet, preSet, f_out):
        for i in postSet:

            if isFirstTime:
                newGenTIds = self.db_algorithm[i]
            else:
                newGenTIds = self.intersection(closedSetTIds, self.db_algorithm[i])

            if len(newGenTIds) >= self.minsup_relative:
                closedSetNew = closedSet + [i]

                if not self.is_duplicate(newGenTIds, preSet):

                    if isFirstTime:
                        closedNewTIds = self.db_algorithm[i]
                    else:
                        closedNewTIds = newGenTIds.copy()

                    postSetNew = []

                    for j in postSet:

                        if self.is_smaller_by_support(i, j):

                            if set(newGenTIds).issubset(self.db_algorithm[j]):
                                closedSetNew.append(j)

                                jTIds = self.db_algorithm[j]

                                closedNewTIds = self.intersection(closedNewTIds, jTIds)
                            else:
                                postSetNew.append(j)

                    self.itemSetsDict[frozenset(closedSetNew)] = len(closedNewTIds)

                    # print("[{}], itemsets: {}  support: {}".format(count, closedSetNewWord, len(closedNewTIds)))
                    # closedSetNewWord = self.list2Word(closedSetNew)
                    # f_out.write(' '.join(map(repr, closedSetNewWord)) + " #SUP: " + str(len(closedNewTIds)) + "\n") # TODO implement normal out

                    preSetNew = preSet.copy()
                    self.dci_closed(False, closedSetNew, closedNewTIds, postSetNew, preSetNew, f_out)

                    preSet.append(i)

    def list2Word(self, items):
        if len(items) == 1:
            inverse_encoded = id2word[items[0]]
        else:
            inverse_encoded = [id2word[i] for i in items]
            inverse_encoded = ", ".join(inverse_encoded)
        return inverse_encoded

    def printFrequentClosedItemsets(self):
        self.itemSetsDict = dict(sorted(self.itemSetsDict.items(), key=lambda item: (len(item[0]), item[1])))
        for key in self.itemSetsDict:
            if len(key) == 1:
                inverse_encoded = self.id2word[list(key)[0]]
            else:
                inverse_encoded = [self.id2word[i] for i in list(key)]
                inverse_encoded = ", ".join(inverse_encoded)
            print("Number of itemsets: {}, ItemSet ({}) with frequent: {} support: {}".format(
                len(key), inverse_encoded, self.itemSetsDict[key],
                round(self.itemSetsDict[key] / len(self.db_source), 32)))
        print("Total number of frequent closed itemsets is {}".format(len(self.itemSetsDict)))

    @utils.profile
    def run_algorithm(self):

        maxItemId = self.prepare_data_for_algorithm()
        postSet = self.get_post_set(maxItemId)
        sortedPostSet = self.get_sorted_post_set(postSet)

        closedSet = []
        closedSetTIds = []
        preSet = []

        f_out = open("output_dci.txt", "w")
        self.dci_closed(True, closedSet, closedSetTIds, sortedPostSet, preSet, f_out)
        f_out.close()


# if __name__ == '__main__':
#     file_name = 'tweets_300000_1.txt'
#     tweets = list()
#     num_of_trans = 100000
#     minsup = 0.03
#
#     db_list, word2id, id2word = charm.preprocess('tweets_300000_1.txt', num_of_trans)
#     dci = DCI(db_list, word2id, id2word, minsup)
#     dci.run_algorithm()
#
#     print("finish")
