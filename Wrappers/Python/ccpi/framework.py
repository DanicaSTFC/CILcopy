# -*- coding: utf-8 -*-
#   This work is part of the Core Imaging Library developed by
#   Visual Analytics and Imaging System Group of the Science Technology
#   Facilities Council, STFC

#   Copyright 2018 Edoardo Pasca

#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at

#       http://www.apache.org/licenses/LICENSE-2.0

#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
import abc
import numpy
import sys
from datetime import timedelta, datetime
import warnings

if sys.version_info[0] >= 3 and sys.version_info[1] >= 4:
    ABC = abc.ABC
else:
    ABC = abc.ABCMeta('ABC', (), {})

def find_key(dic, val):
    """return the key of dictionary dic given the value"""
    return [k for k, v in dic.items() if v == val][0]

class CCPiBaseClass(ABC):
    def __init__(self, **kwargs):
        self.acceptedInputKeywords = []
        self.pars = {}
        self.debug = True
        # add keyworded arguments as accepted input keywords and add to the
        # parameters
        for key, value in kwargs.items():
            self.acceptedInputKeywords.append(key)
            #print ("key {0}".format(key))
            #self.setParameter(key.__name__=value)
            self.setParameter(**{key:value})
    
    def setParameter(self, **kwargs):
        '''set named parameter for the reconstructor engine
        
        raises Exception if the named parameter is not recognized
        
        '''
        for key , value in kwargs.items():
            if key in self.acceptedInputKeywords:
                self.pars[key] = value
            else:
                raise KeyError('Wrong parameter "{0}" for {1}'.format(key, 
                               self.__class__.__name__ ))
    # setParameter

    def getParameter(self, key):
        if type(key) is str:
            if key in self.acceptedInputKeywords:
                return self.pars[key]
            else:
                raise KeyError('Unrecongnised parameter: {0} '.format(key) )
        elif type(key) is list:
            outpars = []
            for k in key:
                outpars.append(self.getParameter(k))
            return outpars
        else:
            raise Exception('Unhandled input {0}' .format(str(type(key))))
    #getParameter
    def getParameterMap(self, key):
        if type(key) is str:
            if key in self.acceptedInputKeywords:
                return self.pars[key]
            else:
                raise KeyError('Unrecongnised parameter: {0} '.format(key) )
        elif type(key) is list:
            outpars = {}
            for k in key:
                outpars[k] = self.getParameter(k)
            return outpars
        else:
            raise Exception('Unhandled input {0}' .format(str(type(key))))
    #getParameter
    
    def log(self, msg):
        if self.debug:
            print ("{0}: {1}".format(self.__class__.__name__, msg))
            
