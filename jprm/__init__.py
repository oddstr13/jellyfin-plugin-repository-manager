#!/usr/bin/env python3
#
# Copyright (c) 2020 - Odd Strabo <oddstr13@openshell.no>
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#

import os
import json
import hashlib
import datetime
from typing import Optional, Union
import zipfile
import subprocess
import tempfile
import shutil
import logging
from functools import total_ordering
import re
import uuid

import yaml
import click
import click_log
from slugify import slugify
import tabulate

logger = logging.getLogger("jprm")
click_log.basic_config(logger)

__version__ = "1.1.2"
JSON_METADATA_FILE = "meta.json"
DEFAULT_IMAGE_FILE = "image.png"
DEFAULT_FRAMEWORK = "netstandard2.1"
CONFIG_LOCATIONS = [
    "jprm.yaml",
    ".jprm.yaml",
    ".ci/jprm.yaml",
    ".github/jprm.yaml",
    ".gitlab/jprm.yaml",
    "meta.yaml",
    "build.yaml",
]

####################


def checksum_file(path, checksum_type='md5'):
    cs = hashlib.new(checksum_type)

    with open(path, "rb") as fh:
        data = True
        while data:
            data = fh.read(1_048_576)
            if data:
                cs.update(data)

    return cs.hexdigest()


def zip_path(fn, path, prefix=''):

    with zipfile.ZipFile(fn, "w", zipfile.ZIP_DEFLATED) as z:
        for root, dirs, files in os.walk(path, topdown=True):
            for d in dirs:
                fp = os.path.join(root, d)
                ap = os.path.join(prefix, os.path.relpath(fp, path))

                if not ap:
                    continue

                z.write(fp, ap)

            for f in files:
                fp = os.path.join(root, f)
                ap = os.path.join(prefix, os.path.relpath(fp, path))

                z.write(fp, ap)


def load_manifest(manifest_file_name):
    """
    Read in an arbitrary YAML manifest and return it
    """
    with open(manifest_file_name, 'r') as manifest_file:
        try:
            cfg = yaml.load(manifest_file, Loader=yaml.SafeLoader)
        except yaml.YAMLError as e:
            logger.error("Failed to load YAML manifest {}: {}".format(manifest_file_name, e))
            return None
    return cfg


def get_config(path):
    for config_file in CONFIG_LOCATIONS:
        config_path = os.path.join(path, config_file)
        if os.path.exists(config_path):
            build_cfg = load_manifest(config_path)
            if build_cfg is not None:
                return build_cfg
    logger.warning("Failed to locate config file.")
    return None


def run_os_command(command, environment=None, shell=False, cwd=None):
    if shell:
        cmd = command
    else:
        cmd = command.split()

    logger.debug(['run_os_command', cmd, environment, shell, cwd])
    try:
        command_output = None
        command_output = subprocess.run(
            cmd,
            env=environment,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=shell,
            cwd=cwd,
        )
    except Exception as e:
        logger.exception(command_output, exc_info=e)
        raise

    return command_output.stdout.decode('utf8'), command_output.stderr.decode('utf8'), command_output.returncode


####################


