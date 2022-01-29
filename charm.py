import math
import utils
import pandas as pd
from mlxtend.frequent_patterns import apriori
from mlxtend.preprocessing import TransactionEncoder


class Charm:
    def __init__(self, database, word2id, id2word):
        self.database = database
        self.itemSetsDict = dict()
        self.word2id = word2id
        self.id2word = id2word

    def getItemSetDict(self):
        return self.itemSetsDict

    @utils.profile
    def runAlgoritm(self, minsup):
        closedItemsets = None

        hash = {}
        itemsetCount = 0
        minsupRelative = int(math.ceil(minsup * len(self.database)))

        # (1) First database pass : calculate tidsets of each item
        mapItemTIDS = {}
        maxItemId = 0
        maxItemId = self.calculateSupportSingleItems(self.database, mapItemTIDS)

        # (2) create the list of single items
        frequentItems = []

        for entry in mapItemTIDS:
            tidset = mapItemTIDS[entry]
            support = len(tidset)
            item = entry
            if support >= minsupRelative:
                frequentItems.append(item)

        # Sort the list of items by the total order of increasing support
        frequentItemsSorted = {}
        for k in mapItemTIDS:
            if k in frequentItems:
                frequentItemsSorted[k] = len(mapItemTIDS[k])

        frequentItemsSorted = list(dict(sorted(frequentItemsSorted.items(), key=lambda item: item[1])).keys())
        # Combine each pairs of single items to generate equivalence classes
        # of 2-itemsets

        for i in range(len(frequentItemsSorted)):

            itemX = frequentItemsSorted[i]

            if itemX is None:
                continue

            # Obtain the tidset and support of that item X
            tidsetX = mapItemTIDS[itemX]

            # Create an itemset with the item X
            itemsetX = [itemX]

            # Create an empty equivalence class for storing all itemsets obtained by
            # joining X with other itemsets. Equivalence class is represented by
            # 1. structure which stores suffix of all itemsets starting with the prefix "X"
            # 2. structure which stores the tidset of each itemset in the equivalence class of the prefix "i"

            equivalenceClassIitemsets = []
            equivalenceClassItidsets = []

            # For each item itemJ that is larger than i according to the total order of increasing support.
            for j in range(i + 1, len(frequentItemsSorted)):

                itemJ = frequentItemsSorted[j]

                if itemJ is None:
                    continue

                # Obtain the tidset of J
                tidsetJ = mapItemTIDS[itemJ]

                # Calculate the tidset of itemset "X" + "J" by performing the intersection of the tidsets of X and the tidset of J
                bitsetSupportUnion = self.performAND(tidsetX, tidsetJ)

                # If the union is infrequent, no need to consider it further
                if len(bitsetSupportUnion) < minsupRelative:
                    continue

                # Check which of the four Charm properties hold
                if (len(tidsetX) == len(tidsetJ)) and (len(bitsetSupportUnion) == len(tidsetX)):
                    # Remove Xj
                    frequentItemsSorted[j] = None
                    # Calculate the union of X and Xj
                    itemsetX = itemsetX + [itemJ]
                elif (len(tidsetX) < len(tidsetJ)) and (len(bitsetSupportUnion) == len(tidsetX)):
                    # Calculate the union of X and Xj
                    itemsetX = itemsetX + [itemJ]
                elif (len(tidsetX) > len(tidsetJ)) and (len(bitsetSupportUnion) == len(tidsetX)):
                    # Remove Xj
                    frequentItemsSorted[j] = None
                    equivalenceClassIitemsets.append([itemJ])
                    equivalenceClassItidsets.append(bitsetSupportUnion)
                else:
                    equivalenceClassIitemsets.append([itemJ])
                    equivalenceClassItidsets.append(bitsetSupportUnion)

            # Process all itemsets from the equivalence class that we are building,
            # which has X as prefix, to find larger itemsets.
            if len(equivalenceClassIitemsets) > 0:
                self.processEquivalenceClass(itemsetX, equivalenceClassIitemsets, equivalenceClassItidsets,
                                             minsupRelative)

            self.save(None, itemsetX, tidsetX)

        return closedItemsets

    def calculateSupportSingleItems(self, database, mapItemTIDS):
        maxItemId = 0
        for i, transaction in enumerate(database):
            for item in transaction:
                if mapItemTIDS.get(item) is None:
                    mapItemTIDS[item] = []
                    if item > maxItemId:
                        maxItemId = item

                # Append transaction or id
                mapItemTIDS[item].append(i)
        return maxItemId

    def performAND(self, tidsetX, tidsetJ):
        return set(tidsetX) & set(tidsetJ)

    def processEquivalenceClass(self, prefix, equivalenceClassItemsets, equivalenceClassTidsets, minsupRelative):
        if len(equivalenceClassItemsets) == 1:
            itemsetI = equivalenceClassItemsets[0]
            tidsetI = equivalenceClassTidsets[0]
            self.save(prefix, itemsetI, tidsetI)
            return

        if len(equivalenceClassItemsets) == 2:
            itemsetI = equivalenceClassItemsets[0]
            tidsetI = equivalenceClassTidsets[0]

            itemsetJ = equivalenceClassItemsets[1]
            tidsetJ = equivalenceClassTidsets[1]

            bitsetSupportIJ = self.performAND(tidsetI, tidsetJ)

            if len(bitsetSupportIJ) >= minsupRelative:
                suffixIJ = itemsetI + itemsetJ
                self.save(prefix, suffixIJ, bitsetSupportIJ)

            if len(bitsetSupportIJ) != len(tidsetI):
                self.save(prefix, itemsetI, tidsetI)

            if len(bitsetSupportIJ) != len(tidsetJ):
                self.save(prefix, itemsetJ, tidsetJ)
            return

        for i in range(len(equivalenceClassItemsets)):
            itemsetX = equivalenceClassItemsets[i]

            if itemsetX is None:
                continue

            tidsetX = equivalenceClassTidsets[i]

            equivalenceClassIitemsets = []
            equivalenceClassItidsets = []

            for j in range(i + 1, len(equivalenceClassItemsets)):
                itemsetJ = equivalenceClassItemsets[j]

                if itemsetJ is None:
                    continue

                tidsetJ = equivalenceClassTidsets[j]

                bitsetSupportUnion = self.performAND(tidsetX, tidsetJ)

                if len(bitsetSupportUnion) < minsupRelative:
                    continue

                # Check which of the four Charm properties hold
                if (len(tidsetX) == len(tidsetJ)) and (len(bitsetSupportUnion) == len(tidsetX)):
                    # Remove prefix + j
                    equivalenceClassItemsets[j] = None
                    equivalenceClassTidsets[j] = None
                    # Replace X by X + J
                    itemsetX = itemsetX + itemsetJ
                elif (len(tidsetX) < len(tidsetJ)) and (len(bitsetSupportUnion) == len(tidsetX)):
                    # Replace X by X + J
                    itemsetX = itemsetX + itemsetJ
                elif (len(tidsetX) > len(tidsetJ)) and (len(bitsetSupportUnion) == len(tidsetX)):
                    # Remove prefix + j
                    equivalenceClassItemsets[j] = None
                    equivalenceClassTidsets[j] = None

                    equivalenceClassIitemsets.append(itemsetJ)
                    equivalenceClassItidsets.append(bitsetSupportUnion)
                else:
                    equivalenceClassIitemsets.append(itemsetJ)
                    equivalenceClassItidsets.append(bitsetSupportUnion)

            if len(equivalenceClassIitemsets) > 0:
                newPrefix = prefix + itemsetX
                self.processEquivalenceClass(newPrefix, equivalenceClassIitemsets, equivalenceClassItidsets,
                                             minsupRelative)

            self.save(prefix, itemsetX, tidsetX)

    def save(self, prefix, suffix, tidset):
        self.saveToItemSetsList(prefix, suffix, tidset)
        with open('output.txt', 'a') as f:
            f.write("{} {} {} \n".format(prefix, suffix, tidset))

    def saveToItemSetsList(self, prefix, suffix, tidset):
        itemSet = frozenset()
        if prefix is not None:
            itemSet |= frozenset(prefix)
        if suffix is not None:
            itemSet |= frozenset(suffix)

        support = len(tidset)
        self.itemSetsDict[itemSet] = support

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
                round(self.itemSetsDict[key] / len(self.database), 32)))
        print("Total number of frequent closed itemsets is {}".format(len(self.itemSetsDict)))
