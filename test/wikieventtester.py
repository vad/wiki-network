import unittest

class WikiTester(unittest.TestCase):

    def setUp(self):
        from datetime import date
        
        self.opts = {
            'lang':'en','range_':10,'skip':180,
            'dump_date':date(2010,07,30),'desired':True
        }
        self.pages = {
            '7 July 2005 London bombings': {
                'normal': {
                    'total':1.3517076093469143,'anniversary':2.8476190476190477
                }
                ,'talk': {
                    'total':0.2055122828040743,'anniversary':0.9428571428571428
                }
                ,'anniversary_date': date(2005,7,07)
            }
            ,'2004 Madrid train bombings': {
                'normal': {
                    'total':0.8062267657992565,'anniversary':0.9126984126984127
                }
                ,'talk': {
                    'total':1.1686802973977695,'anniversary':1.1349206349206349
                }
                ,'anniversary_date': date(2004,3,11)
            }           
            ,'Beslan school hostage crisis': {
                'normal': {
                    'total':1.4693980778958018,'anniversary':1.7904761904761906
                }
                ,'talk': {
                    'total':0.2276176024279211,'anniversary':0.8476190476190476
                }
                ,'anniversary_date': date(2004,9,02)
            }
        }
        
    def test_wikievent(self):
        import wikieventanalysis
        
        self.processor = wikieventanalysis.EventsProcessor(**self.opts)       
        self.processor.set_desired(self.pages.keys())
        self.processor.process()
        #processor.print_out()
        
        for key,value in self.pages.iteritems():          
            ## asserting normal and talk values
            self.assertDictContainsSubset(self.processor.counter_desired[key],
                                          self.pages[key])
            ## asserting anniversary date
            self.assertEqual(self.pages[key]['anniversary_date'],
                            self.processor.desired_pages[key])              
            
    def tearDown(self):
        self.processor = None
        

if __name__ == '__main__':
    unittest.main()