@total_ordering
class Version(object):
    version_re = re.compile(r'^(?P<major>[0-9]+)(\.(?P<minor>[0-9]+)(\.(?P<build>[0-9]+)(\.(?P<revision>[0-9]+))?)?)?$')

    major = None
    minor = None
    build = None
    revision = None

    def __init__(self, version):
        if isinstance(version, Version):
            self.major = version.major
            self.minor = version.minor
            self.build = version.build
            self.revision = version.revision

        elif isinstance(version, str):
            match = self.version_re.match(version)
            if not match:
                raise ValueError(version)

            gd = match.groupdict()
            self.major = int(gd.get('major')) if gd.get('major') else None
            self.minor = int(gd.get('minor')) if gd.get('minor') else None
            self.build = int(gd.get('build')) if gd.get('build') else None
            self.revision = int(gd.get('revision')) if gd.get('revision') else None

        elif isinstance(version, int):
            self.major = version

        else:
            raise TypeError(version)

    def full(self):
        return '{major}.{minor}.{build}.{revision}'.format(
            major = self.major or 0,
            minor = self.minor or 0,
            build = self.build or 0,
            revision = self.revision or 0,
        )

    def __str__(self):
        if self.revision is not None:
            return '{major}.{minor}.{build}.{revision}'.format(**self)
        if self.build is not None:
            return '{major}.{minor}.{build}'.format(**self)
        if self.minor is not None:
            return '{major}.{minor}'.format(**self)
        else:
            return '{major}'.format(**self)

    def __repr__(self):
        return "<{}({})>".format(self.__class__.__name__, repr(str(self)))

    def __iter__(self):
        return iter(self.values())

    def __getitem__(self, key):
        if key in ('major', 0):
            return self.major

        if key in ('minor', 1):
            return self.minor

        if key in ('build', 2):
            return self.build

        if key in ('revision', 3):
            return self.revision

        raise KeyError

    def __setitem__(self, key, value):
        if key not in self:
            raise KeyError(key)

        if value is not None:
            value = int(value)

        if key in ('major', 0):
            self.major = value
            if value is None:
                self.minor = None
                self.build = None
                self.revision = None

        if key in ('minor', 1):
            self.minor = value
            if value is None:
                self.build = None
                self.revision = None

        if key in ('build', 2):
            self.build = value
            if value is None:
                self.revision = None

        if key in ('revision', 3):
            self.revision = value

    def __delitem__(self, key):
        self[key] = None

    def __len__(self):
        return 4

    def __contains__(self, key):
        return key in ('major', 'minor', 'build', 'revision', 0, 1, 2, 3)

    def keys(self):
        return ('major', 'minor', 'build', 'revision')

    def values(self):
        return (self.major, self.minor, self.build, self.revision)

    def items(self):
        return (
            ('major', self.major),
            ('minor', self.minor),
            ('build', self.build),
            ('revision', self.revision),
        )

    def get(self, key, default=None):
        if key not in self:
            logger.warning('Accessing non-existant key `{}` of `{!r}`'.format(key, self))
            return default

        return self[key]

    @staticmethod
    def _hasattrs(obj, *names):
        for name in names:
            if not hasattr(obj, name):
                return False
        return True

    def __eq__(self, other):
        if self._hasattrs(other, 'major', 'minor', 'build', 'revision'):
            return (
                self.major or 0,
                self.minor or 0,
                self.build or 0,
                self.revision or 0,
            ) == (
                other.major or 0,
                other.minor or 0,
                other.build or 0,
                other.revision or 0,
            )

        return NotImplemented

    def __lt__(self, other):
        if self._hasattrs(other, 'major', 'minor', 'build', 'revision'):
            return (
                self.major or 0,
                self.minor or 0,
                self.build or 0,
                self.revision or 0,
            ) < (
                other.major or 0,
                other.minor or 0,
                other.build or 0,
                other.revision or 0,
            )

        return NotImplemented

    def pop(self, k, d=KeyError):
        raise NotImplementedError


####################


