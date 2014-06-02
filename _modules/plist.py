'''
Property List Module
====================

The Property List module reads and writes PropertyList files which are used
heavily throughout OSX. Several parts of this code have been taken/modified from Greg Neagle's
FoundationPlist class which is a part of the munki project.

Remember that changes may not be effected immediately, and that you should try to avoid modifying the plist
of any running process.

TODO:

- The write_key/read_key executions should support collections. Operations on selections via command line
are always a bit clunky, so need to put some thought into this.

:maintainer:    Mosen <mosen@github.com>
:maturity:      new
:depends:       objc
:platform:      darwin
'''

import logging

log = logging.getLogger(__name__)  # Start logging

HAS_LIBS = False
try:
    from Foundation import NSData, \
        NSPropertyListSerialization, \
        NSPropertyListMutableContainers, \
        NSPropertyListXMLFormat_v1_0, \
        NSNumber, \
        NSString

    HAS_LIBS = True
except ImportError:
    log.debug('Error importing dependencies for plist execution module.')

__virtualname__ = 'plist'


def __virtual__():
    '''
    Only load if the platform is correct and we can use PyObjC libs
    '''
    if __grains__.get('kernel') != 'Darwin':
        return False

    if not HAS_LIBS:
        return False

    return __virtualname__


class FoundationPlistException(Exception):
    pass


class NSPropertyListSerializationException(FoundationPlistException):
    pass


class NSPropertyListWriteException(FoundationPlistException):
    pass





def _readPlist(filepath):
    """
    Read a .plist file from filepath.  Return the unpacked root object
    (which is usually a dictionary).
    """
    plistData = NSData.dataWithContentsOfFile_(filepath)
    dataObject, plistFormat, error = \
        NSPropertyListSerialization.propertyListFromData_mutabilityOption_format_errorDescription_(
            plistData, NSPropertyListMutableContainers, None, None)
    if error:
        error = error.encode('ascii', 'ignore')
        errmsg = "%s in file %s" % (error, filepath)

        import traceback

        log.debug(errmsg)
        log.debug(traceback.format_exc())
        raise NSPropertyListSerializationException(errmsg)
    else:
        return dataObject


def _readPlistFromString(data):
    '''Read a plist data from a string. Return the root object.'''
    plistData = buffer(data)
    dataObject, plistFormat, error = \
        NSPropertyListSerialization.propertyListFromData_mutabilityOption_format_errorDescription_(
            plistData, NSPropertyListMutableContainers, None, None)
    if error:
        error = error.encode('ascii', 'ignore')

        import traceback

        log.debug('Error parsing plist from string')
        log.debug(error)
        raise NSPropertyListSerializationException(error)
    else:
        return dataObject


def _writePlist(dataObject, filepath):
    '''
    Write 'rootObject' as a plist to filepath.
    '''
    plistData, error = \
        NSPropertyListSerialization.dataFromPropertyList_format_errorDescription_(
            dataObject, NSPropertyListXMLFormat_v1_0, None)
    if error:
        error = error.encode('ascii', 'ignore')
        log.debug('Error writing plist')
        log.debug(error)
        raise NSPropertyListSerializationException(error)
    else:
        if plistData.writeToFile_atomically_(filepath, True):
            return
        else:
            errmsg = "Failed to write plist data to %s" % filepath

            import traceback

            log.debug(errmsg)
            log.debug(traceback.format_exc())
            raise NSPropertyListWriteException(errmsg)


def _writePlistToString(rootObject):
    '''Return 'rootObject' as a plist-formatted string.'''
    plistData, error = \
        NSPropertyListSerialization.dataFromPropertyList_format_errorDescription_(
            rootObject, NSPropertyListXMLFormat_v1_0, None)
    if error:
        error = error.encode('ascii', 'ignore')
        log.debug('Error encoding to plist')
        log.debug(error)
        raise NSPropertyListSerializationException(error)
    else:
        return str(plistData)


