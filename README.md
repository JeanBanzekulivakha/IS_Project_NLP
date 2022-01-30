## Intelligent systems NLP Project
**Topic:** Finding Maximal/Closed Frequent Itemsets by examining tweets from Twitter.

### How To Run a Project
#### Before running check if you have installed the following modules:
* pandas - `pip3 install pandas`
* mlxtend - `pip3 install mlxtend`
* psutil - `pip3 install psutil`

#### To run the project, run the script *run.py* with the following arguments:
* *-db* [--data_base] - input data file.
* *-minsup* [--minimal_support] - the minimum support (eg. 0.05 - 5%). The value is responsible for assuming that a given word/expression (item) is frequent. For example, if the number is 5 , then it means that the number occurs in 5 percent of transactions.
* *-num_tran* [--number_transaction] - the number of transactions that will be taken into account.
* *-a* [--algorithm] - selection of the algorithm to run, on which the input data will be processed, which will be specified with the --db tag. User selectable value modes are: CHARM, DCI, Apriory.

*For Example:* 
```
python3 run.py -db tweets_121000.txt -minsup 0.02 -num_tran 10000 -a CHARM
```
