from celery.task import Task
from celery.registry import tasks
from subprocess import *
from django_wikinetwork import settings

class AnalyseTask(Task):
    def run(self, lang, options):
        import os
        from glob import glob
        
        logger = self.get_logger()
        logger.info("Running: %s" % (lang,))
        
        files = '%s/%swiki-*_rich.pickle' % (settings.DATASET_PATH, lang,)
        
        # find the most recent file
        fn = sorted(glob(files))[-1]
        logger.info("Running: %s, filename: %s" % (lang, fn))
        
        cmd = "/sra0/sra/setti/Source/wiki-network/analysis.py --as-table --group %s %s" % (' '.join(options), fn)
        logger.info(cmd)
        
        p = Popen(cmd, shell=True, stderr=PIPE)
        
        return fn
        
        
tasks.register(AnalyseTask)