def _valueToNSObject(value, nstype):
    '''Convert a string with a type specifier to a native Objective-C NSObject (serializable).'''
    return {
        'string': lambda v: NSString.stringWithUTF8String_(v),
        'int': lambda v: NSNumber.numberWithInt_(v),
        'float': lambda v: NSNumber.numberWithFloat_(v),
        'bool': lambda v: True if v == 'true' else False
    }[nstype](value)


def _objectForKeyList(dict, keys):
    '''
    Get an object inside a nested NSDictionary structure, using a list of nested keys
    '''
    key = keys.pop(0)

    # User accidentally supplies zero length key
    if len(key) == 0:
        return dict

    if len(keys) > 0:
        return _objectForKeyList(dict.objectForKey_(key), keys)
    else:
        # TODO: special case for array index notation [x] if current object is NSArray
        # if dict.isKindOfClass_(NSArray.class_()):
        # return
        return dict.objectForKey_(key)


def _setObjectForKeyList(dict, keys, value):
    '''
    Set the value of an object inside a nested NSDictionary structure, using a list of keys
    '''
    key = keys.pop(0)

    # User accidentally supplies zero length key
    if len(key) == 0:
        return dict

    if len(keys) > 0:
        return _objectForKeyList(dict.objectForKey_(key), keys)
    else:
        # TODO: special case for array index notation [x] if current object is NSArray
        # if dict.isKindOfClass_(NSArray.class_()):
        # return
        dict.setObject_forKey_(value, key)


def _removeObjectForKeyList(dict, keys):
    '''
    Remove an object inside a nested NSDictionary structure, using a list of nested keys
    '''
    key = keys.pop(0)

    # User accidentally supplies zero length key
    if len(key) == 0:
        return dict

    if len(keys) > 0:
        return _objectForKeyList(dict.objectForKey_(key), keys)
    else:
        # TODO: special case for array index notation [x] if current object is NSArray
        # if dict.isKindOfClass_(NSArray.class_()):
        # return
        return dict.removeObjectForKey_(key)


def read_key(path, key=''):
    '''
    Read the value of a key contained within the Property List file specified

    path
        An absolute path to a property list (.plist) file, including the extension

    key
        The path specification for the key to modify. A list of keys separated by a colon. eg. 'path:to:name'

    CLI Example:

    .. code-block:: bash

        salt '*' plist.read <path> [key]
    '''
    dataObject = _readPlist(path)

    keys = key.split(':')
    if type(keys) is str:
        keys = list(keys)

    value = _objectForKeyList(dataObject, keys)
    return value


def write_key(path, key, nstype, value):
    '''
    Write the value of a key contained within the Property List file specified

    path
        An absolute path to a property list (.plist) file, including the extension

    key
        The path specification for the key to modify. A list of keys separated by a colon.

    nstype
        The value type to write, one of 'string', 'int', 'float', 'bool'

    value
        The property value. If not specified it will be set to an empty value.

    CLI Example:

    .. code-block:: bash

        salt '*' plist.write <path> <key> <nstype> [value]
    '''
    dataObject = _readPlist(path)

    keys = key.split(':')
    if type(keys) is str:
        keys = list(keys)

    _setObjectForKeyList(dataObject, keys, _valueToNSObject(value, nstype))
    _writePlist(dataObject, path)


def delete_key(path, key):
    '''
    Delete the key from the property list at the specified path

    path
        An absolute path to a property list (.plist) file, including the extension

    key
        The specification of the key to modify. A list of keys separated by a colon.

    .. code-block:: bash

        salt '*' plist.delete <path> [key]
    '''
    dataObject = _readPlist(path)

    keys = key.split(':')
    if type(keys) is str:
        keys = list(keys)

    _removeObjectForKeyList(dataObject, keys)
    _writePlist(dataObject, path)

def read(path):
    '''
    Read the entire contents of the property list at the specified path

    path
        An absolute path to a property list (.plist) file, including the extension

    .. code-block:: bash

        salt '*' plist.read <path>
    '''
    dataObject = _readPlist(path)
    return dataObject