def build_plugin(path, output=None, build_cfg=None, version=None, dotnet_config='Release', dotnet_framework=None, max_cpu_count=None):
    if build_cfg is None:
        build_cfg = get_config(path)

        if build_cfg is None:
            return None

    if version is None:
        version = build_cfg['version']

    if version is not None:
        version = Version(version).full()

    if output is None:
        output = './bin/'

    if max_cpu_count is None:
        max_cpu_count = 1

    if dotnet_framework is None:
        if 'framework' not in build_cfg:
            logger.warning("`framework` is not specified in build manifest, defaulting to `{}`.".format(DEFAULT_FRAMEWORK))
            logger.warning("The default target framework may change in the future.")
        dotnet_framework = build_cfg.get('framework', DEFAULT_FRAMEWORK)

    params = {
        'dotnet_config': dotnet_config,
        'dotnet_framework': dotnet_framework,
        'output': output,
        'max_cpu_count': max_cpu_count,
        'version': version,
    }

    logger.debug(params)

    projects = []

    sln_file = None
    for fn in os.listdir(path):
        if fn.endswith('.sln'):
            sln_file = os.path.join(path, fn)
            break

    if sln_file is not None:
        projects.extend(solution_get_projects(sln_file))
    else:
        for fn in os.listdir(path):
            if fn.endswith('.csproj'):
                projects.append(os.path.join(path, fn))
                break

    dbp_file = os.path.join(path, "Directory.Build.props")
    if os.path.exists(dbp_file):
        projects.append(dbp_file)

    for project in projects:
        set_project_version(project, version=version)
        set_project_framework(project, framework=dotnet_framework)

    clean_command = "dotnet clean --configuration={dotnet_config} --framework={dotnet_framework}"
    stdout, stderr, retcode = run_os_command(clean_command.format(**params), cwd=path)
    if retcode:
        logger.info(stdout)
        logger.error(stderr)
        exit(1)

    restore_command = "dotnet restore --no-cache"
    stdout, stderr, retcode = run_os_command(restore_command.format(**params), cwd=path)
    if retcode:
        logger.info(stdout)
        logger.error(stderr)
        exit(1)

    build_command = "dotnet publish --nologo --no-restore" \
        " --configuration={dotnet_config} --framework={dotnet_framework}" \
        " -p:PublishDir={output} -p:Version={version} -maxcpucount:{max_cpu_count}"

    stdout, stderr, retcode = run_os_command(build_command.format(**params), cwd=path)
    if retcode:
        logger.info(stdout)
        logger.error(stderr)
        exit(1)

    logger.info(stdout)


def package_plugin(path, build_cfg=None, version=None, binary_path=None, output=None, bundle=False):
    if build_cfg is None:
        build_cfg = get_config(path)

        if build_cfg is None:
            return None

    if version is None:
        version = build_cfg['version']

    if version is not None:
        version = Version(version).full()

    if binary_path is None:
        binary_path = './bin/'

    if output is None:
        output = './artifacts/'

    image_path = None
    if "image" in build_cfg:
        image_path = os.path.join(path, build_cfg['image'])
        if not os.path.exists(image_path):
            logger.error("Image `{}` not found at expected path `{}`.".format(build_cfg['image'], image_path))
            exit(1)

    if image_path is None:
        image_path = os.path.join(path, DEFAULT_IMAGE_FILE)
        if os.path.exists(image_path):
            logger.info("Image autodetected at path `{}`.".format(image_path))
        else:
            image_path = None

    slug = slugify(build_cfg['name'])

    output_file = "{slug}_{version}.zip".format(slug=slug, version=version)
    output_path = os.path.join(output, output_file)

    with tempfile.TemporaryDirectory() as tempdir:
        for artifact in build_cfg['artifacts']:
            artifact_path = os.path.join(binary_path, artifact)
            artifact_temp_path = os.path.join(tempdir, artifact)

            artifact_temp_dir = os.path.dirname(artifact_temp_path)
            if not os.path.exists(artifact_temp_dir):
                os.makedirs(artifact_temp_dir)

            shutil.copyfile(artifact_path, artifact_temp_path)

        if image_path is not None:
            image_name = os.path.basename(image_path)
            image_temp_path = os.path.join(tempdir, image_name)
            shutil.copyfile(image_path, image_temp_path)

            build_cfg['image'] = image_name

        meta = generate_metadata(build_cfg, version=version)
        meta_tempfile = os.path.join(tempdir, JSON_METADATA_FILE)
        with open(meta_tempfile, 'w') as fh:
            json.dump(meta, fh, sort_keys=True, indent=4)

        try:
            zip_path(output_path, tempdir)
        except FileNotFoundError as e:
            logger.error(e)
            exit(1)

        md5 = checksum_file(output_path, checksum_type='md5')

        with open(output_path + '.md5sum', 'wb') as fh:
            fh.write(md5.encode())
            fh.write(b' *')
            fh.write(output_file.encode())
            fh.write(b'\n')

        shutil.move(meta_tempfile, '{filename}.{meta}'.format(filename=output_path, meta=JSON_METADATA_FILE))

    return output_path


