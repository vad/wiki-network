## Source code here: http://code.google.com/p/django-geo
from django.db import models
import cPickle as pickle


class DictionaryField(models.Field):
        # Django seems to do some funky stuff prohibiting this class from inheriting from
        # PickledObjectField which I can't be bothered to explore. This is quicker, but not DRY :-(
        __metaclass__ = models.SubfieldBase
        
        def to_python(self, value):
                if isinstance(value, dict):
                        return value
                else:
                        if not value:
                                return value
                        return pickle.loads(str(value))
        
        def get_db_prep_save(self, value):
                if value is not None and not isinstance(value, basestring):
                        if isinstance(value, dict):
                                value = pickle.dumps(value)
                        else:
                                raise TypeError('This field can only store dictionaries. Use PickledObjectField to store a wide(r) range of data types.')
                return value
        
        def get_internal_type(self): 
                return 'TextField'
        
        def get_db_prep_lookup(self, lookup_type, value):
                if lookup_type == 'exact':
                        value = self.get_db_prep_save(value)
                        return super(DictionaryField, self).get_db_prep_lookup(lookup_type, value)
                elif lookup_type == 'in':
                        value = [self.get_db_prep_save(v) for v in value]
                        return super(DictionaryField, self).get_db_prep_lookup(lookup_type, value)
                else:
                        raise TypeError('Lookup type %s is not supported.' % lookup_type)
