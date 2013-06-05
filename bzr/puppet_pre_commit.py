#!/usr/bin/env python
#
# BZR pre-commit hook, which will run some basic syntax checking on manifests
# in the current branch.
#
# To use this script, place it in your ~/.bazzar/plugins directory (create
# this directory if it doesn't exist).
#

from bzrlib import branch
import os
import sys
import subprocess

def get_puppet_args():
    """Find the right args for checking puppet syntax"""
    try:
        process = subprocess.Popen(["puppet","-V"],
            stderr=subprocess.STDOUT, stdout=subprocess.PIPE)
        process.wait()
        if process.returncode != 0:
            print "\n\n Error: puppet error: %s" % (process.stdout.readlines())
        else:
            version = process.stdout.readline().rstrip()
            if version >= "2.7":
                return ["parser","validate"]
            else:
                return ["--parseonly"]
    except OSError, e:
        print "\n\n Error: failed to execute 'puppet': %s" % (e)
        sys.exit(1)

def get_branch_root(directory):
    """Find the root directory of the current BZR branch."""
    while os.path.exists(directory):
        if os.path.exists(os.path.join(directory, '.bzr')):
            return directory
        if directory == '/':
            break
        (parent, dir) = os.path.split(directory)
        directory = parent
    print "Commit FAILED:  Can't locate BZR Root."
    sys.exit(1)

def check_puppet_syntax(local, master, old_revno, old_revid, future_revno,
                       future_revid, tree_delta, future_tree):
    """This will run some basic syntax checking on the puppet manifests."""

    # Check syntax on changed files
    errors = []
    os.chdir(get_branch_root(os.getcwd()))
    print "\n" # make some space so we aren't clobbered by bzr's status msgs
    for file in tree_delta.added + tree_delta.renamed + tree_delta.modified:
        file = file[0]
        if file.endswith(".pp"):
            print "Checking syntax in: %s" % (file)
            try:
                process = subprocess.Popen(["puppet"] + get_puppet_args() + [file],
                    stderr=subprocess.STDOUT, stdout=subprocess.PIPE)
                process.wait()
                if process.returncode != 0:
                    errors.append((file, ''.join(process.stdout.readlines())))
            except OSError, e:
                print "\n\n Error: failed to execute 'puppet': %s" % (e)
                sys.exit(1)
    if errors:
        print "\nSyntax errors were found:\n"
        for error in errors:
            print "%s: %s" % (error[0], error[1]),
        print "\nCommit FAILED"
        sys.exit(1)
    else:
        print "\nAll syntax checks PASSED"


# This is where the magic happens
branch.Branch.hooks.install_named_hook('pre_commit', check_puppet_syntax,
                                       'Check puppet manifests for syntax errors.')