def generate_metadata(build_cfg, version=None, build_date=None):

    if version is None:
        version = build_cfg['version']

    if version is not None:
        version = Version(version).full()

    if build_date is None:
        build_date = datetime.datetime.utcnow().isoformat(timespec='seconds') + 'Z'

    meta = {
        "guid": str(uuid.UUID(build_cfg['guid'])),
        "name": build_cfg['name'],
        "description": build_cfg['description'],
        "overview": build_cfg['overview'],
        "owner": build_cfg['owner'],
        "category": build_cfg['category'],
        ########
        "version": version,
        "changelog": build_cfg['changelog'],
        "targetAbi": build_cfg['targetAbi'],
#        "sourceUrl": "{url}/{slug}/{slug}_{version}.zip".format(
#            url=repo_url.rstrip('/'),
#            slug=slug,
#            version=version,
#        ),
#        "checksum": bin_md5sum,
        "timestamp": build_date,
    }

    if "imageUrl" in build_cfg:
        meta['imageUrl'] = build_cfg['imageUrl']

    if "image" in build_cfg:
        meta['image'] = build_cfg['image']

    elif "imageUrl" not in build_cfg:
        logger.warning("Neither image nor imageUrl is specified.")

    if "image" in meta and "imageUrl" in meta:
        logger.warning("Both image and imageUrl is specified.")

    return meta


def generate_plugin_manifest(filename, repo_url='', plugin_url=None, meta=None, md5=None):
    if meta is None:
        meta_filename = '{filename}.{meta}'.format(filename=filename, meta=JSON_METADATA_FILE)
        if os.path.exists(meta_filename):
            with open(meta_filename) as fh:
                meta = json.load(fh)
                logger.info("Read meta from `{}`".format(meta_filename))
                logger.debug(meta)

    if meta is None:
        with zipfile.ZipFile(filename, 'r') as zf:
            if JSON_METADATA_FILE in zf.namelist():
                with zf.open(JSON_METADATA_FILE, 'r') as fh:
                    meta = json.load(fh)
                    logger.info("Read meta from `{}:{}`".format(filename, JSON_METADATA_FILE))
                    logger.debug(meta)

    if meta is None:
        raise ValueError('Metadata not provided')

    # TODO: Read .md5sum file
    if md5 is None:
        md5 = checksum_file(filename)

    if not repo_url and not plugin_url:
        logger.warning("repo and plugin url not provided, provide at least one.")

    slug = slugify(meta['name'])

    source_url = "{url}/{slug}/{slug}_{version}.zip".format(
        url=repo_url.rstrip('/'),
        slug=slug,
        version=meta['version'],
    )
    if plugin_url:
        logger.info("Plugin url `{}` overrides the autogenerated `{}`.".format(plugin_url, source_url))
        source_url = plugin_url

    manifest = {
        "guid": str(uuid.UUID(meta['guid'])),
        "name": meta['name'],
        "description": meta['description'],
        "overview": meta['overview'],
        "owner": meta['owner'],
        "category": meta['category'],

        "versions": [{
            "version": meta['version'],
            "changelog": meta['changelog'],
            "targetAbi": meta['targetAbi'],
            "sourceUrl": source_url,
            "checksum": md5,
            "timestamp": meta['timestamp'],
        }]
    }

    if "imageUrl" in meta:
        manifest['imageUrl'] = meta['imageUrl']

    if "image" in meta:
        manifest['image'] = meta['image']

        manifest['imageUrl'] = "{url}/{slug}/{image}".format(
            url=repo_url.rstrip('/'),
            slug=slug,
            image=meta['image'],
        )

        if "imageUrl" in meta:
            logger.warning("Image URL `{}` is getting overwritten by `{}` due to presence of `image`.".format(meta['imageUrl'], manifest['imageUrl']))

    elif "imageUrl" not in meta:
        logger.warning("Neither image nor imageUrl is specified.")

    return manifest


