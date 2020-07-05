#!/usr/bin/env python3
import os
import json
import hashlib
import datetime
import zipfile
import subprocess
import tempfile
import shutil
import logging

import yaml
import click
import click_log
from slugify import slugify

__version__ = "0.1.0"

logger = logging.getLogger("jprm")
click_log.basic_config(logger)

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


def run_os_command(command, environment=None, shell=False, cwd=None):
    if shell:
        cmd = command
    else:
        cmd = command.split()

    logger.debug(cmd, environment, shell, cwd)
    try:
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

    return command_output.stdout.decode('utf8'), command_output.stderr.decode('utf8'), command_output.returncode


# def cmd(args, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, encoding=None):
#     p = subprocess.Popen(args, stdout=stdout, stderr=stderr)
#     if p.stdout is not None:
#         if encoding is not None:
#             p.stdout.read().decode(encoding)
#         return p.stdout.read()
#     else:
#         p.wait()
#         return p.returncode


####################


def build_plugin(path, output=None, build_cfg=None, version=None, dotnet_config='Release', dotnet_framework='netstandard2.1'):
    if build_cfg is None:
        build_cfg = load_manifest(os.path.join(path, "build.yaml"))

        if build_cfg is None:
            return None

    if version is None:
        version = build_cfg['version']

    if output is None:
        output = './bin/'


    params = {
        'dotnet_config': dotnet_config,
        'dotnet_framework': dotnet_framework,
        'output': output,
        'version': version,
    }

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

    build_command = "dotnet publish --nologo" \
        " --configuration={dotnet_config} --framework={dotnet_framework}" \
        " --output={output} /p:Version={version}"

    stdout, stderr, retcode = run_os_command(build_command.format(**params), cwd=path)
    if retcode:
        logger.info(stdout)
        logger.error(stderr)
        exit(1)

    logger.info(stdout)


def package_plugin(path, build_cfg=None, version=None, binary_path=None, output=None, bundle=False):
    if build_cfg is None:
        build_cfg = load_manifest(os.path.join(path, "build.yaml"))

        if build_cfg is None:
            return None

    if version is None:
        version = build_cfg['version']

    if binary_path is None:
        binary_path = './bin/'

    if output is None:
        output = './artifacts/'

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

            shutil.copy(artifact_path, artifact_temp_path)

        meta = generate_metadata(build_cfg, version=version)
        meta_tempfile = os.path.join(tempdir, 'meta.json')
        with open(meta_tempfile, 'w') as fh:
            json.dump(meta, fh, sort_keys=True, indent=4)

        try:
            zip_path(output_path, tempdir)
        except FileNotFoundError as e:
            logger.error(e)
            exit(1)

        md5 = checksum_file(output_path, checksum_type='md5')

        with open(output_path + '.md5sum', 'wb') as fh:
            fh.write(output_file.encode())
            fh.write(b' *')
            fh.write(md5.encode())
            fh.write(b'\n')

        shutil.move(meta_tempfile, output_path + '.meta.json')

    return output_path


