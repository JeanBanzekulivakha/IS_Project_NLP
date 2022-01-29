import utils
import argparse
import json
import pandas as pd
from mlxtend.frequent_patterns import apriori
from mlxtend.preprocessing import TransactionEncoder

from charm import Charm
from dci import DCI


def preprocess(file_name, num_of_trans):
    tweets = []
    with open(file_name, 'r') as file:
        for line in file:
            tweets.append(line.strip())
    tweets = tweets[:num_of_trans]

    tweets_splited = [tweet.split() for tweet in tweets]
    tweets_splited_flat = [word for tweet in tweets_splited for word in tweet]
    tweets_splited_unique = sorted(list(set(tweets_splited_flat)))
    word2id = {}
    id2word = {}
    for i, word in enumerate(tweets_splited_unique):
        word2id[word] = i
        id2word[i] = word

    tids = []
    for tweet in tweets_splited:
        tids.append([word2id[word] for word in tweet])

    return tids, word2id, id2word


@utils.profile
def run_apriori(dataset, support=0.1):
    te = TransactionEncoder()
    oht_ary = te.fit(dataset).transform(dataset, sparse=True)
    sparse_df = pd.DataFrame.sparse.from_spmatrix(oht_ary, columns=te.columns_)
    frequent_itemsets = apriori(sparse_df, min_support=support, use_colnames=True)
    return frequent_itemsets


if __name__ == '__main__':

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "-db",
        "--data_base",
        default=None,
        type=str,
        required=True,
        help="Path to the dataset file in .txt format."
    )

    parser.add_argument(
        "-minsup",
        "--minimal_support",
        default=None,
        type=float,
        required=True,
        help="Minimal support."
    )

    parser.add_argument(
        "-num_tran",
        "--number_transaction",
        default=100000,
        type=int,
        required=True,
        help="Number of transaction."
    )

    parser.add_argument(
        "-a",
        "--algorithm",
        default='CHARM',
        type=str,
        required=False,
        help="Algorithm name: CHARM or apriori."
    )

    args = parser.parse_args()

    db_list, word2id, id2word = preprocess(args.data_base, args.number_transaction)

    itemSetResultLen = -1
    if args.algorithm == 'CHARM':
        charm = Charm(db_list, word2id, id2word)
        charm.runAlgoritm(minsup=args.minimal_support)
        charm.printFrequentClosedItemsets()

        itemSetResultLen = len(charm.getItemSetDict())
    elif args.algorithm == 'apriori':
        apriori_result = run_apriori(db_list, args.minimal_support)
        apriori_result['itemsets'] = apriori_result['itemsets'].apply(
            lambda x: ", ".join([id2word[i] for i in list(x)]))

        apriori_result.to_csv('output_apriori.csv', index=False)

        itemSetResultLen = len(apriori_result)
    elif args.algorithm == 'DCI':
        dci = DCI(db_list, word2id, id2word, args.minimal_support, args.number_transaction)
        dci.run_algorithm()
        dci.printFrequentClosedItemsets()
        print("DCI algorithm")
        itemSetResultLen = len(dci.getItemSetDict())
    else:
        raise ValueError('No such algorithm.')

    return_data = {}
    return_data['data'] = []
    return_data['data'].append({
        'minsup': args.minimal_support,
        'num_of_trans': args.number_transaction,
        'executing_time': utils.total_time,
        'memory_usage': utils.mem_usage,
        'algorithm_name': args.algorithm,
        'num_of_transaction': itemSetResultLen
    })

    print(f'Statistics:\n {return_data}')

    with open('return_data.txt', 'a') as outfile:
        json.dump(return_data, outfile)
        outfile.write('\n')