class DataSet():
    '''Generic class to hold data'''
    
    def __init__ (self, array, deep_copy=True, dimension_labels=None, 
                  **kwargs):
        '''Holds the data'''
        
        self.shape = numpy.shape(array)
        self.number_of_dimensions = len (self.shape)
        self.dimension_labels = {}
        
        if dimension_labels is not None and \
           len (dimension_labels) == self.number_of_dimensions:
            for i in range(self.number_of_dimensions):
                self.dimension_labels[i] = dimension_labels[i]
        else:
            for i in range(self.number_of_dimensions):
                self.dimension_labels[i] = 'dimension_{0:02}'.format(i)
        
        if type(array) == numpy.ndarray:
            if deep_copy:
                self.array = array[:]
            else:
                self.array = array
        else:
            raise TypeError('Array must be NumpyArray, passed {0}'\
                            .format(type(array)))

    def as_array(self, dimensions=None):
        '''Returns the DataSet as Numpy Array
        
        Returns the pointer to the array if dimensions is not set.
        If dimensions is set, it first creates a new DataSet with the subset
        and then it returns the pointer to the array'''
        if dimensions is not None:
            return self.subset(dimensions).as_array()
        return self.array
        
    def subset(self, dimensions=None):
        '''Creates a DataSet containing a subset of self according to the 
        labels in dimensions'''
        if dimensions is None:
            return self.array.copy()
        else:
            # check that all the requested dimensions are in the array
            # this is done by checking the dimension_labels
            proceed = True
            unknown_key = ''
            # axis_order contains the order of the axis that the user wants
            # in the output DataSet
            axis_order = []
            if type(dimensions) == list:
                for dl in dimensions:
                    if dl not in self.dimension_labels.values():
                        proceed = False
                        unknown_key = dl
                        break
                    else:
                        axis_order.append(find_key(self.dimension_labels, dl))
                if not proceed:
                    raise KeyError('Unknown key specified {0}'.format(dl))
                    
                # slice away the unwanted data from the array
                unwanted_dimensions = self.dimension_labels.copy()
                left_dimensions = []
                for ax in sorted(axis_order):
                    this_dimension = unwanted_dimensions.pop(ax)
                    left_dimensions.append(this_dimension)
                #print ("unwanted_dimensions {0}".format(unwanted_dimensions))
                #print ("left_dimensions {0}".format(left_dimensions))
                #new_shape = [self.shape[ax] for ax in axis_order]
                #print ("new_shape {0}".format(new_shape))
                command = "self.array"
                for i in range(self.number_of_dimensions):
                    if self.dimension_labels[i] in unwanted_dimensions.values():
                        command = command + "[0]"
                    else:
                        command = command + "[:]"
                #print ("command {0}".format(command))
                cleaned = eval(command)
                # cleaned has collapsed dimensions in the same order of
                # self.array, but we want it in the order stated in the 
                # "dimensions". 
                # create axes order for numpy.transpose
                axes = []
                for key in dimensions:
                    #print ("key {0}".format( key))
                    for i in range(len( left_dimensions )):
                        ld = left_dimensions[i]
                        #print ("ld {0}".format( ld))
                        if ld == key:
                            axes.append(i)
                #print ("axes {0}".format(axes))
                
                cleaned = numpy.transpose(cleaned, axes).copy()
                
                return DataSet(cleaned , True, dimensions)
    
    def fill(self, array):
        '''fills the internal numpy array with the one provided'''
        if numpy.shape(array) != numpy.shape(self.array):
            raise ValueError('Cannot fill with the provided array.' + \
                             'Expecting {0} got {1}'.format(
                                     numpy.shape(self.array),
                                     numpy.shape(array)))
        self.array = array[:]
        
                    

                
                    
                
class VolumeData(DataSet):
    '''DataSet for holding 2D or 3D dataset'''
    def __init__(self, 
                 array, 
                 deep_copy=True, 
                 dimension_labels=None, 
                 **kwargs):
        
        if type(array) == DataSet:
            # if the array is a DataSet get the info from there
            if not ( array.number_of_dimensions == 2 or \
                     array.number_of_dimensions == 3 ):
                raise ValueError('Number of dimensions are not 2 or 3: {0}'\
                                 .format(array.number_of_dimensions))
            
            DataSet.__init__(self, array.as_array(), deep_copy,
                             array.dimension_labels, **kwargs)
        elif type(array) == numpy.ndarray:
            if not ( array.ndim == 3 or array.ndim == 2 ):
                raise ValueError(
                        'Number of dimensions are not 3 or 2 : {0}'\
                        .format(array.ndim))
                
            if dimension_labels is None:
                if array.ndim == 3:
                    dimension_labels = ['horizontal_x' , 
                                        'horizontal_y' , 
                                        'vertical']
                else:
                    dimension_labels = ['horizontal' , 
                                        'vertical']   
            
            DataSet.__init__(self, array, deep_copy, dimension_labels, **kwargs)
        
       
        # load metadata from kwargs if present
        for key, value in kwargs.items():
            if (type(value) == list or type(value) == tuple) and \
                ( len (value) == 3 and len (value) == 2) :
                    if key == 'origin' :    
                        self.origin = value
                    if key == 'spacing' :
                        self.spacing = value
                        