def update_plugin_manifest(old, new):
    new_versions = new.pop('versions')
    old_versions = old.pop('versions')

    new_version_numbers = [x['version'] for x in new_versions]

    old.update(new)

    old['versions'] = []

    while old_versions:
        ver = old_versions.pop(0)

        # Upgrade old incomplete version numbers - Jellyfin is not a fan of those.
        ver['version'] = Version(ver['version']).full()

        if ver['version'] not in new_version_numbers:
            old['versions'].append(ver)

    while new_versions:
        ver = new_versions.pop(0)
        old['versions'].append(ver)

    old['versions'].sort(key=lambda l: Version(l['version']), reverse=True)
    return old


def get_plugin_from_manifest(repo_manifest: dict, plugin: Union[str, uuid.UUID]) -> Optional[dict]:
    if plugin is None:
        return None

    if isinstance(plugin, uuid.UUID):
        plugin = str(plugin)
    else:
        try:
            plugin = str(uuid.UUID(plugin))
        except ValueError:
            pass

    items = [item for item in repo_manifest if plugin in [item.get('name'), item.get('guid'), slugify(item.get('name'))]]
    if items:
        return items[0]

    return None


_project_version_re = re.compile(r'\<Version\>(?P<version>.*?)\</Version\>')
_project_file_version_re = re.compile(r'\<FileVersion\>(?P<version>.*?)\</FileVersion\>')
_project_assembly_version_re = re.compile(r'\<AssemblyVersion\>(?P<version>.*?)\</AssemblyVersion\>')
_project_version_pattern = '<Version>{version}</Version>'
_project_file_version_pattern = '<FileVersion>{version}</FileVersion>'
_project_assembly_version_pattern = '<AssemblyVersion>{version}</AssemblyVersion>'


def set_project_version(project_file, version):
    version = Version(version)
    logger.info("Setting project version to {}".format(version.full()))

    with open(project_file, 'r') as fh:
        pdata = fh.read()

    ver_matches = list(_project_version_re.finditer(pdata))
    file_ver_matches = list(_project_file_version_re.finditer(pdata))
    ass_ver_matches = list(_project_assembly_version_re.finditer(pdata))
    if len(ver_matches) > 1 or len(file_ver_matches) > 1 or len(ass_ver_matches) > 1:
        logger.error('Found multiple instances of the version tag(s), bailing.')
        return None

    if ver_matches:
        old_version = ver_matches[0]['version']
        logger.debug('Old version: {}'.format(old_version))
    else:
        old_version = None

    if file_ver_matches:
        old_file_version = file_ver_matches[0]['version']
        logger.debug('Old file version: {}'.format(old_file_version))
    else:
        old_file_version = None

    if ass_ver_matches:
        old_assembly_version = ass_ver_matches[0]['version']
        logger.debug('Old assembly version: {}'.format(old_assembly_version))
    else:
        old_assembly_version = None

    pdata = _project_version_re.sub(_project_version_pattern.format(version=version.full()), pdata)
    pdata = _project_file_version_re.sub(_project_file_version_pattern.format(version=version.full()), pdata)
    pdata = _project_assembly_version_re.sub(_project_assembly_version_pattern.format(version=version.full()), pdata)

    with open(project_file, 'w') as fh:
        fh.write(pdata)

    return (old_version, old_file_version, old_assembly_version)


_project_framework_re = re.compile(r'\<TargetFramework\>(?P<framework>.*?)\</TargetFramework\>')
_project_framework_pattern = '<TargetFramework>{framework}</TargetFramework>'


