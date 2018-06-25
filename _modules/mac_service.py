# -*- coding: utf-8 -*-
'''
The service module for macOS
.. versionadded:: 2016.3.0

This module has support for services in the following locations.

.. code-block:: bash
	/System/Library/LaunchDaemons/
	/System/Library/LaunchAgents/
	/Library/LaunchDaemons/
	/Library/LaunchAgents/
	/Users/foo/Library/LaunchAgents/

.. note::

	This is a custom bug fix module for mac_service. most changes in here
	have already been approved and merged into either the dev branch or
	a bug fix branch, I will update this/ delete when all changes have been in
	officially release.

'''
from __future__ import absolute_import, unicode_literals, print_function

# Import python libs
import os
import re
import pwd
import plistlib

# Import salt libs
import logging
import salt.utils.files
import salt.utils.path
import salt.utils.platform
import salt.utils.stringutils
import salt.utils.mac_utils
import salt.modules.cmdmod
import salt.utils.args
import salt.utils.decorators as decorators
import salt.utils.timed_subprocess
from salt.exceptions import CommandExecutionError
from salt.utils.versions import LooseVersion as _LooseVersion
from salt.modules.cmdmod import _cmd_quote as _cmd_quote

# Import 3rd party libs
from salt.ext import six
from salt.ext.six.moves import range, zip, map

#global logger
log = logging.getLogger(__name__)

# Define the module's virtual name
__virtualname__ = 'service'

__func_alias__ = {
	'list_': 'list',
}


def __virtual__():
	'''
	Only for macOS with launchctl
	'''
	if not salt.utils.platform.is_darwin():
		return (False, 'Failed to load the mac_service module:\n'
					   'Only available on macOS systems.')

	if not salt.utils.path.which('launchctl'):
		return (False, 'Failed to load the mac_service module:\n'
					   'Required binary not found: "launchctl"')

	if not salt.utils.path.which('plutil'):
		return (False, 'Failed to load the mac_service module:\n'
					   'Required binary not found: "plutil"')

	if _LooseVersion(__grains__['osrelease']) < _LooseVersion('10.11'):
		return (False, 'Failed to load the mac_service module:\n'
					   'Requires macOS 10.11 or newer')

	return __virtualname__


def _get_service(name):
	'''
	Get information about a service.  If the service is not found, raise an
	error

	:param str name: Service label, file name, or full path

	:return: The service information for the service, otherwise an Error
	:rtype: dict
	'''
	services = __salt__['service.available_services']()
	name = name.lower()

	if name in services:
		# Match on label
		return services[name]

	for service in six.itervalues(services):
		if service['file_path'].lower() == name:
			# Match on full path
			return service
		basename, ext = os.path.splitext(service['file_name'])
		if basename.lower() == name:
			# Match on basename
			return service

	# Could not find service
	raise CommandExecutionError('Service not found: {0}'.format(name))


def _always_running_service(name):
	'''
	Check if the service should always be running based on the KeepAlive Key
	in the service plist.

	:param str name: Service label, file name, or full path

	:return: True if the KeepAlive key is set to True, False if set to False or
		not set in the plist at all.

	:rtype: bool

	.. versionadded:: Fluorine
	'''

	# get all the info from the launchctl service
	service_info = show(name)

	# get the value for the KeepAlive key in service plist
	try:
		keep_alive = service_info['plist']['KeepAlive']
	except KeyError:
		return False

	# check if KeepAlive is True and not just set.
	if keep_alive is True:
		return True

	return False


def _get_domain_target(name, service_target=False):
	'''
	Returns the domain/service target and path for a service. This is used to
	determine whether or not a service should be loaded in a user space or
	system space.

	:param str name: Service label, file name, or full path

	:param bool service_target: Whether to return a full
	service target. This is needed for the enable and disable
	subcommands of /bin/launchctl. Defaults to False

	:return: Tuple of the domain/service target and the path to the service.

	:rtype: tuple

	.. versionadded:: Fluorine
	'''

	# Get service information
	service = _get_service(name)

	# get the path to the service
	path = service['file_path']

	# most of the time we'll be at the system level.
	domain_target = 'system'

	# check if a LaunchAgent as we should treat these differently.
	if 'LaunchAgents' in path:
		# Get the console user so we can service in the correct session
		uid = __salt__['service.console_user']()
		domain_target = 'gui/{}'.format(uid)

	# check to see if we need to make it a full service target.
	if service_target is True:
		domain_target = '{}/{}'.format(domain_target, service['plist']['Label'])

	return (domain_target, path)