class SinogramData(DataSet):
    '''DataSet for holding 2D or 3D sinogram'''
    def __init__(self, 
                 array, 
                 deep_copy=True, 
                 dimension_labels=None, 
                 **kwargs):
        
        if type(array) == DataSet:
            # if the array is a DataSet get the info from there
            if not ( array.number_of_dimensions == 2 or \
                     array.number_of_dimensions == 3 ):
                raise ValueError('Number of dimensions are not 2 or 3: {0}'\
                                 .format(array.number_of_dimensions))
            
            DataSet.__init__(self, array.as_array(), deep_copy,
                             array.dimension_labels, **kwargs)
        elif type(array) == numpy.ndarray:
            if not ( array.ndim == 3 or array.ndim == 2 ):
                raise ValueError('Number of dimensions are != 3: {0}'\
                                 .format(array.ndim))
            if dimension_labels is None:
                if array.ndim == 3:
                    dimension_labels = ['angle' , 
                                        'horizontal' , 
                                        'vertical']
                else:
                    dimension_labels = ['angle' , 
                                        'horizontal']
            DataSet.__init__(self, array, deep_copy, dimension_labels, **kwargs)
        
        # finally copy the instrument geometry
        if 'instrument_geometry' in kwargs.keys():
            self.instrument_geometry = kwargs['instrument_geometry']
        else:
            # assume it is parallel beam
            pass
            
        
class InstrumentGeometry(CCPiBaseClass):
    def __init__(self, **kwargs):
        CCPiBaseClass.__init__(self, **kwargs)
        
    def convertToAstra():
        pass
        
        
        
class DataSetProcessor1(CCPiBaseClass):
    '''Abstract class for a DataSetProcessor
    
    inputs: dictionary of inputs
    outputs: dictionary of outputs
    '''
    
    def __init__(self, **inputs):
        if 'hold_input' in inputs.keys():
            hold_input = inputs.pop('hold_input')
        else:
            hold_input = True
        if 'hold_output' in inputs.keys():
            hold_output = inputs.pop('hold_output')
        else:
            hold_output = True
                
        self.number_of_inputs = len (inputs)
        #pars = ['hold_output', 'hold_input'] 
        wargs = {}
        wargs['hold_output'] = hold_output
        wargs['hold_input'] = hold_input
        wargs['output'] = None
        
        # add the hold_output and hold_input to the wargs
        for key, value in wargs.items():
            if not key in inputs.keys():
                inputs[key] = value
                
        self.runTime = None
        self.mTime = datetime.now()
        
        CCPiBaseClass.__init__(self, **inputs)
                
    def getOutput(self):
        shouldRun = False
        if self.runTime is None:
            shouldRun = True
        elif self.mTime > self.runTime:
            shouldRun = True
            
        if self.getParameter('hold_output'):
            if shouldRun:
                output = self.__execute__()
                self.setParameter(output=output)
            return self.getParameter( 'output' )
        else:
            return self.__execute__()
        
    def __execute__(self):
        print ("__execute__")
        self.runTime = datetime.now()
        return self.apply()
    
    def apply(self):
        raise NotImplementedError('The apply method is not implemented!')
        
        
    
class AX(DataSetProcessor1):
    '''Example DataSetProcessor
    The AXPY routines perform a vector multiplication operation defined as

    y := a*x
    where:

    a is a scalar

    x a DataSet.
    '''
    
    def __init__(self, scalar, input_dataset, **wargs):
        kwargs = {'scalar':scalar, 
                  'input_dataset':input_dataset, 
                  'output': None
                  }
        for key, value in wargs.items():
            kwargs[key] = value
        DataSetProcessor1.__init__(self, **kwargs)
        
        
        
    def apply(self):
        a, x = self.getParameter(['scalar' , 'input_dataset' ])
        y = DataSet( a * x.as_array() , True, 
                    dimension_labels=x.dimension_labels )
        #self.setParameter(output_dataset=y)
        return y
    
        
    
    
class PixelByPixelDataSetProcessor(DataSetProcessor1):
    '''Example DataSetProcessor
    
    This processor applies a python function to each pixel of the DataSet
    
    f is a python function

    x a DataSet.
    '''
    
    def __init__(self, pyfunc, input_dataset):
        kwargs = {'pyfunc':pyfunc, 
                  'input_dataset':input_dataset, 
                  'output_dataset': None}
        DataSetProcessor1.__init__(self, **kwargs)
        
        
        
    def apply(self):
        pyfunc, x = self.getParameter(['pyfunc' , 'input_dataset' ])
        
        eval_func = numpy.frompyfunc(pyfunc,1,1)

        
        y = DataSet( eval_func( x.as_array() ) , True, 
                    dimension_labels=x.dimension_labels )
        return y
    
