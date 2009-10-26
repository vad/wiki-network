from celery.task import Task
from celery.registry import tasks


class AnalyseTask(Task):
    def run(self, lang, date):
        from subprocess import *
        import os
        
        logger = self.get_logger()
        logger.info("Running: %s-%s" % (lang, date))
        
        p = Popen("/sra0/sra/setti/Source/wiki-network/analysis.py --as-table --group --reciprocity --density $HHOME/datasets/wikipedia/%swiki-%s_rich.pickle" % (lang, date),
            shell=True, stderr=PIPE)
                
        #sts = os.waitpid(p.pid, 0)
        
        #return p.stderr.readlines()
        return []
        
        
tasks.register(AnalyseTask)
