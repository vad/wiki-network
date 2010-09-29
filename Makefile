DATASET=${HHOME}/datasets/wikipedia
SOURCE=~/Source/wiki-network/

graph:
	cd ${DATASET} ; ${SOURCE}/wikixml2graph.py ${LANG}wiki-${DATE}-pages-meta-current.xml.bz2

enrich:
	cd ${DATASET} ; ${SOURCE}/enrich.py ${LANG}wiki-${DATE}.pickle

hist:
	cd ${SOURCE} ; ./analysis.py -cg ${DATASET}/${LANG}wiki-${DATE}_rich.pickle

analysis:
	cd ${SOURCE} ; ./analysis.py --as-table --group -derc --distance --power-law ${DATASET}/${LANG}wiki-${DATE}_rich.pickle

param-analysis:
	cd ${SOURCE} ; ./analysis.py ${PARAMS} ${DATASET}/${LANG}wiki-${DATE}_rich.pickle


centrality:
	cd ${SOURCE} ; ./analysis.py --as-table --group -c ${DATASET}/${LANG}wiki-${DATE}_rich.pickle

all-hist: graph enrich hist

all: graph enrich analysis

test:
	nosetests