def set_project_framework(project_file, framework):
    logger.info("Setting project framework to {}".format(framework))

    with open(project_file, 'r') as fh:
        pdata = fh.read()

    framework_matches = list(_project_framework_re.finditer(pdata))
    if len(framework_matches) > 1:
        logger.error('Found multiple instances of the TargetFramework tag, bailing.')
        return None

    if framework_matches:
        old_framework = framework_matches[0]['framework']
        logger.debug('Old framework: {}'.format(old_framework))
    else:
        old_framework = None

    pdata = _project_framework_re.sub(_project_framework_pattern.format(framework=framework), pdata)

    with open(project_file, 'w') as fh:
        fh.write(pdata)

    return old_framework


_solution_file_project_re = re.compile(r'\s*Project\("[^"]*"\)\s*=\s*"(?P<project_name>[^"]*)",\s*"(?P<project_file>[^"]+proj)",\s*"[^"]*"\s*')


def solution_get_projects(sln_file):
    with open(sln_file, 'r') as fh:
        data = fh.read()

    sln_dir = os.path.dirname(sln_file)
    matches = _solution_file_project_re.finditer(data)
    for match in matches:
        gd = match.groupdict()
        project_file = os.path.join(sln_dir, gd.get('project_file').replace('\\', os.path.sep))
        yield project_file


####################


class RepoPathParam(click.ParamType):
    name = 'repo_path'

    def __init__(self, should_exist=None):
        self.should_exist = should_exist

    def convert(self, value, param, ctx):
        if not value.endswith('.json'):
            value = os.path.join(value, 'manifest.json')

        if self.should_exist is not None:
            does_exist = os.path.exists(value)
            if self.should_exist and not does_exist:
                self.fail('Can not find repository at `{}`. Try initializing the repo first.'.format(value))
            elif does_exist and not self.should_exist:
                self.fail('There is already an existing repository at `{}`.'.format(value), param, ctx)

        dirname = os.path.dirname(value)
        if not os.path.exists(dirname):
            self.fail('The directory `{}` does not exist.'.format(dirname), param, ctx)

        return value


class ZipFileParam(click.ParamType):
    def validate(self, value, param, ctx):
        if not os.path.exists(value):
            self.fail('No such file: `{}`'.format(value))
            return False

        if not zipfile.is_zipfile(value):
            self.fail('`{}` is not a zip file.'.format(value))
            return False

        return True


####################


@click.group()
@click.version_option(version=__version__, prog_name='Jellyfin Plugin Repository Manager')
@click_log.simple_verbosity_option(logger)
def cli():
    pass  # Command grouping


@cli.group('plugin')
def cli_plugin():
    pass  # Command grouping


@cli_plugin.command('build')
@click.argument('path',
    nargs=1,
    required=False,
    default='.',
    type=click.Path(exists=True, file_okay=False, dir_okay=True, writable=True),
)
@click.option('--output', '-o',
    default=None,
    type=click.Path(exists=False, file_okay=False, dir_okay=True, writable=True),
    help='Path to dotnet build directory',
)
@click.option('--version', '-v',
    default=None,
    help='Plugin version',
)
@click.option('--dotnet-configuration',
    default='Release',
    help='Dotnet configuration',
)
@click.option('--dotnet-framework',
    default=None,
    help='Dotnet framework ({})'.format(DEFAULT_FRAMEWORK),
)
@click.option('--max-cpu-count',
    default=1,
    type=int,
    help='Max number of cores to use during build (1)',
)
def cli_plugin_build(path, output, dotnet_configuration, dotnet_framework, max_cpu_count, version):
    build_cfg = get_config(path)
    if build_cfg is None:
        raise click.UsageError('No build config found in `{}`'.format(path))

    with tempfile.TemporaryDirectory() as bintemp:
        build_plugin(path, output=bintemp, build_cfg=build_cfg, dotnet_config=dotnet_configuration, dotnet_framework=dotnet_framework,
                     version=version, max_cpu_count=max_cpu_count)
        filename = package_plugin(path, build_cfg=build_cfg, version=version, binary_path=bintemp, output=output)
        click.echo(filename)