def _launch_agent(name):
	'''
	Checks to see if the provided service is a LaunchAgent

	:param str name: Service label, file name, or full path

	:return: True if a LaunchAgent, False if not.

	:rtype: bool

	.. versionadded:: Fluorine
	'''

	# Get the path to the service.
	path = _get_service(name)['file_path']

	if 'LaunchAgents' not in path:
		log.debug('"{}" is NOT a LaunchAgent'.format(name))
		return False
	log.debug('"{}" IS a LaunchAgent'.format(name))
	return True


def _available_services():
	'''
	This is a helper function needed for testing. We are using the memoziation
	decorator on the `available_services` function, which causes the function
	to run once and then return the results of the first run on subsequent
	calls. This causes problems when trying to test the functionality of the
	`available_services` function.
	'''
	launchd_paths = [
		'/Library/LaunchAgents',
		'/Library/LaunchDaemons',
		'/System/Library/LaunchAgents',
		'/System/Library/LaunchDaemons',
	]

	try:
		for user in os.listdir('/Users/'):
			agent_path = '/Users/{}/Library/LaunchAgents/'.format(user)
			if os.path.isdir(agent_path):
				launchd_paths.append(agent_path)
	except OSError:
		pass

	_available_services = dict()
	for launch_dir in launchd_paths:
		for root, dirs, files in salt.utils.path.os_walk(launch_dir):
			for file_name in files:

				# Must be a plist file
				if not file_name.endswith('.plist'):
					continue

				# Follow symbolic links of files in _launchd_paths
				file_path = os.path.join(root, file_name)
				true_path = os.path.realpath(file_path)

				# ignore broken symlinks
				if not os.path.exists(true_path):
					continue

				try:
					# This assumes most of the plist files
					# will be already in XML format
					plist = plistlib.readPlist(true_path)

				except Exception:
					# If plistlib is unable to read the file we'll need to use
					# the system provided plutil program to do the conversion
					cmd = '/usr/bin/plutil -convert xml1 -o - -- "{0}"'.format(
						true_path)
					plist_xml = salt.modules.cmdmod.run(cmd, output_loglevel='quiet')
					if six.PY2:
						plist = plistlib.readPlistFromString(plist_xml)
					else:
						plist = plistlib.loads(
							salt.utils.stringutils.to_bytes(plist_xml))

				try:
					_available_services[plist.Label.lower()] = {
						'file_name': file_name,
						'file_path': true_path,
						'plist': plist}
				except AttributeError:
					# Handle malformed plist files
					_available_services[os.path.basename(file_name).lower()] = {
						'file_name': file_name,
						'file_path': true_path,
						'plist': plist}

	return _available_services


@decorators.memoize
def available_services():
	'''
	Return a dictionary of all available services on the system

	Returns:
		dict: All available services

	CLI Example:

	.. code-block:: bash

		import salt.utils.mac_service
		salt.utils.mac_service.available_services()
	'''
	return _available_services()


def console_user(username=False):
	'''
	Gets the UID or Username of the current console user.

	:return: The uid or username of the console user.

	:param bool username: Whether to return the username of the console
	user instead of the UID. Defaults to False

	:rtype: Interger of the UID, or a string of the username.

	Raises:
		CommandExecutionError: If we fail to get the UID.

	CLI Example:

	.. code-block:: bash

		import salt.utils.mac_service
		salt.utils.mac_service.console_user()
	'''
	try:
		# returns the 'st_uid' stat from the /dev/console file.
		uid = os.stat('/dev/console')[4]
	except (OSError, IndexError):
		# we should never get here but raise an error if so
		raise CommandExecutionError('Failed to get a UID for the console user.')

	if username:
		return pwd.getpwuid(uid)[0]

	return uid


def show(name):
	'''
	Show properties of a launchctl service

	:param str name: Service label, file name, or full path

	:return: The service information if the service is found
	:rtype: dict

	CLI Example:

	.. code-block:: bash

		salt '*' service.show org.cups.cupsd  # service label
		salt '*' service.show org.cups.cupsd.plist  # file name
		salt '*' service.show /System/Library/LaunchDaemons/org.cups.cupsd.plist  # full path
	'''
	return _get_service(name)