class DataSetProcessor():
    '''Defines a generic DataSet processor
    
    accepts DataSet as inputs and 
    outputs DataSet
    additional attributes can be defined with __setattr__
    '''
    
    def __init__(self):
        pass
    
    def __setattr__(self, name, value):
        if name == 'input':
            self.setInput(value)
        elif name in self.__dict__.keys():
            self.__dict__[name] = value
        else:
            raise KeyError('Attribute {0} not found'.format(name))
        #pass
    
    def setInput(self, dataset):
        print('Setting input as {0}...'.format(dataset))
        if issubclass(type(dataset), DataSet):
            if self.checkInput(dataset):
                self.__dict__['input'] = dataset
        else:
            raise TypeError("Input type mismatch: got {0} expecting {1}"\
                            .format(type(dataset), DataSet))
    
    def checkInput(self, dataset):
        '''Checks parameters of the input DataSet
        
        Should raise an Error if the DataSet does not match expectation, e.g.
        if the expected input DataSet is 3D and the Processor expects 2D.
        '''
        raise NotImplementedError('Implement basic checks for input DataSet')
        
    def getOutput(self):
        if None in self.__dict__.values():
            raise ValueError('Not all parameters have been passed')
        return self.process()
    
    def setInputProcessor(self, processor):
        print('Setting input as {0}...'.format(processor))
        if issubclass(type(processor), DataSetProcessor):
            self.__dict__['input'] = processor
        else:
            raise TypeError("Input type mismatch: got {0} expecting {1}"\
                            .format(type(processor), DataSetProcessor))
        
    
    def process(self):
        raise NotImplementedError('process must be implemented')
        
        
        
if __name__ == '__main__':
    shape = (2,3,4,5)
    size = shape[0]
    for i in range(1, len(shape)):
        size = size * shape[i]
    #print("a refcount " , sys.getrefcount(a))
    a = numpy.asarray([i for i in range( size )])
    print("a refcount " , sys.getrefcount(a))
    a = numpy.reshape(a, shape)
    print("a refcount " , sys.getrefcount(a))
    ds = DataSet(a, False, ['X', 'Y','Z' ,'W'])
    print("a refcount " , sys.getrefcount(a))
    print ("ds label {0}".format(ds.dimension_labels))
    subset = ['W' ,'X']
    b = ds.subset( subset )
    print("a refcount " , sys.getrefcount(a))
    print ("b label {0} shape {1}".format(b.dimension_labels, 
           numpy.shape(b.as_array())))
    c = ds.subset(['Z','W','X'])
    print("a refcount " , sys.getrefcount(a))
    
    # Create a VolumeData sharing the array with c
    volume0 = VolumeData(c.as_array(), False, dimensions = c.dimension_labels)
    volume1 = VolumeData(c, False)
    
    print ("volume0 {0} volume1 {1}".format(id(volume0.array),
           id(volume1.array)))
    
    # Create a VolumeData copying the array from c
    volume2 = VolumeData(c.as_array(), dimensions = c.dimension_labels)
    volume3 = VolumeData(c)
    
    print ("volume2 {0} volume3 {1}".format(id(volume2.array),
           id(volume3.array)))
        
    # single number DataSet
    sn = DataSet(numpy.asarray([1]))
    
    ax = AX(scalar = 2 , input_dataset=c)
    #ax.apply()
    print ("ax  in {0} out {1}".format(c.as_array().flatten(),
           ax.getOutput().as_array().flatten()))
    axm = AX(hold_output=False, scalar = 0.5 , input_dataset=ax.getOutput())
    #axm.apply()
    print ("axm in {0} out {1}".format(c.as_array(), axm.getOutput().as_array()))
    
    # create a PixelByPixelDataSetProcessor
    
    #define a python function which will take only one input (the pixel value)
    pyfunc = lambda x: -x if x > 20 else x
    clip = PixelByPixelDataSetProcessor(pyfunc,c)    
    #clip.apply()
    
    print ("clip in {0} out {1}".format(c.as_array(), clip.getOutput().as_array()))
    
    dsp = DataSetProcessor()
    dsp.setInput(ds)
    dsp.input = a
    # pipeline
#    Pipeline
#    Pipeline.setProcessor(0, ax)
#    Pipeline.setProcessor(1, axm)
#    Pipeline.execute()     
        