@cli.group('repo')
def cli_repo():
    pass  # Command grouping


@cli_repo.command('init')
@click.argument('repo_path',
    nargs=1,
    required=True,
    type=RepoPathParam(should_exist=False),
)
def cli_repo_init(repo_path):
    if os.path.exists(repo_path):
        raise click.BadParameter("File already exists: `{}`".format(repo_path))

    with open(repo_path, 'w') as fh:
        json.dump([], fh)
        logger.info("Initialized `{}`.".format(repo_path))


@cli_repo.command('add')
@click.argument('repo_path',
    nargs=1,
    required=True,
    type=RepoPathParam(should_exist=True),
)
@click.argument('plugins',
    nargs=-1,
    required=True,
    type=ZipFileParam(),
)
@click.option('--url', '-u',
    default='',
    help='Repository public base URL',
)
@click.option('plugin_urls', '--plugin-url', '-U',
    default=[],
    help='Full URL of the plugin zip file',
    multiple=True,
)
def cli_repo_add(repo_path, plugins, url='', plugin_urls=[]):
    with open(repo_path, 'r') as fh:
        logger.debug('Reading repo manifest from {}'.format(repo_path))
        repo_manifest = json.load(fh)

    if plugin_urls and len(plugin_urls) != len(plugins):
        logger.error("When plugin url is specified, the number of times it's specified must match the number of plugins.")
        exit(1)

    for i, plugin_file in enumerate(plugins):
        logger.info("Processing {}".format(plugin_file))

        plugin_url = None
        if plugin_urls:
            plugin_url = plugin_urls[i]

        plugin_manifest = generate_plugin_manifest(plugin_file, repo_url=url, plugin_url=plugin_url)
        logger.debug(plugin_manifest)

        # TODO: Add support for separate repo file path
        repo_dir = os.path.dirname(repo_path)
        name = plugin_manifest['name']
        slug = slugify(name)
        version = plugin_manifest['versions'][0]['version']
        guid = uuid.UUID(plugin_manifest['guid'])

        logger.info("Adding {plugin} version {version} to {repo}".format(
            plugin=name,
            version=version,
            repo=repo_path,
        ))

        plugin_dir = os.path.join(repo_dir, slug)

        if plugin_url:
            logger.warning("Plugin url is specified, we are NOT copying the plugin file to the repo.")
        else:
            plugin_target = os.path.join(plugin_dir, '{slug}_{version}.zip'.format(
                slug=slug,
                version=version
            ))

            if not os.path.exists(plugin_dir):
                os.makedirs(plugin_dir)

            logger.info("Copying {plugin_file} to {plugin_target}".format(
                plugin_file=plugin_file,
                plugin_target=plugin_target,
            ))
            shutil.copyfile(plugin_file, plugin_target)

        if "image" in plugin_manifest:
            image_data = None
            with zipfile.ZipFile(plugin_file, 'r') as zf:
                if plugin_manifest["image"] in zf.namelist():
                    with zf.open(plugin_manifest["image"], 'r') as fh:
                        image_data = fh.read()
                        logger.info("Read image from `{}:{}`".format(plugin_file, plugin_manifest["image"]))

            if image_data is not None:
                image_target_path = os.path.join(plugin_dir, plugin_manifest["image"])

                write_image = True
                if os.path.exists(image_target_path):
                    existing_image_size = os.stat(image_target_path).st_size
                    if existing_image_size == len(image_data):
                        with open(image_target_path, "rb") as fh:
                            existing_image = fh.read()

                        if existing_image == image_data:
                            write_image = False
                            logger.info("Existing image same as new, skipping copy.")
                        del existing_image
                    else:
                        logger.info("Existing image differs in size ({}).".format(existing_image_size))

                if write_image:
                    logger.info("Writing image to `{}`.".format(image_target_path))
                    if not os.path.exists(plugin_dir):
                        os.makedirs(plugin_dir)
                    with open(image_target_path, "wb") as fh:
                        fh.write(image_data)
                del image_data

        updated = False
        for p_manifest in repo_manifest:
            if uuid.UUID(p_manifest.get('guid')) == guid:
                update_plugin_manifest(p_manifest, plugin_manifest)
                updated = True

        if not updated:
            repo_manifest.append(plugin_manifest)

    tmpfile = repo_path + '.tmp'
    with open(tmpfile, 'w') as fh:
        logging.debug('Writing repo manifest to {}'.format(tmpfile))
        json.dump(repo_manifest, fh, indent=4)
        fh.flush()
        os.fsync(fh.fileno())
    logging.debug('Renaming {} to {}'.format(tmpfile, repo_path))
    os.replace(tmpfile, repo_path)