def launchctl(sub_cmd, *args, **kwargs):
	'''
	Run a launchctl command and raise an error if it fails

	Args: additional args are passed to launchctl
		sub_cmd (str): Sub command supplied to launchctl

	Kwargs: passed to ``cmd.run_all``
		return_stdout (bool): A keyword argument. If true return the stdout of
			the launchctl command

	Returns:
		bool: ``True`` if successful
		str: The stdout of the launchctl command if requested

	Raises:
		CommandExecutionError: If command fails

	CLI Example:

	.. code-block:: bash

		import salt.utils.mac_service
		salt.utils.mac_service.launchctl('debug', 'org.cups.cupsd')
	'''
	# Get return type
	log.debug('Our current kwargs are {}'.format(kwargs))
	return_stdout = kwargs.pop('return_stdout', False)

	# Construct command
	cmd = ['launchctl', sub_cmd]
	cmd.extend(args)

	if 'runas' in kwargs and kwargs.get('runas'):
		# we need to insert the user simulation into the command itself and not
		# just run it from the environment on macOS as that
		# method doesn't work properly when run as root for certain commands.
		runas = kwargs.get('runas')
		if isinstance(cmd, (list, tuple)):
			cmd = ' '.join(map(_cmd_quote, cmd))

		cmd = 'su -l {0} -c "{1}"'.format(runas, cmd)
		# set runas to None, because if you try to run `su -l` as well as
		# simulate the environment macOS will prompt for the password of the
		# user and will cause salt to hang.
		kwargs['runas'] = None

	# Run command
	kwargs['python_shell'] = False
	ret = __salt__['cmd.run_all'](cmd, **kwargs)

	# Raise an error or return successful result
	if ret['retcode']:
		out = 'Failed to {0} service:\n'.format(sub_cmd)
		out += 'stdout: {0}\n'.format(ret['stdout'])
		out += 'stderr: {0}\n'.format(ret['stderr'])
		out += 'retcode: {0}'.format(ret['retcode'])
		raise CommandExecutionError(out)
	else:
		return ret['stdout'] if return_stdout else True


def list_(name=None, runas=None):
	'''
	Run launchctl list and return the output

	:param str name: The name of the service to list

	:param str runas: User to run launchctl commands

	:return: If a name is passed returns information about the named service,
		otherwise returns a list of all services and pids
	:rtype: str

	CLI Example:

	.. code-block:: bash

		salt '*' service.list
		salt '*' service.list org.cups.cupsd
	'''
	if name:
		# Get service information and label
		service = _get_service(name)
		label = service['plist']['Label']

		# we can assume if we are trying to list a LaunchAgent we need
		# to run as a user, if not provided, we'll use the console user.
		if not runas and _launch_agent(name):
			runas = __salt__['service.console_user'](username=True)

		# Collect information on service: will raise an error if it fails
		return launchctl('list',
						 label,
						 return_stdout=True,
						 output_loglevel='trace',
						 runas=runas)

	# Collect information on all services: will raise an error if it fails
	return launchctl('list',
					 return_stdout=True,
					 output_loglevel='trace',
					 runas=runas)


def enable(name, runas=None):
	'''
	Enable a launchd service. Raises an error if the service fails to be enabled

	:param str name: Service label, file name, or full path

	:param str runas: User to run launchctl commands

	:return: ``True`` if successful or if the service is already enabled
	:rtype: bool

	CLI Example:

	.. code-block:: bash

		salt '*' service.enable org.cups.cupsd
	'''
	# Get the domain target. enable requires a full <service-target>
	service_target = _get_domain_target(name, service_target=True)[0]

	# Enable the service: will raise an error if it fails
	return launchctl('enable', service_target, runas=runas)


def disable(name, runas=None):
	'''
	Disable a launchd service. Raises an error if the service fails to be
	disabled

	:param str name: Service label, file name, or full path

	:param str runas: User to run launchctl commands

	:return: ``True`` if successful or if the service is already disabled
	:rtype: bool

	CLI Example:

	.. code-block:: bash

		salt '*' service.disable org.cups.cupsd
	'''
	# Get the service target. enable requires a full <service-target>
	service_target = _get_domain_target(name, service_target=True)[0]

	# disable the service: will raise an error if it fails
	return launchctl('disable', service_target, runas=runas)


def start(name, runas=None):
	'''
	Start a launchd service.  Raises an error if the service fails to start

	.. note::
		To start a service in macOS the service must be enabled first. Use
		``service.enable`` to enable the service.

	:param str name: Service label, file name, or full path

	:param str runas: User to run launchctl commands

	:return: ``True`` if successful or if the service is already running
	:rtype: bool

	CLI Example:

	.. code-block:: bash

		salt '*' service.start org.cups.cupsd
	'''
	# Get the domain target.
	domain_target, path = _get_domain_target(name)

	# Load (bootstrap) the service: will raise an error if it fails
	return launchctl('bootstrap', domain_target, path, runas=runas)


def stop(name, runas=None):
	'''
	Stop a launchd service.  Raises an error if the service fails to stop

	.. note::
		Though ``service.stop`` will unload a service in macOS, the service
		will start on next boot unless it is disabled. Use ``service.disable``
		to disable the service

	:param str name: Service label, file name, or full path

	:param str runas: User to run launchctl commands

	:return: ``True`` if successful or if the service is already stopped
	:rtype: bool

	CLI Example:

	.. code-block:: bash

		salt '*' service.stop org.cups.cupsd
	'''
	# Get the domain target.
	domain_target, path = _get_domain_target(name)

	# Stop (bootout) the service: will raise an error if it fails
	return launchctl('bootout', domain_target, path, runas=runas)


