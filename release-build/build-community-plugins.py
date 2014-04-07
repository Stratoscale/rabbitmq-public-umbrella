#!/usr/bin/env python

from optparse import OptionParser
import sys, subprocess, os, copy

# There is no real dependency management here, if there are
# dependencies between community plugins list them in order.
PLUGINS = [
    ('rfc4627_jsonrpc',                   {'url': 'https://github.com/rabbitmq/erlang-rfc4627-wrapper',
                                          'version-add-hash': False}),
    ('rabbitmq_jsonrpc',                  {'url': 'https://github.com/rabbitmq/rabbitmq-jsonrpc'}),
    ('rabbitmq_jsonrpc_channel',          {'url': 'https://github.com/rabbitmq/rabbitmq-jsonrpc-channel'}),
    ('rabbitmq_jsonrpc_channel_examples', {'url': 'https://github.com/rabbitmq/rabbitmq-jsonrpc-channel-examples'}),
    ('rabbitmq_auth_backend_http',        {'url': 'https://github.com/simonmacmullen/rabbitmq-auth-backend-http'}),
    ('rabbitmq_lvc',                      {'url': 'https://github.com/simonmacmullen/rabbitmq-lvc-plugin'})
]

OTP_VERSION="R13B03"
BUILD_DIR = "/var/tmp/plugins-build/"
CURRENT_DIR = ""
RABBITMQ_TAG = ""
HGREPOBASE="ssh://hg@rabbit-hg-private"

def main():
    parser = OptionParser()
    parser.add_option("-p", "--plugin",
                      dest="plugin",
                      help="build a single plugin")
    parser.add_option("-t", "--server-tag",
                      dest="server_tag",
                      help="build against specific server tag")
    parser.add_option("-T", "--plugin-tag",
                      dest="plugin_tag",
                      help="build against specific plugin tag")
    parser.add_option("-R", "--repo-base",
                      dest="repo_base",
                      help="clone from alternative hg repository base URL")
    (options, args) = parser.parse_args()
    if options.plugin is None:
        plugins = PLUGINS
    else:
        plugins = [(k, v) for (k, v) in PLUGINS if k == options.plugin]
        if len(plugins) == 0:
            print "Plugin {0} not found".format(options.plugin)
            sys.exit(1)
    if options.repo_base is not None:
        global HGREPOBASE
        HGREPOBASE = options.repo_base
    print "Using: {0}".format(BUILD_DIR)
    if os.path.exists(BUILD_DIR):
        print "Error: {0} exists. Not building.".format(BUILD_DIR)
        sys.exit(1)
    os.makedirs("{0}/plugins".format(BUILD_DIR))
    ensure_otp()
    checkout(options.server_tag)
    print "Building..."
    [build(p, options.plugin_tag) for p in plugins]

def ensure_dir(d):
    if not os.path.exists(d):
        os.makedirs(d)

def ensure_otp():
    cd(BUILD_DIR)
    erl_cmd = 'io:format("~s~n", [erlang:system_info(otp_release)]), halt().'
    erl_ver = do("erl", "-noshell", "-eval", erl_cmd).rstrip()
    if erl_ver != OTP_VERSION:
        print "Erlang {0} found, not {1}".format(erl_ver, OTP_VERSION)
        print "Suggestion: ./install-otp.sh {0}".format(OTP_VERSION)
        exit(1)

def otp_dir():
    return "{0}/otp-{1}".format(os.environ["HOME"], OTP_VERSION)

def checkout(opt_tag):
    global RABBITMQ_TAG
    print "Checking out umbrella..."
    cd(BUILD_DIR)
    do("hg", "clone", HGREPOBASE + "/rabbitmq-public-umbrella")
    cd(CURRENT_DIR + "/rabbitmq-public-umbrella")
    if opt_tag is None:
        RABBITMQ_TAG = get_tag(do("hg", "tags").split('\n'))
        do("make", "checkout")
    else:
        RABBITMQ_TAG = opt_tag
        do("hg", "up", "-r", RABBITMQ_TAG)
        do("make", "checkout")
        do("./foreachrepo", "hg", "up", "-r", RABBITMQ_TAG)

def get_tag(lines):
    for line in lines:
        if line.startswith('rabbitmq'):
            return line.split(' ')[0]
    return None

def server_version():
    return RABBITMQ_TAG[10:].replace('_', '.')

def build((plugin, details), tag):
    print " * {0}".format(plugin)
    cd(BUILD_DIR + "/rabbitmq-public-umbrella")
    url = details['url']
    if 'version-add-hash' in details:
        version_add_hash = details['version-add-hash']
    else:
        version_add_hash = True
    do("git", "clone", "-q", url)
    checkout_dir = url.split("/")[-1].split(".")[0]
    cd(CURRENT_DIR + "/" + checkout_dir)
    if tag is None:
        do("git", "checkout", "master")
    else:
        do("git", "checkout", tag)
    hash = do("git", "--git-dir=./.git", "rev-parse", "HEAD")[0:8]
    if version_add_hash:
        plugin_version = "{0}-{1}".format(server_version(), hash)
    else:
        plugin_version = server_version()
    do("make", "-j", "VERSION={0}".format(plugin_version), "srcdist")
    do("make", "-j", "VERSION={0}".format(plugin_version), "dist")
    dest_dir = os.path.join(BUILD_DIR, "plugins", server_version())
    ensure_dir(dest_dir)
    do("cp",
       find_package("{0}/srcdist/".format(CURRENT_DIR), plugin, ".tar.bz2"),
       dest_dir)
    do("cp", find_package("{0}/dist/".format(CURRENT_DIR), plugin, ".ez"),
       dest_dir)

def find_package(dir, prefix, suffix):
    for f in os.listdir(dir):
        if f.startswith(prefix) and f.endswith(suffix):
            return os.path.join(dir, f)
    raise ('no_package', dir, prefix, suffix)

def do(*args):
    path = os.environ['PATH']
    env = copy.deepcopy(os.environ)
    env['PATH'] = "{0}/bin:{1}".format(otp_dir(), path)
    return subprocess.check_output(args, cwd = CURRENT_DIR,env = env)

def cd(d):
    global CURRENT_DIR
    CURRENT_DIR = d

if __name__ == "__main__":
    main()