@cli_repo.command('list')
@click.argument('repo_path',
    nargs=1,
    required=True,
    type=RepoPathParam(should_exist=True),
)
@click.argument('plugin',
    nargs=1,
    required=False,
    default=None,
)
def cli_repo_list(repo_path, plugin):
    with open(repo_path, 'r') as fh:
        logger.debug('Reading repo manifest from {}'.format(repo_path))
        repo_manifest = json.load(fh)

    if plugin is not None:
        try:
            plugin = str(uuid.UUID(plugin))
        except ValueError:
            pass

        items = [item for item in repo_manifest if plugin in [item.get('name'), item.get('guid'), slugify(item.get('name'))]]
        if items:
            item = items[0]
            for version in item.get('versions', []):
                click.echo(version.get('version'))
        else:
            raise click.UsageError('PLUGIN `{}` not found in `{}`'.format(plugin, repo_path))

    else:
        table = []
        for item in repo_manifest:
            name = item.get('name')
            guid = item.get('guid')
            versions = sorted(
                [release.get('version', '0.0') for release in item.get('versions', [])],
                key = lambda rel: Version(rel),
                reverse = True,
            )

            if versions:
                version = versions[0]
            else:
                version = ''

            table.append([name, version, slugify(name), guid])

        if table:
            click.echo(tabulate.tabulate(table, headers=('NAME', 'VERSION', 'SLUG', 'GUID'), tablefmt='plain', colalign=('left', 'right', 'left')))


@cli_repo.command('remove')
@click.argument('repo_path',
    nargs=1,
    required=True,
    type=RepoPathParam(should_exist=True),
)
@click.argument('plugin',
    nargs=1,
    required=True,
    default=None,
)
@click.argument('version',
    nargs=1,
    required=False,
    default=None,
    type=Version,
)
def cli_repo_remove(repo_path, plugin, version: Optional[Version]):
    with open(repo_path, 'r') as fh:
        logger.debug('Reading repo manifest from {}'.format(repo_path))
        repo_manifest = json.load(fh)

    plugin_manifest = get_plugin_from_manifest(repo_manifest, plugin)
    if plugin_manifest is None:
        raise click.UsageError('PLUGIN `{}` not found in `{}`'.format(plugin, repo_path))

    if version is None:
        logger.warning(f"Removing plugin {plugin_manifest.get('name')})")
        repo_manifest.remove(plugin_manifest)
        click.echo(f"removed {plugin_manifest.get('guid')}")
    else:
        version_str = version.full()
        for release in list(plugin_manifest.get('versions', [])):
            if release.get('version') == version_str:
                logger.warning(f"Removing version {version} of plugin {plugin_manifest.get('name')})")
                plugin_manifest['versions'].remove(release)
                click.echo(f"removed {plugin_manifest.get('guid')} {version_str}")

    tmpfile = repo_path + '.tmp'
    with open(tmpfile, 'w') as fh:
        logging.debug('Writing repo manifest to {}'.format(tmpfile))
        json.dump(repo_manifest, fh, indent=4)
        fh.flush()
        os.fsync(fh.fileno())
    logging.debug('Renaming {} to {}'.format(tmpfile, repo_path))
    os.replace(tmpfile, repo_path)


####################


if __name__ == "__main__":
    cli()