def restart(name, runas=None):
	'''
	Unloads and reloads a launchd service.  Raises an error if the service
	fails to reload

	:param str name: Service label, file name, or full path

	:param str runas: User to run launchctl commands

	:return: ``True`` if successful
	:rtype: bool

	CLI Example:

	.. code-block:: bash

		salt '*' service.restart org.cups.cupsd
	'''
	# Restart the service: will raise an error if it fails
	if enabled(name):
		stop(name, runas=runas)
	start(name, runas=runas)

	return True


def status(name, sig=None, runas=None):
	'''
	Return the status for a service.

	:param str name: Used to find the service from launchctl.  Can be any part
		of the service name or a regex expression.

	:param str sig: Find the service with status.pid instead.  Note that
		``name`` must still be provided.

	:param str runas: User to run launchctl commands

	:return: The PID for the service if it is running, or 'loaded' if the
		service should not always have a PID, or otherwise an empty string

	:rtype: str

	CLI Example:

	.. code-block:: bash

		salt '*' service.status cups
	'''
	# Find service with ps
	if sig:
		return __salt__['status.pid'](sig)

	# mac services are a little different than other platforms as they may be
	# set to run on intervals and may not always active with a PID. This will
	# return a string 'loaded' if it shouldn't always be running and is enabled.
	log.debug('Checking to see if "{}" is enabled and supposed to be running.')
	if not _always_running_service(name) and enabled(name):
		return 'loaded'

	log.debug('"{}"service is an always running service.'.format(name))
	if not runas and _launch_agent(name):
		log.debug('need to set runas user. setting to console_user')
		runas = __salt__['service.console_user'](username=True)

	output = list_(runas=runas)

	# Used a string here instead of a list because that's what the linux version
	# of this module does
	pids = ''
	for line in output.splitlines():
		if 'PID' in line:
			continue
		if re.search(name, line.split()[-1]):
			if line.split()[0].isdigit():
				if pids:
					pids += '\n'
				pids += line.split()[0]

	return pids


def available(name):
	'''
	Check that the given service is available.

	:param str name: The name of the service

	:return: True if the service is available, otherwise False
	:rtype: bool

	CLI Example:

	.. code-block:: bash

		salt '*' service.available com.openssh.sshd
	'''
	try:
		_get_service(name)
		return True
	except CommandExecutionError:
		return False


def missing(name):
	'''
	The inverse of service.available
	Check that the given service is not available.

	:param str name: The name of the service

	:return: True if the service is not available, otherwise False
	:rtype: bool

	CLI Example:

	.. code-block:: bash

		salt '*' service.missing com.openssh.sshd
	'''
	return not available(name)


def enabled(name, runas=None):
	'''
	Check if the specified service is enabled

	:param str name: The name of the service to look up

	:param str runas: User to run launchctl commands

	:return: True if the specified service enabled, otherwise False
	:rtype: bool

	CLI Example:

	.. code-block:: bash

		salt '*' service.enabled org.cups.cupsd
	'''
	# Try to list the service.  If it can't be listed, it's not enabled
	try:
		list_(name=name, runas=runas)
		return True
	except CommandExecutionError:
		return False


def disabled(name, runas=None):
	'''
	Check if the specified service is not enabled. This is the opposite of
	``service.enabled``

	:param str name: The name to look up

	:param str runas: User to run launchctl commands

	:return: True if the specified service is NOT enabled, otherwise False
	:rtype: bool

	CLI Example:

	.. code-block:: bash

		salt '*' service.disabled org.cups.cupsd
	'''
	# A service is disabled if it is not enabled
	return not enabled(name, runas=runas)


def get_all(runas=None):
	'''
	Return a list of services that are enabled or available. Can be used to
	find the name of a service.

	:param str runas: User to run launchctl commands

	:return: A list of all the services available or enabled
	:rtype: list

	CLI Example:

	.. code-block:: bash

		salt '*' service.get_all
	'''
	# Get list of enabled services
	enabled = get_enabled(runas=runas)

	# Get list of all services
	available = list(__salt__['service.available_services']().keys())

	# Return composite list
	return sorted(set(enabled + available))


def get_enabled(runas=None):
	'''
	Return a list of all services that are enabled. Can be used to find the
	name of a service.

	:param str runas: User to run launchctl commands

	:return: A list of all the services enabled on the system
	:rtype: list

	CLI Example:

	.. code-block:: bash

		salt '*' service.get_enabled
	'''
	# Collect list of enabled services
	stdout = list_(runas=runas)
	service_lines = [line for line in stdout.splitlines()]

	# Construct list of enabled services
	enabled = []
	for line in service_lines:
		# Skip header line
		if line.startswith('PID'):
			continue

		pid, status, label = line.split('\t')
		enabled.append(label)

	return sorted(set(enabled))