def generate_metadata(build_cfg, version=None, build_date=None):

    if version is None:
        version = build_cfg['version']

    if build_date is None:
        build_date = datetime.datetime.utcnow().isoformat(timespec='seconds') + 'Z'

    slug = slugify(build_cfg['name'])

    meta = {
        "guid": build_cfg['guid'],
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
    return meta


def generate_plugin_manifest(filename, repo_url='', meta=None, md5=None):
    if meta is None:
        meta_filename = filename + '.meta.json'
        if os.path.exists(meta_filename):
            with open(meta_filename) as fh:
                meta = json.load(fh)
                logger.info("Read meta from `{}`".format(meta_filename))
                logger.debug(meta)

    if meta is None:
        with zipfile.ZipFile(filename, 'r') as zf:
            if 'meta.json' in zf.namelist():
                with zf.open('meta.json', 'r') as fh:
                    meta = json.load(fh)
                    logger.info("Read meta from `{}:meta.json`".format(filename))
                    logger.debug(meta)

    if meta is None:
        raise ValueError('Metadata not provided')

    # TODO: Read .md5sum file
    if md5 is None:
        md5 = checksum_file(filename)

    if not repo_url:
        logger.warning("repo url not provided.")

    manifest = {
        "guid": meta['guid'],
        "name": meta['name'],
        "description": meta['description'],
        "overview": meta['overview'],
        "owner": meta['owner'],
        "category": meta['category'],

        "versions": [{

            "version": meta['version'],
            "changelog": meta['changelog'],
            "targetAbi": meta['targetAbi'],
            "sourceUrl": "{url}/{slug}/{slug}_{version}.zip".format(
                url=repo_url.rstrip('/'),
                slug=slugify(meta['name']),
                version=meta['version'],
            ),
            "checksum": md5,
            "timestamp": meta['timestamp'],
        }]
    }

    return manifest


def update_plugin_manifest(old, new):
    new_versions = new.pop('versions')
    old_versions = old.pop('versions')

    new_version_numbers = [x['version'] for x in new_versions]

    old.update(new)

    old['versions'] = []

    while old_versions:
        ver = old_versions.pop(0)
        if ver['version'] not in new_version_numbers:
            old['versions'].append(ver)

    while new_versions:
        ver = new_versions.pop(0)
        old['versions'].append(ver)

    return old


####################


@click.group()
@click.version_option(version=__version__, prog_name='Jellyfin Plugin Repository Manager')
@click_log.simple_verbosity_option(logger)
def cli():
    pass


@cli.group('plugin')
def cli_plugin():
    pass


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
    default='netstandard2.1',
    help='Dotnet framework',
)
def cli_plugin_build(path, output, dotnet_configuration, dotnet_framework, version):
    with tempfile.TemporaryDirectory() as bintemp:
        build_plugin(path, output=bintemp, dotnet_config=dotnet_configuration, dotnet_framework=dotnet_framework, version=version)
        filename = package_plugin(path, version=version, binary_path=bintemp, output=output)
        click.echo(filename)


@cli.group('repo')
def cli_repo():
    pass


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
def cli_repo_add(repo_path, plugins, url):
    with open(repo_path, 'r') as fh:
        logger.debug('Reading repo manifest from {}'.format(repo_path))
        repo_manifest = json.load(fh)

    for plugin_file in plugins:
        logger.info("Processing {}".format(plugin_file))
        plugin_manifest = generate_plugin_manifest(plugin_file, repo_url=url)
        logger.debug(plugin_manifest)

        # TODO: Add support for separate repo file path
        repo_dir = os.path.dirname(repo_path)
        name = plugin_manifest['name']
        slug = slugify(name)
        version = plugin_manifest['versions'][0]['version']

        logger.info("Adding {plugin} version {version} to {repo}".format(
            plugin=name,
            version=version,
            repo=repo_path,
        ))

        plugin_dir = os.path.join(repo_dir, slug)
        plugin_target = os.path.join(plugin_dir, '{slug}_{version}.zip'.format(
            slug=slug,
            version=version
        ))

        if not os.path.exists(plugin_dir):
            os.makedirs(plugin_dir)
        shutil.copy(plugin_file, plugin_target)

        updated = False
        for p_manifest in repo_manifest:
            if p_manifest.get('name') == name:
                update_plugin_manifest(p_manifest, plugin_manifest)
                updated = True

        if not updated:
            repo_manifest.append(plugin_manifest)

    tmpfile = repo_path + '.tmp'
    with open(tmpfile, 'w') as fh:
        logging.debug('Writing repo manifest to {}'.format(tmpfile))
        json.dump(repo_manifest, fh, indent=4)
    logging.debug('Renaming {} to {}'.format(tmpfile, repo_path))
    os.rename(tmpfile, repo_path)


####################


if __name__ == "__main__":
    cli()
